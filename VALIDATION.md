# EditAI validation record

## Session evidence

The repository update tool can read and write GitHub files but provides no local shell, filesystem, FFmpeg runtime, compiler, emulator, or physical device. No machine specifications are asserted.

## Present source paths

- Portable project create/add/validate helpers, per-scene duration and approval controls, and integrity checking.
- Portable ZIP export/import with selected-scene export, strict member path allowlist, traversal/symlink rejection, member and expansion limits, and validation before import.
- Still-image pan/zoom and photo montage with optional audio via external FFmpeg.
- Unit tests for project manifests, path escape rejection, content hash integrity, bundle roundtrip, and existing-output protection.

## Not executed in this session

- Python tests, FFmpeg rendering, or ffprobe/playback inspection.
- Flutter or Android build, app launch, emulator/physical-device run.
- AI/model inference, benchmark, OS-level network-denied test, companion test, or signing.

## Local verification commands

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py capabilities
```

For an actual render, provide a test image and a new output path:

```bash
python3 services/local_worker/editai_worker.py photo-animation "input image.jpg" "animation.mp4" --seconds 3 --fps 24
ffprobe -v error -show_streams -show_format "animation.mp4"
```

For project bundle roundtrip:

```bash
python3 services/local_worker/editai_worker.py project create demo-project --title Demo
python3 services/local_worker/editai_worker.py project add-photo demo-project "photo one.jpg" --seconds 2
python3 services/local_worker/project_bundle.py export demo-project demo.zip
python3 services/local_worker/project_bundle.py import demo.zip restored-project
python3 services/local_worker/editai_worker.py project validate restored-project
```

These are instructions, not results from this session. A successful export still needs playback/decode checks and inspection of streams, duration, dimensions, and audio synchronization.

## Explicit status

No test pass, render success, benchmark number, model revision, packaged artifact, or supported-device validation is claimed. Product status remains incomplete; the source changes must be run and validated on a maintainer machine before relying on them.
