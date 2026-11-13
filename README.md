# EditAI

**Create freely. Keep your files. Use your own machine.**

EditAI is an incomplete local-first creative studio project. The current usable slice is a Python command-line worker for portable photo projects and conventional FFmpeg-based exports; it is not the complete cross-platform product or an AI application.

## Available workflows

Requirements for these commands: Python 3.10+ and a user-installed FFmpeg executable with compatible codecs (`libx264`; AAC for montage audio). The project/package commands use only the Python standard library.

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

Projects use a versioned JSON manifest, relative paths, copied photo assets, and SHA-256 validation. Add or edit scene timing/approval and exchange self-contained project archives with the companion helper:

```bash
python3 services/local_worker/project_bundle.py duration "My Project" scene-1 5
python3 services/local_worker/project_bundle.py approve "My Project" scene-1 --yes
python3 services/local_worker/project_bundle.py export "My Project" "my-project.zip"
python3 services/local_worker/project_bundle.py import "my-project.zip" "Restored Project"
```

`export` includes every scene and asset by default. Repeat `--scene scene-id` to export a selected set of scenes. Import validates archive paths, member count, sizes, project schema, and content hashes before creating a new destination directory. It refuses to overwrite an existing archive or project. Weights and external model files are never bundled.

Run unit tests:

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

There is no Flutter UI, Android app, project timeline editor, drawing surface, sketch renderer, general video-edit tools, subtitle workflow, model manager, AI inference, companion connection, installer, or release artifact. Tests and real FFmpeg renders have not been executed in this editing environment; see `VALIDATION.md`. FFmpeg and codec licensing/availability depend on the user's distribution and are not certified here.

The worker contains no cloud endpoint, model download, or telemetry code. This is not an OS-level network sandbox and cannot control unrelated processes. Local rendering consumes hardware resources, energy, storage, and time. Output rights depend on source material, component terms, and applicable law.
