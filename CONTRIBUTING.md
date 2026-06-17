# Contributing

Thank you for considering a contribution.

## Scope

This project should stay small and practical. Good contributions improve:

- Multi-agent workflow clarity.
- Safer Codex or AI coding agent operations.
- Handoff quality between sessions and tools.
- Repository hygiene and review gates.

## Local Checks

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init ./tmp-project
python -m codex_multi_agent_workflow_kit.cli check ./tmp-project
```

## Guidelines

- Keep runtime dependencies out unless they are clearly necessary.
- Keep templates public-safe and free of personal paths, accounts, tokens, or private data.
- Add tests for CLI behavior changes.
- Update `HANDOFF.md` when project state or verification changes.
