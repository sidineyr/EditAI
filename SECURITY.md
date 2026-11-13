# Security policy

## Reporting a vulnerability

Please do not disclose vulnerabilities in public issues or pull requests. Keep private reports limited to the maintainer and project owners until a fix is ready.

If the repository is under active maintenance, send the report to the repository owner privately and include:

- the affected file or component
- a description of the issue and exploit path
- the estimated impact
- the exact version or commit SHA involved
- any reproduction steps or proof of concept, sanitized to avoid private data

## Security posture

This project is intentionally local-first and does not depend on a remote service in the default path. However:

- local workers are not a complete sandbox for unrelated OS processes
- network exposure must remain opt-in and explicit
- archive import and project validation must reject traversal, symlinks, and malformed content
- user media and originals must never be overwritten without explicit action

## Patch expectations

Prefer small, reviewed changes that reduce risk without broadening attack surface. Do not substitute a mock or partial validation for a real test.
