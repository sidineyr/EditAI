# EditAI

## Contributor guide

This repository is a local-first creative studio project in an early implementation stage. Contributions are welcome when they improve reproducibility, portability, privacy, safety, or honest capability tracking.

### Scope

We prefer contributions that are:

- small and testable
- local-first and offline-capable
- clear about limitations and missing validations
- aligned with the repository's architecture and licensing goals

### Before submitting

1. Review the repository status and keep changes small and understandable.
2. Do not promise inference or hardware performance that was not actually tested.
3. Explain any skipped tests, missing models, or unsupported devices.
4. Prefer deterministic local fixtures and unit tests over fake or mocked end-to-end claims.

### Commit expectations

- Keep tool calls typed and explicit.
- Avoid cloud fallback or paid services in the default path.
- Default to Python standard-library tools unless a dependency is clearly justified.
- Preserve original files; do not overwrite user media or project assets silently.

### Reporting issues

Use a concise summary, real reproduction steps, environment details, and evidence collected locally. If a bug involves model licensing, media parsing, or security boundaries, include the exact risk and affected files.

### Legal and licenses

Do not submit code, weights, model files, or media assets without review of their licenses and provenance. Do not include private tokens or signing keys. New project-owned code should remain compatible with the repository's GPL-3.0-or-later licensing direction unless the repository owner explicitly requests otherwise.
