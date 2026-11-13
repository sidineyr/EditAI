#!/usr/bin/env python3
"""Local storyboard planner for EditAI projects. Uses only the Python standard library."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from services.local_worker.project import load_project
except ImportError:  # pragma: no cover
    from project import load_project


def storyboard_payload(project_dir: Path) -> dict[str, object]:
    data = load_project(project_dir)
    assets = {asset["id"]: asset for asset in data["assets"]}
    scenes = []
    for index, scene in enumerate(data["scenes"], start=1):
        asset = assets[scene["asset_id"]]
        scenes.append({
            "index": index,
            "scene_id": scene["id"],
            "asset_id": asset["id"],
            "asset_path": asset["path"],
            "duration_seconds": float(scene["duration_seconds"]),
            "approved": bool(scene.get("approved", False)),
            "prompt": str(scene.get("prompt", "")),
        })
    return {"project_title": data["title"], "scenes": scenes}


def set_scene_prompt(project_dir: Path, scene_id: str, prompt: str) -> None:
    project_dir = project_dir.expanduser().resolve(strict=True)
    data = load_project(project_dir)
    scene = next((item for item in data["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene: {scene_id}")
    scene["prompt"] = prompt
    path = project_dir / "project.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="editai-storyboard")
    sub = parser.add_subparsers(dest="command", required=True)
    list_cmd = sub.add_parser("list", help="show storyboard information for a project")
    list_cmd.add_argument("project", type=Path)
    set_cmd = sub.add_parser("set-prompt", help="write a text prompt for a specific scene")
    set_cmd.add_argument("project", type=Path)
    set_cmd.add_argument("scene_id")
    set_cmd.add_argument("prompt")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(json.dumps(storyboard_payload(args.project), indent=2))
        elif args.command == "set-prompt":
            set_scene_prompt(args.project, args.scene_id, args.prompt)
            print(json.dumps(storyboard_payload(args.project), indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"editai-storyboard: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
