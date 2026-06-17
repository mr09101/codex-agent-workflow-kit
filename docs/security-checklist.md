# Security Checklist

Use this checklist before merging or releasing agent-assisted changes.

## CLI Safety

- The CLI makes no network calls.
- The CLI does not create `.env` files.
- The CLI does not generate secrets, credentials, tokens, keys, or passwords.
- Existing files are not overwritten unless the maintainer explicitly passes `--force`.
- `check` returns a non-zero exit code when required files or sections are missing.

## Repository Hygiene

- No unrelated files are edited.
- Generated caches are not staged.
- Temporary smoke-test folders are removed.
- Final user-facing artifacts are separated from scratch work.
- `HANDOFF.md` records current status, checks, risks, and next steps.

## Review Gates

- Scope gate: the change matches the issue or maintainer request.
- Safety gate: no private paths, account names, credentials, or production data are included.
- Test gate: relevant tests or smoke checks ran.
- Documentation gate: README and docs match current behavior.
- Release gate: known risks are recorded before tagging or publishing.

## Public-Safety Scan

For this repository, a conservative local scan can start with:

```bash
rg -n "[A-Z]:\\\\|@|sk-[A-Za-z0-9]|AIza|BEGIN .*PRIVATE|PASSWORD\\s*=|SECRET\\s*=|TOKEN\\s*=|KEY\\s*="
```

Review matches manually. Mentions of `token`, `.env`, or `key` in security documentation can be legitimate when they are examples or warnings rather than values.
