"""Command line interface for Codex Multi-Agent Workflow Kit."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from .envelope import EnvelopeError, OperationEnvelope
from .model_policy import load_default_policy, resolve_role
from .skill_sync import (
    SkillSyncError,
    failure_heartbeat,
    sync_skill_roots,
    verify_skill_roots,
)


TEMPLATES = {
    "AGENTS.md": """# Agent Operating Guide

## Safety Rules

- Do not commit secrets, tokens, passwords, `.env` files, or private data.
- State assumptions before editing when the request is ambiguous.
- Make scoped changes and preserve user work you did not create.
- Run relevant checks before reporting completion.

## Session Roles

- Manager: routes requests and reviews final status.
- Project lead: owns implementation, tests, Git state, and handoff updates.
- Reviewer: checks safety, documentation, and release readiness.

## Review Gates

- Security: no secrets or private data.
- Behavior: requested behavior is implemented and verified.
- Documentation: public text matches the current project state.
- Git hygiene: only related files are staged.

## Handoff Discipline

Update `HANDOFF.md` after meaningful work with status, changes, checks, risks, and next steps.

## Repository Hygiene

Keep temporary files, generated caches, and unrelated artifacts out of Git.
""",
    "WORKFLOW.md": """# Workflow

## Roles

- Manager: accepts requests and validates final reports.
- Project lead: edits files, runs tests, and updates handoffs.
- Reviewer: checks public quality and risk before release.

## Standard Loop

1. Intake the request and constraints.
2. Inspect relevant files.
3. Make the smallest safe change.
4. Verify with focused commands.
5. Update the handoff.
6. Commit only related files when appropriate.

## Review Gates

- Scope gate.
- Safety gate.
- Test gate.
- Documentation gate.
- Release gate.

## Verification

Record exact commands and outcomes so another agent can reproduce them.

## Release Checklist

- Required files exist.
- Tests pass or skipped checks are explained.
- Public docs contain no private paths, accounts, or secrets.
""",
    "HANDOFF.md": """# Handoff

## Current Status

- Status: Not started.
- Last updated: YYYY-MM-DD.

## Recent Changes

- No changes recorded yet.

## Verification

- Not run yet.

## Next Steps

- Define the task.
- Inspect the project.
- Make a scoped change.
- Run checks.

## Risks and Notes

- Keep this file public-safe.
- Do not include secrets or private data.
""",
    "FINAL_KEEP/README.md": """# FINAL_KEEP

## What Belongs Here

- Latest user-facing reports, images, videos, decks, documents, or exports.

## What Stays Out

- Scratch files, temporary renders, debug logs, caches, and private input data.

## Archive Policy

Move older final outputs to an archive folder instead of mixing them with the latest output.

## Review Checklist

- Latest artifact is present.
- File names are clear.
- No secrets or private data are included.
""",
}

REQUIRED_SECTIONS = {
    "AGENTS.md": [
        "# Agent Operating Guide",
        "## Safety Rules",
        "## Session Roles",
        "## Review Gates",
        "## Handoff Discipline",
        "## Repository Hygiene",
    ],
    "WORKFLOW.md": [
        "# Workflow",
        "## Roles",
        "## Standard Loop",
        "## Review Gates",
        "## Verification",
        "## Release Checklist",
    ],
    "HANDOFF.md": [
        "# Handoff",
        "## Current Status",
        "## Recent Changes",
        "## Verification",
        "## Next Steps",
        "## Risks and Notes",
    ],
    "FINAL_KEEP/README.md": [
        "# FINAL_KEEP",
        "## What Belongs Here",
        "## What Stays Out",
        "## Archive Policy",
        "## Review Checklist",
    ],
}

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


class CliError(Exception):
    """A public-safe command error that does not expose local paths."""


def _absolute_path(value: str) -> Path:
    return Path(os.path.abspath(Path(value).expanduser()))


def _is_filesystem_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False

    attributes = getattr(metadata, "st_file_attributes", 0)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & FILE_ATTRIBUTE_REPARSE_POINT
    )


def _validate_target_root(target: Path) -> Path:
    if _is_filesystem_link(target):
        raise CliError("Unsafe filesystem link at target root.")
    return target.resolve(strict=True)


def _validate_destination(target: Path, root: Path, relative_path: str) -> Path:
    destination = target / relative_path
    current = target
    for part in Path(relative_path).parts:
        current /= part
        if _is_filesystem_link(current):
            raise CliError(f"Unsafe filesystem link at {relative_path}.")

    try:
        destination.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise CliError(f"Path escapes target root: {relative_path}.") from error

    return destination


def init_target(target: Path, *, force: bool = False) -> tuple[list[str], list[str]]:
    if _is_filesystem_link(target):
        raise CliError("Unsafe filesystem link at target root.")
    target.mkdir(parents=True, exist_ok=True)
    root = _validate_target_root(target)

    for relative_path in TEMPLATES:
        _validate_destination(target, root, relative_path)

    written: list[str] = []
    skipped: list[str] = []

    for relative_path, content in TEMPLATES.items():
        root = _validate_target_root(target)
        destination = _validate_destination(target, root, relative_path)
        if destination.exists() and not force:
            skipped.append(relative_path)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        root = _validate_target_root(target)
        destination = _validate_destination(target, root, relative_path)
        destination.write_text(content, encoding="utf-8", newline="\n")
        written.append(relative_path)

    return written, skipped


def check_target(target: Path) -> list[str]:
    errors: list[str] = []
    root = _validate_target_root(target)

    for relative_path, sections in REQUIRED_SECTIONS.items():
        path = _validate_destination(target, root, relative_path)
        if not path.is_file():
            errors.append(f"Missing required file: {relative_path}")
            continue

        text = path.read_text(encoding="utf-8")
        headings = {line.strip().lower() for line in text.splitlines() if line.startswith("#")}
        for section in sections:
            if section.lower() not in headings:
                errors.append(f"Missing section in {relative_path}: {section}")

    return errors


def _print_list(title: str, values: list[str]) -> None:
    if not values:
        return

    print(f"{title}:")
    for value in values:
        print(f"  - {value}")


def run_init(args: argparse.Namespace) -> int:
    target = _absolute_path(args.target)
    written, skipped = init_target(target, force=args.force)
    print(f"Initialized workflow templates in {target}")
    _print_list("Created or updated", written)
    _print_list("Skipped existing files", skipped)
    if skipped:
        print("Use --force to overwrite skipped files.")
    return 0


def run_check(args: argparse.Namespace) -> int:
    target = _absolute_path(args.target)
    errors = check_target(target)
    if errors:
        print(f"Workflow check failed for {target}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Workflow check passed for {target}")
    return 0


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise CliError("Input JSON is not a valid UTF-8 object.") from error
    if not isinstance(value, dict):
        raise CliError("Input JSON must be an object.")
    return value


def run_validate_envelope(args: argparse.Namespace) -> int:
    values = _read_json_object(_absolute_path(args.envelope))
    fixture_root = _absolute_path(args.fixture_root) if args.fixture_root else None
    envelope = OperationEnvelope.from_mapping(values, fixture_root=fixture_root)
    print(
        json.dumps(
            {
                "status": "VALID",
                "error_code": None,
                "operation_id": envelope.operation_id,
                "delegation_depth": envelope.delegation_depth,
            },
            sort_keys=True,
        )
    )
    return 0


def run_harness_resolve(args: argparse.Namespace) -> int:
    catalog = _read_json_object(_absolute_path(args.catalog))
    policy = (
        _read_json_object(_absolute_path(args.policy))
        if args.policy
        else load_default_policy()
    )
    result = resolve_role(
        args.role,
        catalog,
        policy=policy,
        requested_capabilities=set(args.capability),
    )
    print(json.dumps(result.to_mapping(), sort_keys=True))
    return 0 if result.error_code is None else 3


def _parse_targets(values: list[str]) -> dict[str, Path]:
    targets: dict[str, Path] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path or name in targets:
            raise CliError("Each --target must be a unique name=path pair.")
        targets[name] = _absolute_path(path)
    return targets


def run_skill_sync(args: argparse.Namespace) -> int:
    targets = _parse_targets(args.target)
    try:
        result = sync_skill_roots(
            _absolute_path(args.source),
            targets,
            fixture_root=_absolute_path(args.fixture_root),
            apply=args.apply,
        )
    except SkillSyncError as error:
        payload = error.heartbeat or failure_heartbeat(
            "sync", error_code=getattr(error, "code", "SYNC_FAILED")
        )
        print(json.dumps(payload, sort_keys=True))
        return 4
    print(json.dumps(result.to_mapping(), sort_keys=True))
    return 0


def run_skill_verify(args: argparse.Namespace) -> int:
    targets = _parse_targets(args.target)
    try:
        result = verify_skill_roots(
            _absolute_path(args.source),
            targets,
            fixture_root=_absolute_path(args.fixture_root),
        )
    except SkillSyncError as error:
        payload = error.heartbeat or failure_heartbeat(
            "verify", error_code=getattr(error, "code", "VERIFY_FAILED")
        )
        print(json.dumps(payload, sort_keys=True))
        return 5
    print(json.dumps(result.to_mapping(), sort_keys=True))
    return 0 if result.ok else 5


def _add_skill_roots(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fixture-root", required=True, help="OS temp fixture root.")
    parser.add_argument("--source", required=True, help="Canonical fixture source.")
    parser.add_argument(
        "--target", action="append", required=True, help="Runtime root as name=path."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-workflow-kit",
        description="Initialize and check Codex multi-agent workflow files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Copy workflow templates.")
    init_parser.add_argument("target", help="Target folder.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    init_parser.set_defaults(func=run_init)

    check_parser = subparsers.add_parser("check", help="Check workflow files.")
    check_parser.add_argument("target", help="Target folder.")
    check_parser.set_defaults(func=run_check)

    envelope_parser = subparsers.add_parser(
        "validate-envelope", help="Validate a metadata-only harness envelope."
    )
    envelope_parser.add_argument("envelope", help="Seven-field envelope JSON file.")
    envelope_parser.add_argument(
        "--fixture-root", help="Optional allowed cwd boundary for isolated tests."
    )
    envelope_parser.set_defaults(func=run_validate_envelope)

    resolver_parser = subparsers.add_parser(
        "harness-resolve", help="Resolve a role against an explicit capability catalog."
    )
    resolver_parser.add_argument("role", help="Policy role name.")
    resolver_parser.add_argument("--catalog", required=True, help="Capability catalog JSON.")
    resolver_parser.add_argument("--policy", help="Optional policy JSON override.")
    resolver_parser.add_argument(
        "--capability", action="append", default=[], help="Requested task capability."
    )
    resolver_parser.set_defaults(func=run_harness_resolve)

    sync_parser = subparsers.add_parser(
        "skill-sync", help="Plan or apply a transaction inside an OS temp fixture."
    )
    mode = sync_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Validate without writing.")
    mode.add_argument("--apply", action="store_true", help="Apply inside the fixture boundary.")
    _add_skill_roots(sync_parser)
    sync_parser.set_defaults(func=run_skill_sync)

    verify_parser = subparsers.add_parser(
        "skill-verify", help="Verify all three fixture runtime roots and emit a heartbeat."
    )
    _add_skill_roots(verify_parser)
    verify_parser.set_defaults(func=run_skill_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
    except EnvelopeError as error:
        print(
            json.dumps({"status": "ERROR", "error_code": error.code}),
            file=sys.stderr,
        )
        return 2
    except SkillSyncError as error:
        code = getattr(error, "code", "SYNC_FAILED")
        print(json.dumps({"status": "ERROR", "error_code": code}), file=sys.stderr)
        return 4
    except UnicodeError:
        print("ERROR: Required workflow file is not valid UTF-8.", file=sys.stderr)
    except PermissionError:
        print("ERROR: Permission denied during filesystem operation.", file=sys.stderr)
    except FileExistsError:
        print("ERROR: Target conflicts with an existing filesystem entry.", file=sys.stderr)
    except NotADirectoryError:
        print("ERROR: A target path component is not a directory.", file=sys.stderr)
    except IsADirectoryError:
        print("ERROR: A required file path is an existing directory.", file=sys.stderr)
    except OSError:
        print("ERROR: Filesystem operation failed.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
