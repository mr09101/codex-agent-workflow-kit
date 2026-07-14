"""Validated, metadata-only operation envelopes for harness adapters."""

from __future__ import annotations

import os
import stat
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from .contracts import HarnessErrorCode


ERROR_CODE = HarnessErrorCode.INVALID_ENVELOPE.value
ENVELOPE_FIELDS = frozenset(
    {
        "operation_id",
        "idempotency_key",
        "parent_session_id",
        "delegation_owner",
        "delegation_depth",
        "cwd_realpath",
        "deadline_at",
    }
)
DELEGATION_OWNERS = frozenset(
    {"auto_ultra", "visible_thread", "internal_subagent", "claude_codex"}
)
MAX_DELEGATION_DEPTH = 8
MAX_DEADLINE_HORIZON = timedelta(hours=24)
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


class EnvelopeError(ValueError):
    """A fail-closed envelope validation error."""

    code = ERROR_CODE


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT
    )


def _nonempty_identifier(name: str, value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise EnvelopeError(f"{name} must be a non-empty bounded string.")
    if any(ord(character) < 32 for character in value):
        raise EnvelopeError(f"{name} contains control characters.")
    return value


def _canonical_directory(value: object, fixture_root: Path | None) -> str:
    if not isinstance(value, str) or not value:
        raise EnvelopeError("cwd_realpath must be a non-empty string.")
    candidate = Path(value)
    if not candidate.is_absolute() or os.path.normpath(value) != value:
        raise EnvelopeError("cwd_realpath must be an absolute canonical path.")
    if not candidate.is_dir() or _is_link(candidate):
        raise EnvelopeError("cwd_realpath must identify a real directory.")
    resolved = candidate.resolve(strict=True)
    if os.path.normcase(str(resolved)) != os.path.normcase(value):
        raise EnvelopeError("cwd_realpath must not use an alias or filesystem link.")

    if fixture_root is not None:
        fixture = Path(fixture_root).resolve(strict=True)
        if _is_link(fixture):
            raise EnvelopeError("fixture boundary must not be a filesystem link.")
        try:
            resolved.relative_to(fixture)
        except ValueError as error:
            raise EnvelopeError("cwd_realpath escapes the fixture boundary.") from error
    return str(resolved)


def _deadline(value: object, now: datetime | None) -> str:
    if not isinstance(value, str):
        raise EnvelopeError("deadline_at must be an ISO-8601 string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EnvelopeError("deadline_at is not valid ISO-8601.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EnvelopeError("deadline_at must include a timezone.")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise EnvelopeError("validation clock must include a timezone.")
    if parsed <= current:
        raise EnvelopeError("deadline_at must be in the future.")
    if parsed - current > MAX_DEADLINE_HORIZON:
        raise EnvelopeError("deadline_at exceeds the policy horizon.")
    return parsed.isoformat()


@dataclass(frozen=True, slots=True)
class OperationEnvelope:
    """The seven-field contract shared by all harness adapters."""

    operation_id: str
    idempotency_key: str
    parent_session_id: str | None
    delegation_owner: str
    delegation_depth: int
    cwd_realpath: str
    deadline_at: str

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, Any],
        *,
        now: datetime | None = None,
        fixture_root: Path | None = None,
    ) -> "OperationEnvelope":
        if set(values) != ENVELOPE_FIELDS:
            missing = sorted(ENVELOPE_FIELDS - set(values))
            extra = sorted(set(values) - ENVELOPE_FIELDS)
            raise EnvelopeError(f"Envelope fields differ (missing={missing}, extra={extra}).")

        depth = values["delegation_depth"]
        if isinstance(depth, bool) or not isinstance(depth, int):
            raise EnvelopeError("delegation_depth must be an integer.")
        if not 0 <= depth <= MAX_DELEGATION_DEPTH:
            raise EnvelopeError("delegation_depth is outside the allowed range.")

        owner = values["delegation_owner"]
        if owner not in DELEGATION_OWNERS:
            raise EnvelopeError("delegation_owner is not an allowed owner.")

        parent = values["parent_session_id"]
        if depth == 0:
            if parent is not None:
                raise EnvelopeError("A root envelope must have a null parent_session_id.")
        else:
            parent = _nonempty_identifier("parent_session_id", parent)

        return cls(
            operation_id=_nonempty_identifier("operation_id", values["operation_id"]),
            idempotency_key=_nonempty_identifier(
                "idempotency_key", values["idempotency_key"]
            ),
            parent_session_id=parent,
            delegation_owner=owner,
            delegation_depth=depth,
            cwd_realpath=_canonical_directory(values["cwd_realpath"], fixture_root),
            deadline_at=_deadline(values["deadline_at"], now),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return metadata fields only; prompt/result content is never part of the envelope."""

        return asdict(self)


def child_envelope(
    parent: OperationEnvelope,
    *,
    parent_session_id: str,
    delegation_owner: str,
    now: datetime | None = None,
) -> OperationEnvelope:
    """Create a child while preserving operation and idempotency identity."""

    values = parent.to_mapping()
    values.update(
        parent_session_id=parent_session_id,
        delegation_owner=delegation_owner,
        delegation_depth=parent.delegation_depth + 1,
    )
    return OperationEnvelope.from_mapping(values, now=now)
