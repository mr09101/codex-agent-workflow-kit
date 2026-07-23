# Handoff

## Independent QA Convergence Update (authoritative, 2026-07-15)

- The central resolver is the production source for role/model/thinking/fallback/capabilities, including `root_manager = gpt-5.6-sol / ultra` and structured `UNAVAILABLE`.
- `skill-source-sync` accepts only explicitly injected real roots named `source`, `claude`, `codex`, and `agents`; it has no built-in live paths and defaults to dry-run.
- The adapter enforces exact allowlists, realpath/reparse and overlap boundaries, an external process lock, staging, fsync attempt, full-tree manifests, per-target atomic swap, post-verify rollback, and backup cleanup only after verified commit.
- `.claude`, `.codex`, and `.agents` are all mandatory with identical manifests. A same-name shadow with a different hash fails closed/non-zero.
- The versioned watcher adapter records child exit and metadata-only stdout/stderr and rejects timeouts, malformed heartbeat, non-zero exit, policy/manifest mismatch, and failed targets. Root precedence is fixed as `vault, claude, codex, agents`.
- Current full GREEN: `python -B -m unittest discover -s tests -v` = **41/41**, plus one explicit Windows file-symlink privilege skip.
- A true `compileall` rerun uses the no-space QA checkout and a separate temporary pycache root; exact evidence is recorded in the external implementation handoff.
- No real Vault/runtime root sync, watcher installation/configuration/restart, plugin cache mutation, or WSL/Hermes/OpenClaw change was performed. Apply remains blocked behind a separate deployment approval.

## Current Status

- Status: Local documentation-link drift is covered by a dependency-free regression test; the P0 source remains fixture-bounded and live deployment remains approval-gated.
- Repository: `codex-multi-agent-workflow-kit`.
- Last updated: 2026-07-23.
- Baseline before this maintenance change: `9db5dd89b286aaf9933990a380f739f298a8dd70` (`docs: add FINAL_KEEP archive example`).
- Current work: Keep public documentation navigable and CI-checkable without adding runtime dependencies or network behavior.

## Recent Changes

- Added standard-library regression coverage for local Markdown links in the README, root maintainer docs, `docs/`, and `examples/`.
- Recorded local-link validation as a maintained v0.1 roadmap capability.

- Added an artifact-heavy `FINAL_KEEP` example with stable current names, dated set-level archives, rollback guidance, and a reproducible handoff note.
- Linked the example from README and included it in the documented repository tree.
- Marked the corresponding v0.3 roadmap item as maintained.

- Added the exact seven-field operation envelope, canonical cwd/delegation/deadline validation, machine-readable schemas, and shared error codes.
- Added the versioned role-to-model/thinking/fallback/capability resolver with exact Sol/Terra/Luna assignments, deterministic security/design promotion, semantic 5.9/5.10 comparison, and structured `UNAVAILABLE`.
- Added OS-temp-only skill sync and verify production CLI routes with process lock, staging, full-tree manifests, atomic swap/rollback, `.agents` support, shadow hard-fail, heartbeat output, and explicit `WSL_UNAVAILABLE` separation.
- Added RED-to-GREEN fixtures for FX-09 through FX-14 and the common contract surfaces. No live runtime root, Vault, WSL, watcher, hook, plugin cache, or user config was accessed or changed.

- Added a step-by-step existing-repository adoption guide that previews templates, uses no-overwrite initialization, and merges required headings manually.
- Linked the guide from README and marked the corresponding roadmap item as maintained.
- Added TDD regression coverage for file symlinks, directory junctions/reparse points, a linked target root, path conflicts, and invalid UTF-8 input.
- Hardened `init` so existing symlinks, junctions, and other reparse points cannot redirect writes outside the target root, including with `--force`.
- Added canonical target-root containment checks and repeated validation before writes.
- Converted expected path, filesystem, and UTF-8 exceptions into one public-safe `ERROR:` line with exit code `2`, without a default traceback.
- Added top-level `permissions: contents: read` to both GitHub Actions workflows while retaining Python 3.10-3.12 unit tests and the Python 3.12 smoke workflow.
- Updated README and SECURITY to describe only the implemented behavior and the concurrent-mutation limitation.
- Added `PROJECT_BLUEPRINT.md` with the required ten project-governance items.

## Verification

- Weekly repository growth (2026-07-23):
  - Focused documentation-link test: passed (1 test).
  - `python -B -m unittest discover -s tests -v`: passed (42 tests, 1 explicit Windows file-symlink privilege skip).
  - Fresh `init` and `check` smoke commands plus temporary-target cleanup: passed.
  - Staged `git diff --check`, exact-file scope, and public-safety scan: passed.

- Weekly repository growth (2026-07-16):
  - `python -B -m unittest discover -s tests -v`: passed (41 tests, 1 explicit Windows file-symlink privilege skip).
  - Fresh `init` and `check` smoke commands: passed in an operating-system temporary directory.
  - Temporary smoke cleanup and README example link target check: passed.
  - `git diff --check` and scoped public-safety scan: passed.

- P0 source verification (2026-07-15):
  - Baseline RED: missing contract modules and CLI routes raised `ModuleNotFoundError` or argparse invalid choice; additional RED captured 25-hour deadlines, incomplete policy outputs, missing heartbeat/verify route, overlapping targets, and directory shadow conflicts.
  - Focused GREEN: P0 CLI 7/7; skill-sync 9/9.
  - Full unittest: 36 tests completed successfully with 1 explicit Windows file-symlink privilege skip.
  - `python -m compileall -q codex_multi_agent_workflow_kit tests`: passed.
  - `git diff --check`: passed.
  - Temp apply smoke: apply mode completed, verify returned true, and the three target manifests were identical.

- Current documentation change (2026-07-13):
  - `python -m unittest discover -s tests -v`: passed (9 tests, 1 explicit Windows symlink-permission skip).
  - Fresh `init` and `check` smoke commands: passed.
  - Temporary smoke folder removal and README link target check: passed.
  - `git diff --check` and scoped public-safety scan: passed.

Use the bundled Python runtime:

```powershell
& '<bundled-python>' -m unittest discover -s tests -v
& '<bundled-python>' -m compileall -q codex_multi_agent_workflow_kit tests
& '<bundled-python>' -m codex_multi_agent_workflow_kit.cli init <temporary-target>
& '<bundled-python>' -m codex_multi_agent_workflow_kit.cli check <temporary-target>
git diff --check
git status --short --branch
```

- TDD RED: junction/reparse boundary tests failed because `--force` followed links; path conflict and invalid UTF-8 tests raised uncaught exceptions.
- Focused GREEN: 4 tests passed; 1 file-symlink test was skipped because Windows symlink creation privilege was unavailable.
- Full interim suite: 8 tests passed with 1 explicit Windows file-symlink skip.
- Final unittest: 9 tests completed with 8 passed and 1 explicit Windows file-symlink permission skip.
- Final compileall: passed for the package and tests.
- Final smoke: `init=0`, `check=0`, existing file preserved without `--force`, junction `--force` rejected, and the outside sentinel remained unchanged.
- Smoke targets were created outside the repository in the operating-system temporary area.

## Next Steps

- Add a Codex-ready issue triage template that turns maintainer reports into scoped tasks with acceptance criteria and verification commands.
- Independent QA should rerun FX-01 through FX-14 using the implementation handoff under `D:\AI PROJECT\.codex-jobs\skill-harness-p0`.
- Do not connect this source to live skill roots or automation until the owner approves a deployment plan with backup, rollback, version, and downtime evidence.

## Risks and Notes

- Do not include or stage `.env*`, logs, user data, local agent state, credentials, personal paths, account details, or email addresses.
- Existing filesystem links and reparse points are rejected. The CLI is not a sandbox against an untrusted process that mutates the target concurrently between validation and write.
- The CLI performs no network calls and has no web UI, server, external API, database, authentication, or secret configuration.
- UX review is currently not applicable. Reassess if a web, desktop, or interactive TUI surface is added.
- `FINAL_KEEP` is not created for this source repository because there is no user-facing rendered/exported artifact. Reassess if reports, images, videos, decks, or exports become project deliverables.
- wiki/Obsidian and files outside this repository are out of scope and were not modified.
- The P0 sync/verify implementation is intentionally limited to OS temporary fixtures; it is not the active Windows watcher or WSL sync implementation.
- WSL was not installed or probed. Its source-stage heartbeat state is `WSL_UNAVAILABLE`.
