# EditAI

**Create freely. Keep your files. Use your own machine.**

EditAI is intended to be a local-first creative studio for images, animation, audio-assisted storytelling, and video. The repository currently contains an early desktop-worker vertical slice, not the complete product described in the implementation specification.

## Current implementation

- A Python standard-library worker exposes a capability registry and diagnostics command.
- If FFmpeg is installed, the worker can create a basic pan/zoom animation from one still image as a real MP4 render. This is conventional keyframed motion, not neural image-to-video.
- Render calls use structured subprocess arguments, do not overwrite existing output files, and do not fetch models or access a cloud service.
- A small unit test suite covers worker capability and validation behavior.

This initial slice is not yet a Flutter studio, Android application, packaged desktop app, or validated release. AI inference, sketch/montage workflows, project save/reopen, the Android native renderer, companion mode, and the rest of the specification remain unimplemented.

## Run the worker

Requirements: Python 3.10+ and FFmpeg on `PATH` for rendering. No Python packages are required. No dependency installation is performed by these commands.

```bash
python3 services/local_worker/editai_worker.py capabilities
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py photo-animation input.jpg output.mp4 --seconds 4 --fps 24
```

The render command fails clearly when FFmpeg is unavailable, the input is invalid, or the output already exists. It never replaces the source image. Check the resulting file with a media player or `ffprobe`.

Run unit tests:

```bash
python3 -m unittest discover -s tests -v
```

## Privacy and limitations

The worker does not upload media, download models, or provide telemetry. FFmpeg is a separately installed executable, so its build and codec licensing are outside this repository's control. This code has not been run or tested in a target operating system from this session; see `VALIDATION.md`. Offline behavior is designed by avoiding network operations in this worker, but no OS-level egress sandbox has yet been implemented or tested.

Local rendering still consumes hardware resources, energy, storage, and time. Output rights depend on source material, dependencies, and applicable law.

## Roadmap and status

See `IMPLEMENTATION_STATUS.md`, `VALIDATION.md`, and `docs/CRITICAL_REVIEW.md`. Claims are limited to code present in this repository; planned items are not represented as working features.
