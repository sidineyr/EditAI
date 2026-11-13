# EditAI validation record

## Session evidence

The repository-writing environment reported GitHub repository metadata and accepted a source update. It did not expose a local shell, filesystem, FFmpeg runtime, compiler, emulator, or physical device. No machine specifications are asserted.

## Present source paths

- Portable project create/add/validate helpers and scene asset integrity checking.
- Still-image pan/zoom MP4 and photo-montage MP4 worker paths that require external FFmpeg.
- Unit tests for project manifests, path escape rejection, content hash integrity, and input/output guards.

## Not executed in this session

- Python test suite; FFmpeg render or ffprobe inspection.
- Flutter or Android build, app launch, emulator/physical-device run.
- AI/model inference, benchmark, network-denied test, companion test, or signing.

## Commands for local verification

From repository root:

```bash
python3 -m unittest discover -s tests -v
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py capabilities
```

For a real render, use a test image and an output path that does not exist:

```bash
python3 services/local_worker/editai_worker.py photo-animation "input image.jpg" "animation.mp4" --seconds 3 --fps 24
ffprobe -v error -show_streams -show_format "animation.mp4"
```

For project/montage acceptance, use two image files and an audio file supported by the installed FFmpeg codecs:

```bash
python3 services/local_worker/editai_worker.py project create demo-project --title "Demo"
python3 services/local_worker/editai_worker.py project add-photo demo-project "photo one.jpg" --seconds 2
python3 services/local_worker/editai_worker.py project add-photo demo-project "photo two.jpg" --seconds 2
python3 services/local_worker/editai_worker.py project validate demo-project
python3 services/local_worker/editai_worker.py project render demo-project "demo.mp4" --audio "music.wav"
ffprobe -v error -show_streams -show_format "demo.mp4"
```

These are instructions, not results from this session. Successful export should be confirmed by decoding/playback and inspecting streams, duration, dimensions, and audio synchronization.

## Explicit status

No test pass, render success, benchmark number, model revision, packaged artifact, or supported-device validation is claimed. The product remains incomplete and the current source slice must be validated on the maintainer's machine before relying on it.
