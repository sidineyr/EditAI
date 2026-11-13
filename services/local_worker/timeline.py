#!/usr/bin/env python3
"""Local timeline model and validation helper for EditAI project scenes.

This module intentionally keeps the data model small and explicit: a project contains
scenes, and a timeline is an ordered list of scene entries with optional start time,
track, and effect metadata. The model is local-first and does not vendor a cloud API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from services.local_worker.project import load_project
except ImportError:  # pragma: no cover
    from project import load_project


def build_timeline(project_dir: Path) -> dict[str, Any]:
    data = load_project(project_dir)
    timeline: list[dict[str, Any]] = []
    cursor = 0.0
    for scene in data["scenes"]:
        start = round(cursor, 6)
        duration = float(scene["duration_seconds"])
        timeline.append({
            "scene_id": scene["id"],
            "start_seconds": start,
            "duration_seconds": duration,
            "end_seconds": round(start + duration, 6),
            "track": "video",
            "kind": "image",
            "approved": bool(scene.get("approved", False)),
            "prompt": str(scene.get("prompt", "")),
        })
        cursor += duration
    return {"project_title": data["title"], "total_duration_seconds": round(cursor, 6), "tracks": ["video"], "timeline": timeline}


def add_timeline_entry(project_dir: Path, scene_id: str, *, track: str = "video", kind: str = "image", start_seconds: float | None = None) -> dict[str, Any]:
    project_dir = project_dir.expanduser().resolve(strict=True)
    data = load_project(project_dir)
    scene = next((item for item in data["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene ID: {scene_id}")
    timeline = build_timeline(project_dir)
    if start_seconds is None:
        start_seconds = float(timeline["total_duration_seconds"])
    if start_seconds < 0:
        raise ValueError("start_seconds must be >= 0")
    entry = {
        "scene_id": scene_id,
        "start_seconds": round(float(start_seconds), 6),
        "duration_seconds": float(scene["duration_seconds"]),
        "end_seconds": round(float(start_seconds) + float(scene["duration_seconds"]), 6),
        "track": track,
        "kind": kind,
        "approved": bool(scene.get("approved", False)),
        "prompt": str(scene.get("prompt", "")),
    }
    timeline["timeline"].append(entry)
    timeline["total_duration_seconds"] = round(max((item["end_seconds"] for item in timeline["timeline"]), default=0.0), 6)
    return timeline


def validate_timeline(project_dir: Path) -> dict[str, Any]:
    timeline = build_timeline(project_dir)
    problems: list[str] = []
    for index, item in enumerate(timeline["timeline"]):
        if item["duration_seconds"] <= 0:
            problems.append(f"scene {index} has a non-positive duration")
        if item["start_seconds"] < 0:
            problems.append(f"scene {index} starts before zero")
        if item["end_seconds"] < item["start_seconds"]:
            problems.append(f"scene {index} ends before it starts")
    return {"project_title": timeline["project_title"], "valid": not problems, "problems": problems, "total_duration_seconds": timeline["total_duration_seconds"]}


def save_timeline(project_dir: Path, output: Path | None = None) -> Path:
    project_dir = project_dir.expanduser().resolve(strict=True)
    payload = build_timeline(project_dir)
    destination = output.expanduser().resolve() if output else project_dir / "timeline.json"
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing timeline: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="editai-timeline")
    parser.add_argument("project", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = build_timeline(args.project)
    result = save_timeline(args.project, args.output) if args.output else save_timeline(args.project)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Timeline saved to: {result}")
