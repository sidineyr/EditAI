# EditAI implementation status

**Overall: incomplete early implementation; not a complete product or validated release.**

## Implemented in source

- Python worker diagnostics and machine-readable capability listing.
- Portable project manifest v1, copied photos, relative paths, content hashes, and scene validation.
- Conventional one-photo pan/zoom MP4 and photo montage with optional audio using external FFmpeg.
- Scene duration/approval editing and portable ZIP export/import, including selected-scene export, path traversal checks, size/member limits, and hash validation.
- Unit tests are present but were not executed in this session.

## Not implemented

Flutter application/interface, Android native Media3 integration, drawing canvas and animated strokes, full timeline/video editor, subtitle and color tools, neural image/conditioning/segmentation/transcription/video adapters, agent, model manager, protected companion mode, installers, SBOM, and cross-platform packages.

## Capability evidence distinctions

| Capability | Source implementation | External dependency | Hardware compatibility | Validated here |
| --- | --- | --- | --- | --- |
| Portable project and ZIP exchange | Yes | Python standard library | Not applicable | No; tests not run |
| Still-photo pan/zoom | Yes | FFmpeg and compatible H.264 encoder | Not assessed | No render run |
| Photo montage with optional audio | Yes | FFmpeg, H.264 and AAC support | Not assessed | No render run |
| AI generation/conditioning | No | None | Not assessed | No |
| Android app/export | No | None | Not assessed | No |

“Implemented” means a source path exists; it does not mean installed or validated on this device. Read `VALIDATION.md` for exact status.
