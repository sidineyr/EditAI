#!/usr/bin/env python3
"""Local benchmarking for the EditAI worker slice.

This CLI measures a few fast, representative local operations and emits JSON/CSV-like
machine-readable results for reporting. It intentionally avoids unsupported claims,
measures only what is explicitly executed, and records skipped or failed operations.
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

try:
    from services.local_worker.editai_worker import render_photo_animation
    from services.local_worker.project import add_photo, create_project, load_project
except ImportError:  # pragma: no cover
    from editai_worker import render_photo_animation
    from project import add_photo, create_project, load_project


def _ppm_image(path: Path, width: int = 160, height: int = 120, color: str = "255,128,64") -> None:
    r, g, b = map(int, color.split(","))
    pixels = []
    for _ in range(height):
        row = []
        for _ in range(width):
            row.append(f"{r} {g} {b} ")
        pixels.append("".join(row))
    content = [f"P3\n{width} {height}\n255\n"]
    for y in range(height):
        for x in range(width):
            content.append(f"{r} {g} {b} ")
    path.write_text("".join(content), encoding="utf-8")


def benchmark_photo_animation(output_dir: Path, runs: int = 3) -> dict[str, object]:
    if runs < 1:
        raise ValueError("runs must be at least 1")
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    image = output_dir / "benchmark.ppm"
    _ppm_image(image)
    samples: list[float] = []
    for index in range(runs):
        output = output_dir / f"render_{index}.mp4"
        start = time.perf_counter()
        render_photo_animation(image, output, 2.0, 24)
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
        output.unlink(missing_ok=True)
    return {
        "operation": "photo.pan_zoom",
        "runs": runs,
        "samples_seconds": samples,
        "median_seconds": statistics.median(samples),
        "mean_seconds": statistics.mean(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }


def benchmark_project_roundtrip(output_dir: Path, runs: int = 3) -> dict[str, object]:
    if runs < 1:
        raise ValueError("runs must be at least 1")
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    samples: list[float] = []
    for index in range(runs):
        root = output_dir / f"project_{index}"
        source = output_dir / f"source_{index}.ppm"
        _ppm_image(source)
        start = time.perf_counter()
        create_project(root, f"Bench {index}")
        add_photo(root, source, 1.5)
        project = load_project(root)
        if len(project["scenes"]) != 1:
            raise RuntimeError("Project benchmark created an unexpected number of scenes")
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
    return {
        "operation": "project.portable_v1",
        "runs": runs,
        "samples_seconds": samples,
        "median_seconds": statistics.median(samples),
        "mean_seconds": statistics.mean(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="editai-benchmark")
    parser.add_argument("--output", type=Path, default=Path("benchmarks"))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--kind", choices=["photo", "project", "all"], default="all")
    args = parser.parse_args(argv)
    try:
        output_dir = args.output.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        if args.kind in {"photo", "all"}:
            results["photo"] = benchmark_photo_animation(output_dir / "photo", args.runs)
        if args.kind in {"project", "all"}:
            results["project"] = benchmark_project_roundtrip(output_dir / "project", args.runs)
        report_path = output_dir / "benchmark_report.json"
        report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"Benchmark report written to: {report_path}")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"editai-benchmark: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
