# Release Checklist

Use this checklist when preparing a small public release of a repository that uses Codex Agent Workflow Kit.

## 1. Confirm Scope

- Review the issue, milestone, or maintainer note that defines the release.
- Check `ROADMAP.md` for items that should move into or out of the release.
- Confirm the change set is small enough to review without hidden follow-up work.
- Record anything deferred in `HANDOFF.md`.

## 2. Run Local Verification

For this repository, run:

```bash
python -m unittest discover -s tests
python -m codex_multi_agent_workflow_kit.cli init .tmp_release_check
python -m codex_multi_agent_workflow_kit.cli check .tmp_release_check
```

Remove `.tmp_release_check` after the smoke test.

For another repository using the generated workflow files, run that repo's normal test command and then:

```bash
codex-workflow-kit check .
```

## 3. Review Public Surfaces

- README quick start still matches the current CLI behavior.
- `docs/maintainer-playbook.md` still reflects the maintainer workflow.
- `docs/security-checklist.md` still matches the project safety model.
- Generated templates do not imply hidden automation, secret handling, or a replacement for human review.
- Examples show realistic pass and fail output.

## 4. Check Repository Hygiene

- No unrelated files are staged.
- No temporary smoke-test folders remain.
- No generated caches, local paths, account names, credentials, or private data are included.
- `HANDOFF.md` lists commands run, known risks, and the next maintenance item.

## 5. Prepare The Release Note

Keep the release note short and maintainer-facing:

- What changed.
- Why it helps Codex-assisted maintainers.
- How to verify it.
- Any known limitations.

## 6. Final Gate

Before tagging or publishing, confirm:

- CI is passing on the release commit.
- The version number and release note describe the same scope.
- A maintainer has reviewed the final diff.
- The next small roadmap item is recorded.
