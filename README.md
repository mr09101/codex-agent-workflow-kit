# Codex Agent Workflow Kit

[![CI](https://github.com/mr09101/codex-agent-workflow-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/mr09101/codex-agent-workflow-kit/actions/workflows/ci.yml)

**A dependency-free operational layer for OSS maintainers using Codex: manager roles, project leads, reviewer gates, durable handoffs, and clean final artifacts.**

Codex Agent Workflow Kit is an early-stage project for maintainers who want AI coding agents to be easier to review, continue, and audit. It turns the parts that usually live in chat history into small Markdown files and CI-checkable workflow hygiene.

The Python import module remains `codex_multi_agent_workflow_kit` so the package stays descriptive while the public repository name stays short.

## For OSS Maintainers Using Codex

This kit is for projects where Codex or another AI coding agent helps with real maintainer work:

- Triaging issues into scoped agent tasks.
- Assigning implementation to a project lead session.
- Running reviewer gates before merge or release.
- Recovering context through `HANDOFF.md` after a session reset.
- Keeping final user-facing artifacts separate from scratch outputs.
- Checking workflow files in CI before changes are accepted.

The goal is not to add ceremony. The goal is to make agent-assisted maintenance visible enough that humans can trust and continue it.

## Features

- `codex-workflow-kit init <target>` copies starter workflow files into a project.
- `codex-workflow-kit check <target>` verifies required files and headings.
- No runtime dependencies beyond Python 3.10+.
- No network calls.
- No generated secrets, credentials, or `.env` files.
- No overwrite by default. Existing files are skipped unless `--force` is passed.
- CI-friendly tests cover template creation, missing-file failures, missing-section failures, and no-overwrite behavior.
- Templates cover manager/project lead/reviewer roles, handoff discipline, review gates, repo hygiene, and final-artifact handling.

## Quick Start

Run from a local checkout:

```bash
python -m codex_multi_agent_workflow_kit.cli init ./my-agent-project
python -m codex_multi_agent_workflow_kit.cli check ./my-agent-project
```

After installing locally:

```bash
python -m pip install .
codex-workflow-kit init ./my-agent-project
codex-workflow-kit check ./my-agent-project
```

Use `--force` only when you intentionally want to refresh existing workflow files:

```bash
codex-workflow-kit init ./my-agent-project --force
```

## What Gets Generated

```text
my-agent-project/
|-- AGENTS.md
|-- WORKFLOW.md
|-- HANDOFF.md
`-- FINAL_KEEP/
    `-- README.md
```

- `AGENTS.md`: agent rules, role boundaries, safety expectations, and repo hygiene.
- `WORKFLOW.md`: manager, project lead, reviewer, verification, and release loops.
- `HANDOFF.md`: current status, recent changes, checks, risks, and next steps.
- `FINAL_KEEP/README.md`: rules for final artifacts and archive discipline.

## Maintainer Workflow Example

1. **Issue triage:** a maintainer labels an issue as a small Codex-ready task and records acceptance criteria.
2. **Manager pass:** a manager session chooses the repository, confirms constraints, and assigns a project lead.
3. **Project lead pass:** the lead edits files, runs tests, updates `HANDOFF.md`, and stages only related changes.
4. **Reviewer pass:** a reviewer checks public docs, generated artifacts, security notes, and release readiness.
5. **Final artifact pass:** user-facing outputs go in `FINAL_KEEP`; scratch files stay out of the final surface.
6. **Release pass:** CI runs tests and `codex-workflow-kit check` against generated workflow examples.

See [docs/maintainer-playbook.md](docs/maintainer-playbook.md) for PR review, issue triage, release prep, and handoff recovery scenarios.

## Safety Model

The kit is intentionally small and conservative:

- The CLI never calls external services.
- The CLI never creates secrets, tokens, keys, credentials, or `.env` files.
- `init` skips existing files by default.
- `check` exits with code `1` when required files or sections are missing.
- Templates ask agents to record assumptions, verification commands, risks, and remaining work.
- GitHub Actions can run the same tests used locally.

This does not replace human review. It creates visible surfaces where review can happen.

See [docs/security-checklist.md](docs/security-checklist.md) for a maintainer-facing checklist.

## Project Status

This is an early-stage OSS project. The first release focuses on a small, practical core:

- Standard-library CLI.
- Public-safe workflow templates.
- Tests that run without external services.
- Maintainer documentation for Codex-assisted operations.

The roadmap is intentionally incremental. See [ROADMAP.md](ROADMAP.md).

## Folder Structure

```text
.
|-- codex_multi_agent_workflow_kit/
|   |-- __init__.py
|   `-- cli.py
|-- templates/
|   |-- AGENTS.md
|   |-- WORKFLOW.md
|   |-- HANDOFF.md
|   `-- FINAL_KEEP/
|       `-- README.md
|-- docs/
|   |-- maintainer-playbook.md
|   |-- openai-oss-application.md
|   `-- security-checklist.md
|-- examples/
|   `-- ai-project-layout.md
|-- tests/
|   `-- test_cli.py
`-- .github/
    |-- ISSUE_TEMPLATE/
    `-- workflows/
```

## OpenAI OSS Application Note

This repository is a practical open source contribution for Codex users: a lightweight operations kit that improves multi-agent workflow, Codex Security-oriented operating habits, durable handoffs, review gates, repo hygiene, and auditable project delivery.

See [docs/openai-oss-application.md](docs/openai-oss-application.md) for the submitted application draft.
