# Core Capability

Codex Agent Workflow Kit is a small scaffold-and-check tool for maintainers using Codex or other AI coding agents.

## What It Actually Does

The CLI has two commands:

- `init <target>` copies workflow templates into a target project.
- `check <target>` verifies that the target project has the required workflow files and sections.

That is the core. The value is not hidden automation. The value is making AI-assisted project operations visible, repeatable, and reviewable.

The role names in the templates are workflow labels for maintainers to use in Markdown handoffs. They are not an agent scheduler or orchestration runtime. Likewise, `check` validates required files and headings; it does not judge implementation quality or replace review.

## The Generated Operating Files

Running `init` creates:

```text
target-project/
|-- AGENTS.md
|-- WORKFLOW.md
|-- HANDOFF.md
`-- FINAL_KEEP/
    `-- README.md
```

These files answer practical maintainer questions:

- `AGENTS.md`: What rules should agents follow in this repo?
- `WORKFLOW.md`: How do manager, project lead, and reviewer passes work?
- `HANDOFF.md`: What changed, what was checked, and what remains risky?
- `FINAL_KEEP/README.md`: Which outputs are final, and which are scratch work?

## Example Session

```bash
python -m codex_multi_agent_workflow_kit.cli init ./demo-project
python -m codex_multi_agent_workflow_kit.cli check ./demo-project
```

Expected result:

```text
Initialized workflow templates in .../demo-project
Workflow check passed for .../demo-project
```

If a required file or heading is missing, `check` prints the missing item and exits with code `1`.

## What It Does Not Do

- It does not run Codex.
- It does not call OpenAI or any other network API.
- It does not create `.env` files, credentials, tokens, or keys.
- It does not overwrite existing files unless `--force` is passed.
- It does not replace maintainer review.

## Why Maintainers Might Want It

Agent-assisted work often fails in the handoff layer: the code may be fine, but the next maintainer cannot tell what happened, what was verified, or whether final artifacts are mixed with scratch files.

This kit gives that operating layer a simple file shape and a small validation command.
