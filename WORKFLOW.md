# Repository Workflow

This file describes how maintainers and AI coding agents should operate this repository. It is public-safe and applies to this repository itself. The generated target-project workflow template lives at `templates/WORKFLOW.md`.

## Current Scope

The project provides:

- A dependency-free Python CLI.
- Public workflow templates for Codex-assisted projects.
- Tests and CI checks for template initialization and validation.
- Maintainer documentation for review gates, handoffs, releases, and safety.

The project does not run Codex, call AI APIs, manage secrets, or replace human review.

## Standard Maintenance Loop

1. Inspect the request, `git status`, recent commits, README, roadmap, and `HANDOFF.md`.
2. Choose one small improvement.
3. Edit only the files needed for that improvement.
4. Run relevant tests and smoke checks.
5. Run a public-safety scan for private paths, emails, and secret-like values.
6. Update `HANDOFF.md`.
7. Stage related files only.
8. Commit with a conventional commit message.
9. Push only when requested.

## Review Gates

- Scope gate: the change matches the request and stays small.
- Safety gate: no secrets, `.env` files, credentials, private paths, or production data.
- Runtime gate: no new network behavior in the CLI.
- Template gate: generated workflow files remain public-safe.
- Verification gate: tests or smoke checks are recorded.
- Handoff gate: `HANDOFF.md` reflects the current state.

## No Secrets Required

This repository intentionally has no `.env.example`. The CLI needs no API key, token, model credential, account login, or external service configuration.

If a future feature appears to need secrets, maintainers should first decide whether that feature belongs in this project at all.

## Smoke Check Pattern

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init .tmp_workflow_check
python -m codex_multi_agent_workflow_kit.cli check .tmp_workflow_check
```

Remove `.tmp_workflow_check` after the check.
