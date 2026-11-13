# EditAI validation record

## Current status

This repository contains a small but real local-first slice for project portability, scene metadata, storyboard summary, and a local web UI that binds to loopback by default. The implementation remains incomplete and not a validated product release.

## What is implemented

- Portable project manifest with copy-on-import asset handling, integrity hashes, and scene metadata.
- Scene duration and approval editing.
- Project archive export/import with traversal and size protections.
- Local storyboard metadata generation.
- Local web UI with loopback-only default binding and explicit opt-in for LAN exposure.
- Benchmark CLI that measures representative local operations and writes JSON output.
- Contribution, security, and agent policy documents.

## What remains unimplemented or not validated here

- Flutter UI and Android app.
- Native Media3 Android export.
- Drawing canvas, timeline editing, and timeline transitions.
- Real neural image/video generation or conditioning adapters.
- Physical-device validation, emulator execution, and actual benchmark runs in this environment.

## Local verification commands

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py capabilities
python3 services/local_worker/benchmark.py --kind project --runs 1
```

## Explicit status

No claim is made that the application is complete, installed, or release-ready. These files define a working local slice and honest next steps, not a complete product.
