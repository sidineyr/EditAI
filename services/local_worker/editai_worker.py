#!/usr/bin/env python3
"""Small, local EditAI worker slice for conventional still-image animation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CAPABILITIES = {
    "schema_version": 1,
    "product": "EditAI",
    "operations": [
        {
            "id": "photo.pan_zoom",
            "status": "implemented",
            "inputs": ["image_path", "duration_seconds", "fps"],
            "outputs": ["video/mp4"],
            "backend": "FFmpeg CLI",
            "dependency": "ffmpeg executable (user-installed)",
            "platforms": ["Linux", "Windows", "macOS"],
            "neural": False,
            "license_audit": "FFmpeg distribution and codec terms depend on the user's build; not audited here.",
            "test_status": "unit tests present; render not executed in this session",
        }
    ],
}


def executable_version(name: str) -> str | None:
    """Return the first version line for a tool, or None if unavailable."""
    executable = shutil.which(name)
    if executable is None:
        return None
    result = subprocess.run(
        [executable, "-version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    first_line = (result.stdout or result.stderr).splitlines()
    return first_line[0] if first_line else f"{name} found; version unavailable"


def diagnose() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "ffmpeg": executable_version("ffmpeg"),
        "ffprobe": executable_version("ffprobe"),
        "network_used": False,
    }


def render_photo_animation(
    source: Path, destination: Path, seconds: float, fps: int
) -> None:
    source = source.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    if not source.is_file():
        raise ValueError("Input must be a regular image file")
    if source == destination:
        raise ValueError("Input and output paths must differ")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {destination}")
    if not 0.1 <= seconds <= 120:
        raise ValueError("seconds must be between 0.1 and 120")
    if not 1 <= fps <= 60:
        raise ValueError("fps must be between 1 and 60")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("FFmpeg was not found on PATH; install it explicitly to render")

    destination.parent.mkdir(parents=True, exist_ok=True)
    frames = max(1, round(seconds * fps))
    # Scale to a bounded 1280x720 canvas, then use a gentle zoompan motion.
    # The input path is a distinct subprocess argument, never shell-interpolated.
    vf = (
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
        "zoompan=z='min(zoom+0.0005,1.08)':d=1:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s=1280x720:fps={fps},format=yuv420p"
    )
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
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
        str(destination),
    ]
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=max(30, seconds * 20)
        )
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {result.stderr.strip()}")
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError("FFmpeg returned success but produced no output file")
    except Exception:
        # Do not leave a partial output that looks like a successful render.
        destination.unlink(missing_ok=True)
        raise


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
    args = parser.parse_args(argv)

    try:
        if args.command == "capabilities":
            print(json.dumps(CAPABILITIES, indent=2))
        elif args.command == "diagnose":
            print(json.dumps(diagnose(), indent=2))
        elif args.command == "photo-animation":
            render_photo_animation(args.input, args.output, args.seconds, args.fps)
            print(f"Rendered: {args.output}")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"editai-worker: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
