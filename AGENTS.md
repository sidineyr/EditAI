# AGENTS.md

## Project orientation

This repository is an early-stage, local-first creative studio. The goal is to keep the implementation honest, offline-capable, and transparent about what is implemented versus what remains planned.

## Ground rules

- Do not claim a feature is complete or validated without evidence.
- Prefer local, conventional, and transparent workflows over cloud-dependent shortcuts.
- Treat user media as untrusted input and preserve originals.
- Keep optional AI paths separate from the conventional workflow.
- Separate source implementation from runtime and model downloads.

## Required behavior for changes

- Keep modifications small and readable.
- Add or update tests for the behavior being changed.
- Document any external dependency, model, or platform limitation.
- Mark obviously incomplete features as planned or unverified rather than silently presenting them as working.

## Invalid patterns

- fake renders or mock-only success claims
- hidden analytics or cloud fallback in the default path
- automatic downloads without explicit user approval
- broad network listening or LAN exposure without opt-in consent
