#!/usr/bin/env python3
"""Script to validate the local EditAI worker using standard tools available on the machine.

If FFmpeg/ffprobe are installed, it creates a synthetic still frame, renders a tiny MP4,
and inspects stream metadata. If not installed, it exits cleanly with an explicit note.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_ppm(path: Path, width: int = 120, height: int = 80, color: str = "64,128,255") -> None:
    r, g, b = [int(part.strip()) for part in color.split(",")]
    lines = [f"P3\n{width} {height}\n255\n"]
    for _ in range(height):
        for _ in range(width):
            lines.append(f"{r} {g} {b} ")
    path.write_text("".join(lines), encoding="utf-8")


def validate_with_ffmpeg(base_dir: Path) -> dict[str, object]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        return {
            "status": "skipped",
            "reason": "ffmpeg or ffprobe not found on PATH",
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
        }

    base_dir = base_dir.expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    source = base_dir / "source.ppm"
    _write_ppm(source)
    output = base_dir / "validation.mp4"
    render = subprocess.run([
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-loop",
        "1",
        "-i",
        str(source),
        "-frames:v",
        "24",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ], capture_output=True, text=True)
    if render.returncode != 0:
        return {"status": "failed", "reason": render.stderr.strip() or "ffmpeg render failed"}
    probe = subprocess.run([
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate:format=duration,size",
        "-of",
        "json",
        str(output),
    ], capture_output=True, text=True)
    if probe.returncode != 0:
        return {"status": "failed", "reason": probe.stderr.strip() or "ffprobe inspection failed"}
    try:
        parsed = json.loads(probe.stdout)
    except json.JSONDecodeError:
        return {"status": "failed", "reason": "ffprobe returned invalid JSON"}
    return {"status": "passed", "rendered_path": str(output), "probe": parsed}


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="editai-ffmpeg-validate")
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/ffmpeg_validation"))
    args = parser.parse_args(argv)
    result = validate_with_ffmpeg(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
