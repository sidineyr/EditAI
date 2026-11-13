#!/usr/bin/env python3
"""Portable project editing and bundle CLI using only the Python standard library."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from project import export_project_archive, import_project_archive, set_scene_approval, set_scene_duration
except ImportError:
    from services.local_worker.project import export_project_archive, import_project_archive, set_scene_approval, set_scene_duration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="editai-project")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="create a portable project ZIP")
    export.add_argument("project", type=Path)
    export.add_argument("archive", type=Path)
    export.add_argument("--scene", action="append", dest="scenes", help="include this scene ID (repeatable); omit for all scenes")
    imp = commands.add_parser("import", help="validate and import a portable project ZIP")
    imp.add_argument("archive", type=Path)
    imp.add_argument("destination", type=Path)
    duration = commands.add_parser("duration", help="change a scene duration without changing its source")
    duration.add_argument("project", type=Path); duration.add_argument("scene_id"); duration.add_argument("seconds", type=float)
    approval = commands.add_parser("approve", help="mark a scene approved or unapproved")
    approval.add_argument("project", type=Path); approval.add_argument("scene_id"); approval.add_argument("--yes", action="store_true", required=True)
    approval.add_argument("--unapprove", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            result = export_project_archive(args.project, args.archive, set(args.scenes) if args.scenes else None)
        elif args.command == "import":
            result = import_project_archive(args.archive, args.destination)
        elif args.command == "duration":
            set_scene_duration(args.project, args.scene_id, args.seconds); result = args.project
        else:
            set_scene_approval(args.project, args.scene_id, not args.unapprove); result = args.project
        print(result)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"editai-project: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
