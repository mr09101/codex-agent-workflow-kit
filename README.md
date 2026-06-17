# Codex Agent Workflow Kit

**A dependency-free operational layer for running Codex and AI coding agents with manager roles, project leads, reviewer gates, durable handoffs, and clean final artifacts.**

Recommended public repository name: `codex-agent-workflow-kit`.

The Python import module remains `codex_multi_agent_workflow_kit` so the package stays descriptive while the public repo name stays short.

## Why It Is Useful

Codex is strongest when project operations are explicit. This kit gives AI-assisted projects a small, repeatable structure for the parts that usually live only in chat history:

- Manager, project lead, and reviewer responsibilities.
- Durable `HANDOFF.md` files for context resets and tool changes.
- Review gates for safety, docs, verification, release readiness, and Git hygiene.
- `FINAL_KEEP` conventions so final user-facing artifacts are not mixed with scratch work.
- CI-checkable repo hygiene through a tiny Python CLI.
- Conservative defaults for public and private projects.

## Features

- `codex-workflow-kit init <target>` copies starter workflow files into a project.
- `codex-workflow-kit check <target>` verifies required files and headings.
- No runtime dependencies beyond Python 3.10+.
- No network calls.
- No generated secrets, credentials, or `.env` files.
- No overwrite by default. Existing files are skipped unless `--force` is passed.
- Works locally, in CI, or as a pre-release review step.

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
- `WORKFLOW.md`: manager, lead, reviewer, verification, and release loops.
- `HANDOFF.md`: current status, recent changes, checks, risks, and next steps.
- `FINAL_KEEP/README.md`: rules for final artifacts and archive discipline.

## Safety Model

The kit is intentionally small and conservative:

- The CLI never calls external services.
- The CLI never creates secrets, tokens, keys, credentials, or `.env` files.
- `init` skips existing files by default.
- `check` exits with code `1` when required files or sections are missing.
- Templates ask agents to record assumptions, verification commands, risks, and remaining work.
- GitHub Actions can run the same tests used locally, including template creation, missing-file failures, missing-section failures, and no-overwrite behavior.

This does not replace human review. It creates visible surfaces where review can happen.

## Example Workflow

1. A manager thread receives a request and identifies the target project.
2. A project lead thread owns file changes, tests, Git state, and `HANDOFF.md`.
3. A reviewer thread checks public text, user-facing outputs, safety risks, and release readiness.
4. Final artifacts are placed in `FINAL_KEEP`; scratch outputs stay elsewhere.
5. The lead runs tests and `codex-workflow-kit check .`.
6. The lead commits only related files after the review gates pass.

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
|   `-- openai-oss-application.md
|-- examples/
|   `-- ai-project-layout.md
|-- tests/
|   `-- test_cli.py
`-- .github/
    `-- workflows/
        `-- ci.yml
```

## OpenAI OSS Application Note

This repository is designed to be a practical open source contribution for Codex users: a lightweight operations kit that improves multi-agent workflow, Codex Security-oriented operating habits, durable handoffs, review gates, repo hygiene, and auditable project delivery.

See [docs/openai-oss-application.md](docs/openai-oss-application.md) for a paste-ready application draft.
