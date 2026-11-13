#!/usr/bin/env python3
"""Local EditAI worker: conventional project creation, montage export, and offline storyboard tooling."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from services.local_worker.project import (
        add_photo,
        create_project,
        export_project_archive,
        import_project_archive,
        load_project,
        project_scene_paths,
        set_scene_approval,
        set_scene_duration,
    )
except ImportError:  # pragma: no cover - module execution contexts
    from project import (
        add_photo,
        create_project,
        export_project_archive,
        import_project_archive,
        load_project,
        project_scene_paths,
        set_scene_approval,
        set_scene_duration,
    )

CAPABILITIES = {
    "schema_version": 1,
    "product": "EditAI",
    "operations": [
        {"id": "project.portable_v1", "status": "implemented", "inputs": ["project directory", "photos"], "outputs": ["project.json", "relative hashed assets"], "backend": "Python stdlib", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present"},
        {"id": "project.bundle", "status": "implemented", "inputs": ["project directory", "selected scenes"], "outputs": ["archive.zip"], "backend": "Python zipfile", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present"},
        {"id": "photo.pan_zoom", "status": "implemented", "inputs": ["image_path", "duration_seconds", "fps"], "outputs": ["video/mp4"], "backend": "FFmpeg CLI", "dependency": "user-installed FFmpeg with libx264", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present"},
        {"id": "photos.montage", "status": "implemented", "inputs": ["project with image scenes", "optional audio"], "outputs": ["video/mp4"], "backend": "FFmpeg CLI", "dependency": "user-installed FFmpeg with libx264; AAC for audio", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present"},
        {"id": "storyboard.editor", "status": "implemented", "inputs": ["project directory", "scene prompt"], "outputs": ["storyboard.json"], "backend": "Python stdlib", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present"},
        {"id": "local.web_ui", "status": "implemented", "inputs": ["project workspace", "user file paths"], "outputs": ["HTML API"], "backend": "Python http.server", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "source present; browser not executed in this session"},
    ],
}


def executable_version(name: str) -> str | None:
    executable = shutil.which(name)
    if executable is None:
        return None
    result = subprocess.run([executable, "-version"], check=False, capture_output=True, text=True, timeout=5)
    lines = (result.stdout or result.stderr).splitlines()
    return lines[0] if lines else f"{name} found; version unavailable"


def diagnose() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "ffmpeg": executable_version("ffmpeg"),
        "ffprobe": executable_version("ffprobe"),
        "network_used": False,
    }


def _validate_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    source = source.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    if not source.is_file():
        raise ValueError("Input must be a regular file")
    if source == destination:
        raise ValueError("Input and output paths must differ")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
    return source, destination


def _render_transaction(destination: Path, command_builder) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".editai-render-", suffix=destination.suffix or ".mp4", dir=destination.parent)
    import os
    os.close(fd)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        command = command_builder(temporary)
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {result.stderr.strip()}")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError("FFmpeg returned success but produced no output file")
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def render_photo_animation(source: Path, destination: Path, seconds: float, fps: int) -> None:
    source, destination = _validate_paths(source, destination)
    if not 0.1 <= seconds <= 120:
        raise ValueError("seconds must be between 0.1 and 120")
    if not 1 <= fps <= 60:
        raise ValueError("fps must be between 1 and 60")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg was not found on PATH; install it explicitly to render")
    frames = max(1, round(seconds * fps))
    vf = (
        "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0005,1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s=1280x720:fps={fps},format=yuv420p"
    )

    def build(temp: Path) -> list[str]:
        return [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-n",
            "-loop",
            "1",
            "-i",
            str(source),
            "-vf",
            vf,
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temp),
        ]

    _render_transaction(destination, build)


def render_montage(scenes: list[tuple[Path, float]], destination: Path, fps: int = 24, audio: Path | None = None) -> None:
    if not scenes or len(scenes) > 100:
        raise ValueError("Montage needs between 1 and 100 image scenes")
    if not 1 <= fps <= 60:
        raise ValueError("fps must be between 1 and 60")
    checked: list[tuple[Path, float]] = []
    for path, duration in scenes:
        path = path.expanduser().resolve(strict=True)
        if not path.is_file() or not 0.1 <= duration <= 120:
            raise ValueError("Each montage scene needs a regular image and 0.1-120 second duration")
        checked.append((path, duration))
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
    audio_path = None
    if audio is not None:
        audio_path = audio.expanduser().resolve(strict=True)
        if not audio_path.is_file() or audio_path == destination:
            raise ValueError("Audio must be a regular file distinct from output")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg was not found on PATH; install it explicitly to render")
    total = sum(duration for _, duration in checked)

    def build(temp: Path) -> list[str]:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
        for index, (path, duration) in enumerate(checked):
            command.extend(["-loop", "1", "-t", f"{duration:.6f}", "-i", str(path)])
        if audio_path:
            command.extend(["-stream_loop", "-1", "-i", str(audio_path)])
        filters: list[str] = []
        concat_inputs: list[str] = []
        for index, (_, duration) in enumerate(checked):
            filters.append(f"[{index}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps={fps},trim=duration={duration:.6f},setpts=PTS-STARTPTS,format=yuv420p[v{index}]")
            concat_inputs.append(f"[v{index}]")
        filters.append("".join(concat_inputs) + f"concat=n={len(checked)}:v=1:a=0[vout]")
        command.extend(["-filter_complex", ";".join(filters), "-map", "[vout]"])
        if audio_path:
            command.extend(["-map", f"{len(checked)}:a:0", "-c:a", "aac", "-b:a", "192k"])
        else:
            command.append("-an")
        command.extend(["-t", f"{total:.6f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temp)])
        return command

    _render_transaction(destination, build)


def render_project_montage(project_dir: Path, destination: Path, fps: int = 24, audio: Path | None = None) -> None:
    project_dir = project_dir.expanduser().resolve(strict=True)
    render_montage(project_scene_paths(project_dir), destination, fps=fps, audio=audio)


def _storyboard_payload(project_dir: Path) -> dict[str, object]:
    data = load_project(project_dir)
    assets = {asset["id"]: asset for asset in data["assets"]}
    story = []
    for index, scene in enumerate(data["scenes"], start=1):
        asset = assets[scene["asset_id"]]
        story.append({
            "index": index,
            "scene_id": scene["id"],
            "asset_id": asset["id"],
            "asset_path": asset["path"],
            "duration_seconds": float(scene["duration_seconds"]),
            "approved": bool(scene.get("approved", False)),
            "prompt": str(scene.get("prompt", "")),
        })
    return {"project_title": data["title"], "scenes": story}


def save_storyboard(project_dir: Path, output: Path | None = None) -> Path:
    project_dir = project_dir.expanduser().resolve(strict=True)
    payload = _storyboard_payload(project_dir)
    destination = output.expanduser().resolve() if output else project_dir / "storyboard.json"
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing storyboard: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def set_scene_prompt(project_dir: Path, scene_id: str, prompt: str) -> None:
    project_dir = project_dir.expanduser().resolve(strict=True)
    data = load_project(project_dir)
    scene = next((item for item in data["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene: {scene_id}")
    scene["prompt"] = prompt
    with tempfile.NamedTemporaryFile("w", dir=project_dir, delete=False, encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temp_path = Path(handle.name)
    temp_path.replace(project_dir / "project.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="editai-worker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities", help="print the machine-readable capability registry")
    sub.add_parser("diagnose", help="report locally detected runtime tools")

    render = sub.add_parser("photo-animation", help="render a still-image pan/zoom MP4")
    render.add_argument("input", type=Path)
    render.add_argument("output", type=Path)
    render.add_argument("--seconds", type=float, default=4.0)
    render.add_argument("--fps", type=int, default=24)

    montage = sub.add_parser("mountain", help="render a slideshow from a project (compat alias)")
    montage.add_argument("project", type=Path)
    montage.add_argument("output", type=Path)
    montage.add_argument("--fps", type=int, default=24)
    montage.add_argument("--audio", type=Path)

    project = sub.add_parser("project", help="project and bundle manager")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    create = project_sub.add_parser("create")
    create.add_argument("directory", type=Path)
    create.add_argument("--title", required=True)
    add = project_sub.add_parser("add-photo")
    add.add_argument("directory", type=Path)
    add.add_argument("photo", type=Path)
    add.add_argument("--seconds", type=float, default=4)
    validate = project_sub.add_parser("validate")
    validate.add_argument("directory", type=Path)
    render_project = project_sub.add_parser("render")
    render_project.add_argument("directory", type=Path)
    render_project.add_argument("output", type=Path)
    render_project.add_argument("--fps", type=int, default=24)
    render_project.add_argument("--audio", type=Path)

    bundle = project_sub.add_parser("bundle")
    bundle.add_argument("directory", type=Path)
    bundle.add_argument("archive", type=Path)
    bundle.add_argument("--scene", action="append", dest="scene_ids")

    import_bundle = project_sub.add_parser("import")
    import_bundle.add_argument("archive", type=Path)
    import_bundle.add_argument("destination", type=Path)

    storyboard = sub.add_parser("storyboard", help="generate a storyboard summary from a project")
    storyboard.add_argument("project", type=Path)
    storyboard.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "capabilities":
            print(json.dumps(CAPABILITIES, indent=2))
        elif args.command == "diagnose":
            print(json.dumps(diagnose(), indent=2))
        elif args.command == "photo-animation":
            render_photo_animation(args.input, args.output, args.seconds, args.fps)
            print(f"Rendered: {args.output}")
        elif args.command == "mountain":
            render_project_montage(args.project, args.output, fps=args.fps, audio=args.audio)
            print(f"Rendered: {args.output}")
        elif args.command == "project":
            if args.project_command == "create":
                print(create_project(args.directory, args.title))
            elif args.project_command == "add-photo":
                print(json.dumps(add_photo(args.directory, args.photo, args.seconds), indent=2))
            elif args.project_command == "validate":
                print(json.dumps({"valid": True, "title": load_project(args.directory)["title"]}, indent=2))
            elif args.project_command == "render":
                render_project_montage(args.directory, args.output, fps=args.fps, audio=args.audio)
                print(f"Rendered: {args.output}")
            elif args.project_command == "bundle":
                archive = export_project_archive(args.directory, args.archive, set(args.scene_ids) if args.scene_ids else None)
                print(f"Archived: {archive}")
            elif args.project_command == "import":
                result = import_project_archive(args.archive, args.destination)
                print(f"Imported: {result}")
        elif args.command == "storyboard":
            storyboard_path = save_storyboard(args.project, args.output)
            print(json.dumps(_storyboard_payload(args.project), indent=2))
            print(f"Storyboard: {storyboard_path}")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"editai-worker: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# NOTE: This local worker intentionally keeps all operations conventional and local-only.
# It does not bundle cloud model access, hidden telemetry, or paid account gates.
