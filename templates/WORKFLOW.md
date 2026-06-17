# Workflow

## Roles

- Manager: accepts requests and validates final reports.
- Project lead: edits files, runs tests, and updates handoffs.
- Reviewer: checks public quality and risk before release.

## Standard Loop

1. Intake the request and constraints.
2. Inspect relevant files.
3. Make the smallest safe change.
4. Verify with focused commands.
5. Update the handoff.
6. Commit only related files when appropriate.

## Review Gates

- Scope gate.
- Safety gate.
- Test gate.
- Documentation gate.
- Release gate.

## Verification

Record exact commands and outcomes so another agent can reproduce them.

## Release Checklist

- Required files exist.
- Tests pass or skipped checks are explained.
- Public docs contain no private paths, accounts, or secrets.
