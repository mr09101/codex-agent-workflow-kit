# Role Selection Guide

Use this guide when a maintainer needs to decide which Codex workflow role should handle a task.

These are Markdown operating roles, not a runtime orchestration system. One human or one Codex session can fill more than one role, but naming the active role keeps scope, review, and handoff expectations clear.

## Quick Decision Table

| Situation | Use This Role | Why |
| --- | --- | --- |
| A request needs triage, scope, or routing before edits | Manager | The work is not ready for implementation until the outcome, constraints, and verification target are clear. |
| A small code, docs, test, or template change is ready to make | Project lead | The task has enough shape for one session to inspect, edit, verify, update `HANDOFF.md`, and prepare a commit. |
| A change is ready but needs safety, scope, docs, or release review | Reviewer | A separate pass should inspect the diff and evidence before merge or release. |
| The work has two or more independent research or implementation tracks | Subagent | Parallel help can reduce waiting time when each track has a bounded question and clear return artifact. |
| A maintainer must decide whether to merge, release, or defer | Maintainer | Final project direction and risk acceptance stay with the human maintainer. |

## Manager

Use a manager pass when the request is ambiguous, cross-repository, risky, or likely to produce unrelated edits without a clear scope.

A good manager note includes:

- Expected outcome.
- Files likely in scope.
- Files explicitly out of scope.
- Verification command or review gate.
- Any public-safety constraints.

Do not keep a task in manager mode once the next concrete edit is clear. Hand it to a project lead.

## Project Lead

Use a project lead pass for bounded implementation work.

The project lead should:

- Inspect the relevant files before editing.
- Make the smallest safe change that satisfies the request.
- Run focused tests or smoke checks.
- Update `HANDOFF.md` with status, checks, risks, and next steps.
- Stage only related files when a commit is appropriate.

If the work expands into multiple unrelated changes, stop and return to manager mode.

## Reviewer

Use a reviewer pass after implementation and before merge, release, or public announcement.

The reviewer should inspect:

- Scope: the diff matches the task.
- Safety: no secrets, private paths, credentials, caches, or scratch output.
- Behavior: tests or documented checks support the claimed result.
- Documentation: public text describes what the kit actually does.
- Handoff: a future maintainer can continue without chat history.

For agent-authored pull requests, use `docs/agent-pr-review-checklist.md`.

## Subagent

Use a subagent only when the work can be split into independent tracks with clear boundaries.

Good subagent tasks:

- Compare two documentation approaches.
- Inspect one directory or feature area.
- Reproduce one failing check.
- Draft a narrow example while the project lead handles tests.

Avoid subagents for vague ownership such as "improve the project" or for tasks that require one consistent edit across many files.

## Maintainer

The maintainer owns the final decision. The workflow roles can prepare evidence, but they should not hide product, security, or release risk behind agent summaries.

Before accepting agent-assisted work, the maintainer should be able to answer:

- What changed?
- Why was this role used?
- What verification ran?
- What risk remains?
- What should happen next?
