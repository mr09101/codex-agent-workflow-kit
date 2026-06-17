# Agent Operating Guide

## Safety Rules

- Do not commit secrets, tokens, passwords, `.env` files, or private data.
- State assumptions before editing when the request is ambiguous.
- Make scoped changes and preserve user work you did not create.
- Run relevant checks before reporting completion.

## Session Roles

- Manager: routes requests and reviews final status.
- Project lead: owns implementation, tests, Git state, and handoff updates.
- Reviewer: checks safety, documentation, and release readiness.

## Review Gates

- Security: no secrets or private data.
- Behavior: requested behavior is implemented and verified.
- Documentation: public text matches the current project state.
- Git hygiene: only related files are staged.

## Handoff Discipline

Update `HANDOFF.md` after meaningful work with status, changes, checks, risks, and next steps.

## Repository Hygiene

Keep temporary files, generated caches, and unrelated artifacts out of Git.
