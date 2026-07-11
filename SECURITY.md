# Security Policy

## Supported Versions

This project is pre-1.0. Security fixes target the latest version on the default branch.

## Reporting a Vulnerability

Use the repository's private vulnerability reporting feature if available. If not available, open a minimal issue that describes the affected behavior without posting secrets, exploit payloads, or private data.

## Security Expectations

- The CLI does not call external services.
- The CLI does not read or generate secrets.
- The CLI does not create `.env` files.
- No API keys, tokens, accounts, or external service configuration are required; `.env.example` is intentionally omitted.
- Existing files are not overwritten unless `--force` is provided.
- `init` rejects a symlink, junction, or other reparse point at the target root or in a generated path. `--force` does not bypass this boundary.
- Generated destinations are resolved and checked against the target root before writes.
- Expected filesystem and UTF-8 failures produce one public-safe error line and a nonzero exit code without a default traceback.
- Templates must remain public-safe.

Do not run `init` in a directory that an untrusted process can mutate concurrently.
The CLI validates existing filesystem objects before writes, but it is not a sandbox
for a hostile process racing those checks.
