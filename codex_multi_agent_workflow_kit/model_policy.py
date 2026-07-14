"""Central role-to-model policy and fail-closed capability resolver."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from typing import Any, Mapping, Sequence

from .contracts import HarnessErrorCode


MODEL_PATTERN = re.compile(r"^gpt-(\d+)\.(\d+)(?:\.(\d+))?-(sol|terra|luna)$")
TIER_ORDER = {"luna": 0, "terra": 1, "sol": 2}


class ModelSlugError(ValueError):
    """Raised when a model slug cannot be compared safely."""


class ResolutionStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ModelComparison:
    version: int
    tier: int


@dataclass(frozen=True, slots=True)
class Resolution:
    status: ResolutionStatus
    error_code: str | None
    role: str
    model: str | None
    thinking: str | None
    used_fallback: bool
    capabilities: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    ordered_fallbacks: tuple[str, ...]
    decision_reason: str
    missing_models: tuple[str, ...]
    missing_tools: tuple[str, ...]
    policy_version: str
    policy_hash: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "error_code": self.error_code,
            "role": self.role,
            "model": self.model,
            "thinking": self.thinking,
            "used_fallback": self.used_fallback,
            "capabilities": list(self.capabilities),
            "required_capabilities": list(self.required_capabilities),
            "ordered_fallbacks": list(self.ordered_fallbacks),
            "decision_reason": self.decision_reason,
            "missing_models": list(self.missing_models),
            "missing_tools": list(self.missing_tools),
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
        }


def _parse_model_slug(slug: str) -> tuple[tuple[int, int, int], str]:
    match = MODEL_PATTERN.fullmatch(slug)
    if match is None:
        raise ModelSlugError("Model slug is not a stable semantic version and tier.")
    major, minor, patch, tier = match.groups()
    return (int(major), int(minor), int(patch or 0)), tier


def _comparison(left: object, right: object) -> int:
    return (left > right) - (left < right)


def compare_model_slugs(left: str, right: str) -> ModelComparison:
    """Compare semantic version and tier independently, never as decimal text."""

    left_version, left_tier = _parse_model_slug(left)
    right_version, right_tier = _parse_model_slug(right)
    return ModelComparison(
        version=_comparison(left_version, right_version),
        tier=_comparison(TIER_ORDER[left_tier], TIER_ORDER[right_tier]),
    )


def load_default_policy() -> dict[str, Any]:
    policy_path = files(__package__).joinpath("model-policy.json")
    return json.loads(policy_path.read_text(encoding="utf-8"))


def policy_content_hash(policy: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        policy, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _unavailable(
    role: str,
    policy: Mapping[str, Any],
    *,
    missing_models: Sequence[str] = (),
    missing_tools: Sequence[str] = (),
    required_capabilities: Sequence[str] = (),
    ordered_fallbacks: Sequence[str] = (),
    decision_reason: str = "NO_COMPATIBLE_MODEL",
) -> Resolution:
    return Resolution(
        status=ResolutionStatus.UNAVAILABLE,
        error_code=HarnessErrorCode.UNAVAILABLE.value,
        role=role,
        model=None,
        thinking=None,
        used_fallback=False,
        capabilities=(),
        required_capabilities=tuple(sorted(set(required_capabilities))),
        ordered_fallbacks=tuple(ordered_fallbacks),
        decision_reason=decision_reason,
        missing_models=tuple(sorted(set(missing_models))),
        missing_tools=tuple(sorted(set(missing_tools))),
        policy_version=str(policy.get("policy_version", "UNKNOWN")),
        policy_hash=policy_content_hash(policy),
    )


def resolve_role(
    role: str,
    catalog: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    requested_capabilities: set[str] | None = None,
) -> Resolution:
    """Resolve a role deterministically or return structured UNAVAILABLE."""

    active_policy = policy or load_default_policy()
    roles = active_policy.get("roles", {})
    if role not in roles:
        return _unavailable(role, active_policy, decision_reason="UNKNOWN_ROLE")

    role_policy = dict(roles[role])
    requested = requested_capabilities or set()
    promotion = active_policy.get("promotions", {}).get(role)
    promoted = bool(
        promotion and requested.intersection(promotion.get("when_capabilities", []))
    )
    if promoted:
        role_policy = {
            key: value for key, value in promotion.items() if key != "when_capabilities"
        }

    catalog_models = catalog.get("models", {})
    catalog_tools = set(catalog.get("tools", ()))
    required_tools = set(role_policy.get("required_tools", ()))
    missing_tools = required_tools - catalog_tools
    required_capabilities = set(role_policy.get("required_capabilities", ()))
    ordered_fallbacks = tuple(role_policy.get("fallbacks", ()))
    if missing_tools:
        return _unavailable(
            role,
            active_policy,
            missing_tools=tuple(missing_tools),
            required_capabilities=tuple(required_capabilities),
            ordered_fallbacks=ordered_fallbacks,
            decision_reason="MISSING_REQUIRED_TOOL",
        )

    thinking = str(role_policy["thinking"])
    candidates = [role_policy["primary"], *role_policy.get("fallbacks", ())]
    missing_models: list[str] = []
    for index, model in enumerate(candidates):
        details = catalog_models.get(model)
        if not isinstance(details, Mapping):
            missing_models.append(model)
            continue
        supported_thinking = set(details.get("thinking", ()))
        supported_capabilities = set(details.get("capabilities", ()))
        if thinking not in supported_thinking or not required_capabilities.issubset(
            supported_capabilities
        ):
            missing_models.append(model)
            continue
        return Resolution(
            status=ResolutionStatus.AVAILABLE,
            error_code=None,
            role=role,
            model=model,
            thinking=thinking,
            used_fallback=index > 0,
            capabilities=tuple(sorted(supported_capabilities)),
            required_capabilities=tuple(sorted(required_capabilities)),
            ordered_fallbacks=ordered_fallbacks,
            decision_reason=(
                "HIGH_RISK_PROMOTION"
                if promoted
                else "ALLOWLISTED_FALLBACK"
                if index > 0
                else "PRIMARY_AVAILABLE"
            ),
            missing_models=tuple(sorted(set(missing_models))),
            missing_tools=(),
            policy_version=str(active_policy["policy_version"]),
            policy_hash=policy_content_hash(active_policy),
        )
    return _unavailable(
        role,
        active_policy,
        missing_models=missing_models,
        required_capabilities=tuple(required_capabilities),
        ordered_fallbacks=ordered_fallbacks,
        decision_reason="NO_COMPATIBLE_MODEL",
    )
