# Agent Pull Request Review Checklist

Use this checklist before merging a pull request authored by, or materially changed by, Codex or another AI coding agent.

The goal is not to make agent work special. The goal is to make the review evidence easy for a maintainer to inspect.

## 1. Confirm Scope

- The pull request maps to one issue, maintainer request, or documented maintenance task.
- The changed files match the stated scope.
- Unrelated refactors, generated files, caches, and scratch outputs are absent.
- Any deferred work is listed in `HANDOFF.md` or the pull request description.

## 2. Inspect The Diff

Run a local diff pass before relying on summaries:

```bash
git status --short
git diff --stat
git diff
```

Check for:

- Public docs that describe behavior the code or templates actually provide.
- Tests that match the behavior being changed.
- Template wording that does not imply hidden automation, secret handling, or replacement of human review.
- No accidental edits to unrelated workflow, release, or repository metadata.

## 3. Run Review Gates

For this repository, use:

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init .tmp_agent_pr_review
python -m codex_multi_agent_workflow_kit.cli check .tmp_agent_pr_review
git diff --check
```

Remove `.tmp_agent_pr_review` after the smoke test.

For another repository using this kit, run the repository's normal test command and then:

```bash
codex-workflow-kit check .
```

If a check cannot run, record the reason and the residual risk before merge.

## 4. Review Public Safety

Confirm the pull request does not include:

- Secrets, tokens, credentials, private keys, or `.env` files.
- Private local paths, account names, email addresses, or production data.
- Debug logs, generated caches, temporary smoke-test folders, or scratch artifacts.
- Final user-facing artifacts mixed with temporary work.

Use `docs/security-checklist.md` for the broader safety pass.

## 5. Check Handoff Quality

Before merge, `HANDOFF.md` should answer:

- What changed.
- What was verified.
- What remains risky or incomplete.
- What the next maintainer should do.

The pull request is not ready if a future maintainer would need to reconstruct the work from chat history.

## 6. Final Maintainer Decision

Merge only after:

- Scope, safety, test, documentation, and handoff gates are satisfied.
- The diff is small enough to review confidently.
- Remaining risks are accepted by the maintainer.
