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
- Harness envelopes accept exactly seven metadata fields and reject prompt/result content.
- Role resolution uses an explicit versioned policy, capability catalog, and allowlisted fallbacks; unavailable models or tools return structured `UNAVAILABLE`.
- P0 skill sync and verify commands are restricted to operating-system temporary fixtures and require `.claude`, `.codex`, and `.agents` targets. They reject links/reparse points, overlapping targets, lock contention, and divergent name or directory shadows.
- Full-tree manifests cover every relative path, byte size, and SHA-256. Apply mode stages and verifies before atomic replacement and restores the original fixture targets after injected failure.
- These source-stage commands do not modify the live Vault, runtime skill roots, WSL, plugin cache, hooks, watchers, startup entries, or user configuration.

Do not run `init` in a directory that an untrusted process can mutate concurrently.
The CLI validates existing filesystem objects before writes, but it is not a sandbox
for a hostile process racing those checks.

Do not treat successful fixture QA as authorization to deploy. Live sync or plugin activation requires a separate backup, rollback, ownership, and downtime gate.
