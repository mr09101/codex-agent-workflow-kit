from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from .skill_sync import POLICY_VERSION, REQUIRED_ROOTS


ROOT_PRECEDENCE = ("vault", "claude", "codex", "agents")


def _stream_metadata(value: str) -> dict[str, object]:
    encoded = value.encode("utf-8", errors="replace")
    return {
        "stored": "metadata-only",
        "byte_length": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


@dataclass(frozen=True, slots=True)
class WatcherResult:
    status: str
    child_exit_code: int | None
    error_code: str | None
    source_manifest: str | None
    target_manifests: Mapping[str, str | None]
    failed_targets: tuple[str, ...]
    policy_version: str
    root_precedence: tuple[str, ...]
    stdout_metadata: Mapping[str, object]
    stderr_metadata: Mapping[str, object]

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status,
            "child_exit_code": self.child_exit_code,
            "error_code": self.error_code,
            "source_manifest": self.source_manifest,
            "target_manifests": dict(sorted(self.target_manifests.items())),
            "failed_targets": list(self.failed_targets),
            "policy_version": self.policy_version,
            "root_precedence": list(self.root_precedence),
            "stdout": dict(self.stdout_metadata),
            "stderr": dict(self.stderr_metadata),
        }


def collect_watcher_result(
    command: Sequence[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: float = 300,
) -> WatcherResult:
    """Run a versioned sync child and prevent false success reporting.

    The function is a source adapter only; callers must explicitly supply the child
    command. It does not install, restart, or configure a live watcher.
    """

    if not command or any(not isinstance(part, str) or not part for part in command):
        raise ValueError("watcher command must be a non-empty argv sequence")
    try:
        child = runner(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = child.stdout or ""
        stderr = child.stderr or ""
        exit_code: int | None = child.returncode
        try:
            payload = json.loads(stdout)
            if not isinstance(payload, dict):
                raise ValueError("heartbeat must be an object")
        except (json.JSONDecodeError, ValueError):
            payload = {}
            parse_error = True
        else:
            parse_error = False
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        exit_code = None
        payload = {}
        parse_error = False

    raw_targets = payload.get("target_manifests", {})
    targets = (
        {name: raw_targets.get(name) for name in sorted(REQUIRED_ROOTS)}
        if isinstance(raw_targets, dict)
        else {name: None for name in sorted(REQUIRED_ROOTS)}
    )
    raw_failed = payload.get("failed_targets", [])
    failed = tuple(
        sorted(
            name
            for name in raw_failed
            if isinstance(name, str) and name in REQUIRED_ROOTS
        )
    ) if isinstance(raw_failed, list) else tuple(sorted(REQUIRED_ROOTS))
    policy_matches = payload.get("policy_version") == POLICY_VERSION
    roots_complete = set(raw_targets) == REQUIRED_ROOTS if isinstance(raw_targets, dict) else False
    manifests_match = (
        isinstance(payload.get("source_manifest"), str)
        and all(targets[name] == payload["source_manifest"] for name in REQUIRED_ROOTS)
    )
    success = (
        exit_code == 0
        and not parse_error
        and payload.get("status") == "SUCCESS"
        and policy_matches
        and roots_complete
        and manifests_match
        and not failed
    )
    if success:
        error_code = None
    elif exit_code is None:
        error_code = "WATCHER_CHILD_TIMEOUT"
    elif parse_error:
        error_code = "WATCHER_INVALID_HEARTBEAT"
    elif exit_code != 0:
        error_code = "WATCHER_CHILD_NONZERO"
    elif not policy_matches:
        error_code = "WATCHER_POLICY_MISMATCH"
    elif failed:
        error_code = "WATCHER_TARGET_FAILURE"
    else:
        error_code = "WATCHER_MANIFEST_MISMATCH"

    return WatcherResult(
        status="SUCCESS" if success else "FAILURE",
        child_exit_code=exit_code,
        error_code=error_code,
        source_manifest=(
            payload.get("source_manifest")
            if isinstance(payload.get("source_manifest"), str)
            else None
        ),
        target_manifests=targets,
        failed_targets=failed or (() if success else tuple(sorted(REQUIRED_ROOTS))),
        policy_version=POLICY_VERSION,
        root_precedence=ROOT_PRECEDENCE,
        stdout_metadata=_stream_metadata(stdout),
        stderr_metadata=_stream_metadata(stderr),
    )
