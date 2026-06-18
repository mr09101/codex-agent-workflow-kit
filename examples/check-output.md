# Check Output Examples

These examples show what maintainers should expect from the `init` and `check` commands during local review or CI debugging.

## Passing Scaffold

Command:

```bash
python -m codex_multi_agent_workflow_kit.cli init ./demo-project
python -m codex_multi_agent_workflow_kit.cli check ./demo-project
```

Expected output shape:

```text
Initialized workflow templates in <absolute-path>/demo-project
Created or updated:
  - AGENTS.md
  - WORKFLOW.md
  - HANDOFF.md
  - FINAL_KEEP/README.md
Workflow check passed for <absolute-path>/demo-project
```

The exact absolute path depends on where the command runs. The important signal is that `check` exits with code `0`.

## Failing Missing Files

Command:

```bash
python -m codex_multi_agent_workflow_kit.cli check ./empty-project
```

Expected output shape:

```text
Workflow check failed for <absolute-path>/empty-project
ERROR: Missing required file: AGENTS.md
ERROR: Missing required file: WORKFLOW.md
ERROR: Missing required file: HANDOFF.md
ERROR: Missing required file: FINAL_KEEP/README.md
```

The command exits with code `1`, which makes it suitable for pull request checks and GitHub Actions jobs.

## Failing Missing Section

If a required file exists but a required heading is missing, `check` names the file and heading:

```text
Workflow check failed for <absolute-path>/demo-project
ERROR: Missing section in WORKFLOW.md: ## Roles
```

This keeps the failure actionable for maintainers and agent sessions: restore the required heading or intentionally update the kit's section requirements with tests.

## Review Use

For a small pull request, a maintainer can ask an agent or contributor to include:

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init .tmp_workflow_check
python -m codex_multi_agent_workflow_kit.cli check .tmp_workflow_check
```

Remove `.tmp_workflow_check` after the smoke test.
