# EditAI implementation status

**Overall: early implementation, not a release.**

## Implemented in source

- Portable project and asset integrity helpers.
- Project archive import/export with protections against path traversal and oversized payloads.
- Local storyboard metadata and prompt editing.
- Loopback-only local web UI for creating and populating projects.
- Benchmark CLI that records measured local execution data in JSON.
- Contribution, security, and agent policy files.

## Not implemented

- Full Flutter application.
- Native Android editing/export.
- Real drawing canvas and timeline editor.
- Generative AI adapters with license verification and real inference tests.
- Companion mode and production packaging.

## Evidence distinctions

| Capability | Source implementation | External dependency | Validated here |
| --- | --- | --- | --- |
| Portable project metadata | Yes | Python stdlib | Partial source-only status |
| Archive safety checks | Yes | Python stdlib | Source-only |
| Storyboard metadata | Yes | Python stdlib | Source-only |
| Local web UI | Yes | Python stdlib | Source-only |
| Benchmark runner | Yes | Python stdlib | Source-only |
| Android or Flutter build | No | None | Not executed |
| Neural inference | No | None | Not executed |

## Next priorities

1. Add a more complete locally runnable project editor and gallery workflow.
2. Add true FFmpeg-based validation with synthetic media probes and playback checks.
3. Add a real desktop application shell or web editor interface with persisted actions.
4. Add audited local model adapters only with genuine hardware validation.
