# Maintainer Playbook

This playbook shows how an OSS maintainer can use Codex Agent Workflow Kit to keep agent-assisted work reviewable and easy to continue.

## Roles

- **Manager:** receives an issue or request, identifies the project, writes constraints, and assigns work.
- **Project lead:** makes code or documentation changes, runs checks, updates `HANDOFF.md`, and prepares the commit.
- **Reviewer:** checks safety, scope, public docs, final artifacts, and release readiness.
- **Maintainer:** owns final merge, release, and project direction.

## Scenario 1: Issue Triage

1. Read the issue and separate user-visible behavior from implementation guesses.
2. Label the issue as one of:
   - `workflow-pattern`
   - `bug`
   - `feature`
   - `documentation`
3. Create a short manager note:
   - expected outcome
   - files likely in scope
   - files explicitly out of scope
   - verification command
4. Ask the project lead agent to inspect before editing.
5. Require `HANDOFF.md` to list the final status and tests.

## Scenario 2: Pull Request Review

Use a reviewer pass before merge:

- Confirm the change matches the issue.
- Check that unrelated files were not edited.
- Check that no secrets, private paths, account names, or generated caches were added.
- Confirm tests or documented verification ran.
- Confirm public docs explain user-facing behavior.
- Confirm `HANDOFF.md` records remaining risks.

For this repo, a minimal review command set is:

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init .tmp_playbook_check
python -m codex_multi_agent_workflow_kit.cli check .tmp_playbook_check
```

Remove `.tmp_playbook_check` after the smoke test.

## Scenario 3: Release Prep

Use `docs/release-checklist.md` as the detailed release gate. The quick pass is:

1. Review `ROADMAP.md` and identify the release scope.
2. Run tests locally.
3. Run a fresh `init`/`check` smoke test.
4. Review `SECURITY.md` and `docs/security-checklist.md`.
5. Confirm README quick start still works.
6. Update `HANDOFF.md` with:
   - release status
   - commands run
   - known risks
   - next release target

## Scenario 4: Handoff Recovery

When a Codex session loses context or a new maintainer picks up the work:

1. Read `HANDOFF.md`.
2. Read the related issue or request.
3. Run `git status --short`.
4. Inspect recent commits.
5. Re-run the verification commands listed in the handoff.
6. Continue only after the current state is understood.

## Practical Rule

If future maintainers cannot understand what changed, why it changed, how it was checked, and what remains risky, the agent workflow is not done yet.
