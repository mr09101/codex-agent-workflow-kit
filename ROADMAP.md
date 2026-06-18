# Roadmap

Codex Agent Workflow Kit is intentionally small. The roadmap favors practical maintainer workflows over broad automation.

## v0.1: Stable Starter Kit

- Keep the CLI dependency-free and easy to install.
- Maintain `init` and `check` coverage with standard-library tests.
- Improve README examples for OSS maintainers using Codex.
- Add maintainer-facing docs for issue triage, PR review, release prep, and handoff recovery.
- Add issue templates for workflow patterns, bugs, and feature requests.

## v0.2: Review And Release Gates

- Add a documented review checklist for agent-authored pull requests.
- Add a release checklist template for small OSS packages.
- Expand `check` with optional warnings for stale handoff files.
- Maintain examples that show passing and failing workflow checks.
- Document when to use manager, project lead, reviewer, and subagent roles.

## v0.3: Template Packs

- Add optional template packs for Python libraries, web apps, documentation-only repos, and artifact-heavy projects.
- Add examples for `FINAL_KEEP` archive discipline.
- Add issue triage templates that convert maintainer reports into scoped Codex tasks.
- Add guidance for using the kit with existing repositories without overwriting local conventions.

## Later Ideas

- Machine-readable checklist output for CI.
- Optional JSON summary mode for `check`.
- Example GitHub Actions workflow that initializes a temporary target and validates it.
- Public examples contributed by maintainers using the kit in real projects.

## Non-Goals

- Replacing human review.
- Managing secrets or credentials.
- Calling external AI APIs from the CLI.
- Enforcing one universal agent workflow for every project.
