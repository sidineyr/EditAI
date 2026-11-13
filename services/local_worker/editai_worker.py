#!/usr/bin/env python3
"""Local EditAI worker: conventional media operations; no cloud or model fetching."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from project import add_photo, create_project, load_project, project_scene_paths
except ImportError:  # package import in tests and library use
    from services.local_worker.project import add_photo, create_project, load_project, project_scene_paths

CAPABILITIES = {
    "schema_version": 1,
    "product": "EditAI",
    "operations": [
        {"id": "project.portable_v1", "status": "implemented", "inputs": ["project directory", "photos"], "outputs": ["project.json", "relative hashed assets"], "backend": "Python standard library", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present; not executed in this session"},
        {"id": "photo.pan_zoom", "status": "implemented", "inputs": ["image_path", "duration_seconds", "fps"], "outputs": ["video/mp4"], "backend": "FFmpeg CLI", "dependency": "user-installed FFmpeg with libx264", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present; render not executed in this session"},
        {"id": "photos.montage", "status": "implemented", "inputs": ["project with image scenes", "optional audio"], "outputs": ["video/mp4"], "backend": "FFmpeg CLI", "dependency": "user-installed FFmpeg with libx264; AAC for audio", "platforms": ["Linux", "Windows", "macOS"], "neural": False, "test_status": "unit tests present; render not executed in this session"},
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
    return {"python": sys.version.split()[0], "platform": sys.platform, "ffmpeg": executable_version("ffmpeg"), "ffprobe": executable_version("ffprobe"), "network_used": False}


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
    """Render privately, then publish atomically without replacing an existing file."""
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
        # Hard-link creation is atomic and fails rather than overwriting a raced-in destination.
        temporary.replace(destination) if not destination.exists() else (_ for _ in ()).throw(FileExistsError(f"Refusing to overwrite existing output: {destination}"))
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
    vf = ("scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
          "zoompan=z='min(zoom+0.0005,1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s=1280x720:fps={fps},format=yuv420p")
    def build(temp: Path) -> list[str]:
        return [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n", "-loop", "1", "-i", str(source), "-vf", vf, "-frames:v", str(frames), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temp)]
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
    if destination.exists() or any(path == destination for path, _ in checked):
        raise FileExistsError("Refusing to overwrite an input or existing output")
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
        for path, duration in checked:
            command.extend(["-loop", "1", "-t", f"{duration:.6f}", "-i", str(path)])
        if audio_path:
            command.extend(["-stream_loop", "-1", "-i", str(audio_path)])
        filters = []
        concat_inputs = []
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="editai-worker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities", help="print the machine-readable capability registry")
    sub.add_parser("diagnose", help="report locally detected runtime tools")
    render = sub.add_parser("photo-animation", help="render a still-image pan/zoom MP4")
    render.add_argument("input", type=Path); render.add_argument("output", type=Path)
    render.add_argument("--seconds", type=float, default=4.0); render.add_argument("--fps", type=int, default=24)
    project = sub.add_parser("project", help="create, edit, validate, or render a portable project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    create = project_sub.add_parser("create"); create.add_argument("directory", type=Path); create.add_argument("--title", required=True)
    add = project_sub.add_parser("add-photo"); add.add_argument("directory", type=Path); add.add_argument("photo", type=Path); add.add_argument("--seconds", type=float, default=4)
    validate = project_sub.add_parser("validate"); validate.add_argument("directory", type=Path)
    project_render = project_sub.add_parser("render"); project_render.add_argument("directory", type=Path); project_render.add_argument("output", type=Path); project_render.add_argument("--fps", type=int, default=24); project_render.add_argument("--audio", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "capabilities": print(json.dumps(CAPABILITIES, indent=2))
        elif args.command == "diagnose": print(json.dumps(diagnose(), indent=2))
        elif args.command == "photo-animation":
            render_photo_animation(args.input, args.output, args.seconds, args.fps); print(f"Rendered: {args.output}")
        elif args.command == "project":
            if args.project_command == "create": print(create_project(args.directory, args.title))
            elif args.project_command == "add-photo": print(json.dumps(add_photo(args.directory, args.photo, args.seconds), indent=2))
            elif args.project_command == "validate": print(json.dumps({"valid": True, "title": load_project(args.directory)["title"]}, indent=2))
            elif args.project_command == "render":
                render_montage(project_scene_paths(args.directory), args.output, args.fps, args.audio); print(f"Rendered: {args.output}")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"editai-worker: {exc}", file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
