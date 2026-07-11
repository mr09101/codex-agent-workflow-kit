"""Command line interface for Codex Multi-Agent Workflow Kit."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
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
