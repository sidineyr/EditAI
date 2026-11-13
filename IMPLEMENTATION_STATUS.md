# EditAI validation record

## Current status

This repository contains a small but real local-first slice for project portability, scene metadata, storyboard summary, timeline modeling, and local worker validation. The implementation remains incomplete and not a validated product release.

## What is implemented

- Portable project manifest with asset integrity hashes and scene metadata.
- Safe archive import/export with traversal protections and bounded payloads.
- Storyboard metadata generation and scene prompt editing.
- Timeline model for project scenes with start/end offsets and validation.
- FFmpeg validation helper that can render a synthetic file and inspect stream metadata when FFmpeg/ffprobe are installed.
- Loopback-only default web UI for local project creation and photo ingestion.
- Benchmark CLI for local operations.

## What remains unimplemented or not validated here

- Flutter UI and Android app.
- Native Media3 Android export.
- Drawing canvas and full timeline editor UI.
- Real neural image/video generation or conditioning adapters.
- Physical-device validation, emulator execution, and full render benchmarks in this environment.

## Local verification commands

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py capabilities
python3 services/local_worker/benchmark.py --kind project --runs 1
python3 services/local_worker/ffmpeg_validate.py --output-dir benchmarks/ffmpeg_validation
```

## Explicit status

No claim is made that the application is complete, installed, or release-ready. These files define a working local slice and honest next steps, not a complete product.
