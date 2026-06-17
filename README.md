# Codex Multi-Agent Workflow Kit

A practical starter kit for running Codex and other AI coding agents across manager threads, project lead threads, review threads, and durable handoff files.

## What It Is

This repository provides a small Python CLI and public-safe Markdown templates for AI-assisted software projects. The CLI can:

- `init <target>`: copy workflow templates into a project without overwriting existing files by default.
- `check <target>`: verify that required operating files and sections exist.

The project uses Python 3.10+ and the standard library only.

## Why This Exists

AI coding agents are most useful when work is visible, reproducible, and reviewable. This kit turns practical operating habits into reusable files:

- Clear manager, project lead, and reviewer responsibilities.
- Durable handoffs across sessions and tools.
- Review gates for security, documentation, verification, and release readiness.
- Repo hygiene checks that can run locally or in CI.

## Quick Start

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

Use `--force` only when you intentionally want to overwrite existing template files.

## Folder Structure

```text
.
├── codex_multi_agent_workflow_kit/
│   ├── __init__.py
│   └── cli.py
├── templates/
│   ├── AGENTS.md
│   ├── WORKFLOW.md
│   ├── HANDOFF.md
│   └── FINAL_KEEP/
│       └── README.md
├── docs/
├── examples/
├── tests/
└── .github/workflows/
```

## Codex Security / Safety Model

- The CLI makes no network calls.
- The CLI does not generate secrets, tokens, or `.env` files.
- `init` does not overwrite existing files unless `--force` is passed.
- `check` exits with code `1` when required files or headings are missing.
- Templates ask agents to record assumptions, verification, risks, and next steps.

## Example Workflow

1. A manager thread receives the request and identifies the project.
2. A project lead thread owns code changes, tests, Git state, and `HANDOFF.md`.
3. A reviewer checks public text, user-facing outputs, and release risks.
4. The lead runs tests and `codex-workflow-kit check .`.
5. The lead commits only related files.

## OpenAI OSS Application Note

This repository is intended to demonstrate a practical open source contribution to AI coding operations: multi-agent workflow, Codex Security habits, handoff discipline, repo hygiene, review gates, and durable project operations.

See [docs/openai-oss-application.md](docs/openai-oss-application.md) for an application-ready draft.
