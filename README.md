# EditAI

**Create freely. Keep your files. Use your own machine.**

EditAI is an incomplete local-first creative studio project. This repository now contains a small Python worker slice for portable photo projects and conventional FFmpeg-based exports; it is not the full cross-platform application in the specification.

## Available worker workflows

Requirements: Python 3.10+ and a user-installed FFmpeg executable with the required codecs (`libx264`; AAC for montage audio). No Python packages are needed for these CLI workflows.

```bash
python3 services/local_worker/editai_worker.py diagnose
python3 services/local_worker/editai_worker.py capabilities
python3 services/local_worker/editai_worker.py photo-animation "input image.jpg" "output.mp4" --seconds 4 --fps 24
python3 services/local_worker/editai_worker.py project create "My Project" --title "A short story"
python3 services/local_worker/editai_worker.py project add-photo "My Project" "photo one.jpg" --seconds 3
python3 services/local_worker/editai_worker.py project add-photo "My Project" "photo two.jpg" --seconds 3
python3 services/local_worker/editai_worker.py project validate "My Project"
python3 services/local_worker/editai_worker.py project render "My Project" "montage.mp4" --fps 24 --audio "music.wav"
```

Projects use a versioned JSON manifest, relative asset paths, and SHA-256 checks on load. Added photos are copied into the project; source photos are not modified. MP4 output is conventional non-neural animation or a hard-cut photo montage, not generated video. Output files are not intentionally overwritten.

Run unit tests:

```bash
python3 -m unittest discover -s tests -v
```

## Current limitations

There is no Flutter UI, Android app, project timeline editor, sketch renderer, video trim/color workflow, subtitles, AI model manager/inference, companion mode, installer, or release artifact. Tests and actual FFmpeg renders have not been executed in this editing environment; `VALIDATION.md` records that limitation. FFmpeg installation, codecs, and licensing vary by distribution and are not bundled or certified here.

The worker contains no cloud endpoint, model download, or telemetry code. This is not an OS-level network sandbox and cannot control unrelated processes. Local rendering still consumes hardware, energy, storage, and time. Media/output rights depend on source material, component terms, and applicable law.
