# Adopting the Kit in an Existing Repository

Use this workflow when a repository already has agent instructions, maintainer
notes, or release conventions that must remain intact.

## 1. Start from a Reviewable State

Before generating files, commit or otherwise preserve the repository's current
state. Confirm that unrelated local changes will not be mixed into the adoption:

```bash
git status --short
```

The kit does not manage Git state for you.

## 2. Preview the Templates

Generate a disposable preview outside the repository so you can compare the
kit's headings and guidance with local conventions:

```bash
python -m codex_multi_agent_workflow_kit.cli init ../workflow-kit-preview
```

Review the four generated files, then remove the preview when it is no longer
needed. Do not commit the preview directory.

## 3. Initialize Without `--force`

Run `init` against the existing repository without `--force`:

```bash
python -m codex_multi_agent_workflow_kit.cli init .
```

This creates missing workflow files and reports existing generated paths under
`Skipped existing files`. Existing regular files are left unchanged. The command
also rejects symlinks, junctions, and other reparse points in generated paths.

Treat `--force` as a full template refresh, not a merge operation. It overwrites
existing regular files at all generated paths, so it is usually the wrong choice
for adopting the kit in a customized repository.

## 4. Merge Required Headings Deliberately

Run the checker after initialization:

```bash
python -m codex_multi_agent_workflow_kit.cli check .
```

If an existing file uses different headings, `check` reports each missing file
or section and exits with code `1`. Keep the repository's useful instructions
and add the required headings manually rather than replacing the whole file.

The required surfaces are:

- `AGENTS.md`: safety, roles, review gates, handoff discipline, and repository hygiene.
- `WORKFLOW.md`: roles, the standard loop, review gates, verification, and release checks.
- `HANDOFF.md`: status, changes, verification, next steps, and risks.
- `FINAL_KEEP/README.md`: final artifacts, exclusions, archive policy, and review checks.

Repeat `check` until it passes, then inspect the Git diff and commit only the
workflow changes you intended to adopt.

## Adoption Checklist

- Existing project instructions are preserved.
- `init` was run without `--force`.
- Skipped files were reviewed and merged manually where needed.
- `check` passes.
- Preview files, caches, and unrelated changes are not staged.
- `HANDOFF.md` records the adoption decision and verification commands.
