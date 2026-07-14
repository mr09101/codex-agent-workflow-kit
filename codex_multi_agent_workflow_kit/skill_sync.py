"""Transactional, fixture-bounded skill tree synchronization."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .contracts import HarnessErrorCode


REQUIRED_ROOTS = frozenset({"claude", "codex", "agents"})
SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
)
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
POLICY_VERSION = "2026-07-15.p0"
PROCESS_INSTANCE_ID = f"{os.getpid()}-{uuid.uuid4().hex}"


class SkillSyncError(RuntimeError):
    """Fail-closed sync or verification error."""

    def __init__(self, message: str, *, heartbeat: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.heartbeat = dict(heartbeat) if heartbeat is not None else None


class ShadowConflict(SkillSyncError):
    """The same frontmatter name has different full-tree content."""

    code = HarnessErrorCode.SHADOW_CONFLICT.value


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class TreeManifest:
    files: Mapping[str, ManifestEntry]
    sha256: str


@dataclass(frozen=True, slots=True)
class TargetVerification:
    missing: tuple[str, ...]
    mismatched: tuple[str, ...]
    extra: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not (self.missing or self.mismatched or self.extra)

    def to_mapping(self, manifest: str | None) -> dict[str, object]:
        return {
            "manifest": manifest,
            "missing": list(self.missing),
            "mismatched": list(self.mismatched),
            "extra": list(self.extra),
        }


@dataclass(frozen=True, slots=True)
class VerificationResult:
    ok: bool
    source_manifest: str
    targets: Mapping[str, TargetVerification]
    target_manifests: Mapping[str, str | None]
    completed_at: str

    @property
    def failed_targets(self) -> tuple[str, ...]:
        return tuple(sorted(name for name, result in self.targets.items() if not result.ok))

    def to_mapping(self) -> dict[str, object]:
        return _heartbeat(
            operation="verify",
            success=self.ok,
            error_code=None if self.ok else "VERIFY_FAILED",
            source_manifest=self.source_manifest,
            target_manifests=self.target_manifests,
            failed_targets=self.failed_targets,
            completed_at=self.completed_at,
            targets={
                name: result.to_mapping(self.target_manifests.get(name))
                for name, result in sorted(self.targets.items())
            },
        )


@dataclass(frozen=True, slots=True)
class SyncResult:
    mode: str
    source_manifest: str
    target_manifests: Mapping[str, str | None]
    completed_at: str

    def to_mapping(self) -> dict[str, object]:
        return _heartbeat(
            operation="sync",
            success=True,
            error_code=None,
            source_manifest=self.source_manifest,
            target_manifests=self.target_manifests,
            failed_targets=(),
            completed_at=self.completed_at,
            mode=self.mode,
        )


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _heartbeat(
    *,
    operation: str,
    success: bool,
    error_code: str | None,
    source_manifest: str | None,
    target_manifests: Mapping[str, str | None],
    failed_targets: tuple[str, ...] | list[str],
    completed_at: str | None = None,
    targets: Mapping[str, object] | None = None,
    mode: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "status": "SUCCESS" if success else "FAILURE",
        "operation": operation,
        "error_code": error_code,
        "source_manifest": source_manifest,
        "target_manifests": dict(sorted(target_manifests.items())),
        "completed_at": completed_at or _timestamp(),
        "failed_targets": sorted(set(failed_targets)),
        "process_instance_id": PROCESS_INSTANCE_ID,
        "policy_version": POLICY_VERSION,
        "runtime_status": {
            "windows": "SUCCESS" if success else "FAILURE",
            "wsl": "WSL_UNAVAILABLE",
        },
    }
    if targets is not None:
        result["targets"] = dict(sorted(targets.items()))
    if mode is not None:
        result["mode"] = mode
    return result


def failure_heartbeat(
    operation: str,
    *,
    error_code: str,
    failed_targets: tuple[str, ...] | list[str] = tuple(REQUIRED_ROOTS),
    source_manifest: str | None = None,
    target_manifests: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    """Create a metadata-only failure result without reading untrusted paths."""

    manifests = {
        name: None for name in REQUIRED_ROOTS
    } if target_manifests is None else dict(target_manifests)
    for name in REQUIRED_ROOTS:
        manifests.setdefault(name, None)
    return _heartbeat(
        operation=operation,
        success=False,
        error_code=error_code,
        source_manifest=source_manifest,
        target_manifests=manifests,
        failed_targets=failed_targets,
    )


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT
    )


def _system_temp_root() -> Path:
    return Path(tempfile.gettempdir()).resolve(strict=True)


def _fixture_boundary(fixture_root: Path) -> Path:
    absolute = Path(os.path.abspath(fixture_root))
    if not absolute.is_dir() or _is_link(absolute):
        raise SkillSyncError("fixture_root must be an existing real directory.")
    resolved = absolute.resolve(strict=True)
    try:
        resolved.relative_to(_system_temp_root())
    except ValueError as error:
        raise SkillSyncError("fixture_root must be below the operating-system temp root.") from error
    return resolved


def _bounded_path(path: Path, fixture_root: Path, *, must_exist: bool) -> Path:
    absolute = Path(os.path.abspath(path))
    resolved = absolute.resolve(strict=must_exist)
    try:
        resolved.relative_to(fixture_root)
    except ValueError as error:
        raise SkillSyncError("A sync path escapes the fixture boundary.") from error

    current = fixture_root
    relative = absolute.relative_to(fixture_root)
    for part in relative.parts:
        current /= part
        if current.exists() and _is_link(current):
            raise SkillSyncError("A sync path contains a filesystem link or reparse point.")
    return resolved


def _assert_no_links(root: Path) -> None:
    if _is_link(root):
        raise SkillSyncError("A skill root is a filesystem link or reparse point.")
    for directory, directories, filenames in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in [*directories, *filenames]:
            if _is_link(base / name):
                raise SkillSyncError("A skill tree contains a filesystem link or reparse point.")


def _validate_roots(
    source: Path, outputs: Mapping[str, Path], fixture_root: Path
) -> tuple[Path, dict[str, Path], Path]:
    if set(outputs) != REQUIRED_ROOTS:
        missing = sorted(REQUIRED_ROOTS - set(outputs))
        extra = sorted(set(outputs) - REQUIRED_ROOTS)
        raise SkillSyncError(f"Runtime roots differ (missing={missing}, extra={extra}).")
    boundary = _fixture_boundary(fixture_root)
    safe_source = _bounded_path(source, boundary, must_exist=True)
    if not safe_source.is_dir():
        raise SkillSyncError("Canonical source must be a directory.")
    _assert_no_links(safe_source)
    safe_outputs = {
        name: _bounded_path(path, boundary, must_exist=False)
        for name, path in sorted(outputs.items())
    }
    paths = [("source", safe_source), *sorted(safe_outputs.items())]
    for index, (left_name, left_path) in enumerate(paths):
        for right_name, right_path in paths[index + 1 :]:
            if (
                left_path == right_path
                or _is_relative_to(left_path, right_path)
                or _is_relative_to(right_path, left_path)
            ):
                raise SkillSyncError(
                    f"Skill roots overlap ({left_name}, {right_name}); refusing ambiguous swap."
                )
    return safe_source, safe_outputs, boundary


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return path != parent


def validate_skill_name(name: str) -> str:
    if not isinstance(name, str) or SKILL_NAME.fullmatch(name) is None:
        raise SkillSyncError("Skill name does not match the allowlist.")
    if name.casefold() in WINDOWS_RESERVED:
        raise SkillSyncError("Skill name is reserved by the operating system.")
    return name


def build_tree_manifest(root: Path) -> TreeManifest:
    root = Path(root)
    if not root.exists():
        return TreeManifest(files={}, sha256=hashlib.sha256(b"").hexdigest())
    if not root.is_dir():
        raise SkillSyncError("Manifest root is not a directory.")
    _assert_no_links(root)
    files: dict[str, ManifestEntry] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(block)
                digest.update(block)
        files[relative] = ManifestEntry(size=size, sha256=digest.hexdigest())
    payload = "\n".join(
        f"{path}\0{entry.size}\0{entry.sha256}" for path, entry in sorted(files.items())
    ).encode("utf-8")
    return TreeManifest(files=files, sha256=hashlib.sha256(payload).hexdigest())


def _frontmatter_name(skill_file: Path) -> str:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillSyncError("SKILL.md is missing frontmatter.")
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return validate_skill_name(line.split(":", 1)[1].strip().strip("'\""))
    raise SkillSyncError("SKILL.md is missing a frontmatter name.")


def _skill_tree_hash(skill_directory: Path) -> str:
    return build_tree_manifest(skill_directory).sha256


def _skill_identities(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    directories: dict[str, str] = {}
    for skill_file in sorted(root.rglob("SKILL.md")):
        name = _frontmatter_name(skill_file)
        directory_name = skill_file.parent.name
        digest = _skill_tree_hash(skill_file.parent)
        existing = names.get(name)
        if existing is not None and existing != digest:
            raise ShadowConflict("SHADOW_CONFLICT: duplicate skill name has different content.")
        existing_directory = directories.get(directory_name)
        if existing_directory is not None and existing_directory != digest:
            raise ShadowConflict(
                "SHADOW_CONFLICT: duplicate skill directory has different content."
            )
        names[name] = digest
        directories[directory_name] = digest
    return names, directories


def _skill_hashes(root: Path) -> dict[str, str]:
    return _skill_identities(root)[0]


def _raise_shadow_conflicts(source: Path, outputs: Mapping[str, Path]) -> None:
    source_manifest = build_tree_manifest(source).sha256
    target_manifests = {
        name: build_tree_manifest(root).sha256 if root.exists() else None
        for name, root in sorted(outputs.items())
    }
    try:
        seen_names, seen_directories = _skill_identities(source)
    except ShadowConflict as error:
        raise ShadowConflict(
            str(error),
            heartbeat=failure_heartbeat(
                "verify",
                error_code=HarnessErrorCode.SHADOW_CONFLICT.value,
                source_manifest=source_manifest,
                target_manifests=target_manifests,
            ),
        ) from error
    for target_name, root in sorted(outputs.items()):
        if not root.exists():
            continue
        names, directories = _skill_identities(root)
        for name, digest in sorted(names.items()):
            existing = seen_names.get(name)
            if existing is not None and existing != digest:
                raise ShadowConflict(
                    "SHADOW_CONFLICT: runtime skill name differs from the canonical full-tree hash.",
                    heartbeat=failure_heartbeat(
                        "verify",
                        error_code=HarnessErrorCode.SHADOW_CONFLICT.value,
                        failed_targets=(target_name,),
                        source_manifest=source_manifest,
                        target_manifests=target_manifests,
                    ),
                )
            seen_names[name] = digest
        for directory_name, digest in sorted(directories.items()):
            existing = seen_directories.get(directory_name)
            if existing is not None and existing != digest:
                raise ShadowConflict(
                    "SHADOW_CONFLICT: runtime skill directory differs from the canonical full-tree hash.",
                    heartbeat=failure_heartbeat(
                        "verify",
                        error_code=HarnessErrorCode.SHADOW_CONFLICT.value,
                        failed_targets=(target_name,),
                        source_manifest=source_manifest,
                        target_manifests=target_manifests,
                    ),
                )
            seen_directories[directory_name] = digest


def _compare(expected: TreeManifest, actual: TreeManifest) -> TargetVerification:
    expected_paths = set(expected.files)
    actual_paths = set(actual.files)
    return TargetVerification(
        missing=tuple(sorted(expected_paths - actual_paths)),
        mismatched=tuple(
            sorted(
                path
                for path in expected_paths & actual_paths
                if expected.files[path] != actual.files[path]
            )
        ),
        extra=tuple(sorted(actual_paths - expected_paths)),
    )


def verify_skill_roots(
    source: Path, outputs: Mapping[str, Path], *, fixture_root: Path
) -> VerificationResult:
    safe_source, safe_outputs, _ = _validate_roots(source, outputs, fixture_root)
    _raise_shadow_conflicts(safe_source, safe_outputs)
    expected = build_tree_manifest(safe_source)
    actual_manifests = {
        name: build_tree_manifest(path) for name, path in sorted(safe_outputs.items())
    }
    results = {
        name: _compare(expected, manifest)
        for name, manifest in actual_manifests.items()
    }
    return VerificationResult(
        ok=all(result.ok for result in results.values()),
        source_manifest=expected.sha256,
        targets=results,
        target_manifests={
            name: manifest.sha256 for name, manifest in actual_manifests.items()
        },
        completed_at=_timestamp(),
    )


class _ProcessLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._owned = False

    def __enter__(self) -> "_ProcessLock":
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise SkillSyncError("Another skill-sync process holds the lock.") from error
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "format": 1}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        self._owned = True
        return self

    def __exit__(self, *_: object) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False


def _remove_tree(path: Path) -> None:
    if path.exists():
        if _is_link(path):
            raise SkillSyncError("Refusing to remove a filesystem link.")
        shutil.rmtree(path)


def _fault(requested: str | None, step: str) -> None:
    if requested == step:
        raise SkillSyncError(f"Injected {step} failure.")


def sync_skill_roots(
    source: Path,
    outputs: Mapping[str, Path],
    *,
    fixture_root: Path,
    apply: bool = False,
    fault_step: str | None = None,
) -> SyncResult:
    """Dry-run or atomically replace all three fixture runtime roots."""

    safe_source, safe_outputs, boundary = _validate_roots(source, outputs, fixture_root)
    source_manifest = build_tree_manifest(safe_source)
    _skill_hashes(safe_source)
    if not apply:
        return SyncResult(
            mode="dry-run",
            source_manifest=source_manifest.sha256,
            target_manifests={
                name: build_tree_manifest(path).sha256 if path.exists() else None
                for name, path in sorted(safe_outputs.items())
            },
            completed_at=_timestamp(),
        )

    lock_path = boundary / ".skill-sync.lock"
    token = uuid.uuid4().hex
    stages: dict[str, Path] = {}
    backups: dict[str, Path | None] = {}
    swapped: list[str] = []
    with _ProcessLock(lock_path):
        try:
            for name, target in sorted(safe_outputs.items()):
                target.parent.mkdir(parents=True, exist_ok=True)
                stage = target.parent / f".{target.name}.stage-{token}"
                shutil.copytree(safe_source, stage, copy_function=shutil.copy2)
                stages[name] = stage
            _fault(fault_step, "copy")
            _fault(fault_step, "stage")

            for stage in stages.values():
                if build_tree_manifest(stage) != source_manifest:
                    raise SkillSyncError("Staged full-tree manifest differs from canonical source.")
            _fault(fault_step, "hash")

            for name, target in sorted(safe_outputs.items()):
                backup = target.parent / f".{target.name}.backup-{token}"
                if target.exists():
                    target.replace(backup)
                    backups[name] = backup
                else:
                    backups[name] = None
                stages[name].replace(target)
                swapped.append(name)
                if fault_step == "swap" and len(swapped) == 1:
                    _fault(fault_step, "swap")

            verification = verify_skill_roots(
                safe_source, safe_outputs, fixture_root=boundary
            )
            if not verification.ok:
                raise SkillSyncError("Post-swap full-tree verification failed.")
            _fault(fault_step, "post-verify")

            target_manifests = {
                name: build_tree_manifest(target).sha256
                for name, target in sorted(safe_outputs.items())
            }
            for backup in backups.values():
                if backup is not None:
                    _remove_tree(backup)
            return SyncResult(
                mode="apply",
                source_manifest=source_manifest.sha256,
                target_manifests=target_manifests,
                completed_at=_timestamp(),
            )
        except Exception as error:
            for name in reversed(swapped):
                target = safe_outputs[name]
                _remove_tree(target)
                backup = backups[name]
                if backup is not None and backup.exists():
                    backup.replace(target)
            if isinstance(error, SkillSyncError):
                raise
            raise SkillSyncError("Skill sync failed and original targets were restored.") from error
        finally:
            for stage in stages.values():
                _remove_tree(stage)
            for name, backup in backups.items():
                if backup is not None and backup.exists() and name not in swapped:
                    backup.replace(safe_outputs[name])
