# Security Policy

## Supported Versions

This project is pre-1.0. Security fixes target the latest version on the default branch.

## Reporting a Vulnerability

Use the repository's private vulnerability reporting feature if available. If not available, open a minimal issue that describes the affected behavior without posting secrets, exploit payloads, or private data.

## Security Expectations

- The CLI does not call external services.
- The CLI does not read or generate secrets.
- The CLI does not create `.env` files.
- Existing files are not overwritten unless `--force` is provided.
- Templates must remain public-safe.
