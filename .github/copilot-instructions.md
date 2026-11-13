# GitHub Copilot instructions

This repository is a local-first creative studio and must remain transparent about current implementation status.

## Non-negotiable rules

- Keep the project local-first, offline-friendly, and capable of running without paid accounts or cloud GPUs.
- Do not present planned capabilities as claimed features.
- Use source verification and local tests before stating a workflow works.
- Keep model and runtime separation explicit.
- Prefer conventional, deterministic local tools over opaque or cloud-only features.

## Code expectations

- Write explicit validation checks for file paths, archive contents, project schemas, and overwrites.
- Prefer structured subprocess invocation over shell interpolation.
- Keep new dependencies minimal and justified.
- Add tests for new safety checks and project helpers.

## Documentation expectations

- Update `IMPLEMENTATION_STATUS.md` and `VALIDATION.md` when the status changes.
- Keep `README.md` aligned with actual capabilities and limitations.
- Explain any skip or blocker plainly.

## Safety

- Deny unsafe archive or file traversal patterns.
- Do not create default network listeners or wide-open LAN services.
- Do not assume user consent for model download, heavy render, or external access.
