#!/usr/bin/env python3
"""Versioned, portable EditAI project manifest and asset helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MAX_PROJECT_BYTES = 2 * 1024 * 1024
MAX_ASSETS = 500


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_file(root: Path) -> Path:
    return root / "project.json"


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".editai-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def create_project(root: Path, title: str) -> Path:
    root = root.expanduser().resolve()
    if not title.strip() or len(title) > 200:
        raise ValueError("Project title must contain 1-200 characters")
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Project directory must be empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "title": title.strip(),
        "assets": [],
        "scenes": [],
        "provenance": {"application": "EditAI", "schema_version": SCHEMA_VERSION},
    }
    path = _project_file(root)
    _atomic_json(path, data)
    return path


def load_project(root: Path, verify_hashes: bool = True) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    path = _project_file(root)
    if not path.is_file() or path.stat().st_size > MAX_PROJECT_BYTES:
        raise ValueError("Missing project.json or project manifest exceeds size limit")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid project JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported project schema version")
    if not isinstance(data.get("title"), str) or not isinstance(data.get("assets"), list):
        raise ValueError("Invalid project title or assets")
    if not isinstance(data.get("scenes"), list):
        raise ValueError("Invalid project scenes")
    if len(data["assets"]) > MAX_ASSETS or len(data["scenes"]) > MAX_ASSETS:
        raise ValueError("Project exceeds asset or scene limit")
    asset_ids: set[str] = set()
    for asset in data["assets"]:
        if not isinstance(asset, dict):
            raise ValueError("Invalid asset entry")
        asset_id = asset.get("id")
        rel = asset.get("path")
        expected = asset.get("sha256")
        if not isinstance(asset_id, str) or asset_id in asset_ids:
            raise ValueError("Missing or duplicate asset ID")
        asset_ids.add(asset_id)
        if not isinstance(rel, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Invalid asset path or SHA-256")
        candidate = (root / rel).resolve(strict=True)
        if not candidate.is_file() or not candidate.is_relative_to(root):
            raise ValueError("Asset path escapes project directory or is not a regular file")
        if verify_hashes and sha256_file(candidate) != expected:
            raise ValueError(f"Asset integrity check failed: {asset_id}")
    for scene in data["scenes"]:
        if not isinstance(scene, dict) or scene.get("asset_id") not in asset_ids:
            raise ValueError("Scene references a missing asset")
        duration = scene.get("duration_seconds")
        if not isinstance(duration, (int, float)) or not 0.1 <= duration <= 120:
            raise ValueError("Scene duration must be between 0.1 and 120 seconds")
    return data


def add_photo(root: Path, source: Path, duration: float = 4.0) -> dict[str, Any]:
    if not 0.1 <= duration <= 120:
        raise ValueError("duration must be between 0.1 and 120 seconds")
    source = source.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("Photo source must be a regular file")
    data = load_project(root)
    if len(data["assets"]) >= MAX_ASSETS:
        raise ValueError("Project asset limit reached")
    digest = sha256_file(source)
    asset_id = digest[:16]
    if any(asset["id"] == asset_id for asset in data["assets"]):
        raise ValueError("This asset is already in the project")
    suffix = source.suffix.lower()
    if len(suffix) > 12 or not re.fullmatch(r"\.[a-z0-9]+", suffix or ""):
        suffix = ".bin"
    filename = f"{asset_id}{suffix}"
    destination = (Path(root).resolve() / "assets" / filename)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    asset = {"id": asset_id, "path": f"assets/{filename}", "sha256": digest, "kind": "image"}
    data["assets"].append(asset)
    data["scenes"].append({"id": f"scene-{len(data['scenes']) + 1}", "asset_id": asset_id, "duration_seconds": float(duration), "approved": False})
    _atomic_json(_project_file(Path(root).resolve()), data)
    return asset


def project_scene_paths(root: Path) -> list[tuple[Path, float]]:
    root = root.expanduser().resolve(strict=True)
    data = load_project(root)
    assets = {asset["id"]: asset for asset in data["assets"]}
    return [(root / assets[scene["asset_id"]]["path"], float(scene["duration_seconds"])) for scene in data["scenes"]]
