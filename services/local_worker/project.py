#!/usr/bin/env python3
"""Versioned, portable EditAI project manifest and asset helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
MAX_PROJECT_BYTES = 2 * 1024 * 1024
MAX_ASSETS = 500
MAX_ARCHIVE_MEMBERS = MAX_ASSETS + 1
MAX_ARCHIVE_UNCOMPRESSED = 1024 * 1024 * 1024
MAX_ARCHIVE_FILE = 1100 * 1024 * 1024
MAX_MEMBER_SIZE = 512 * 1024 * 1024


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
        asset_id, rel, expected = asset.get("id"), asset.get("path"), asset.get("sha256")
        if not isinstance(asset_id, str) or not re.fullmatch(r"[a-f0-9]{16}", asset_id) or asset_id in asset_ids:
            raise ValueError("Missing, invalid, or duplicate asset ID")
        asset_ids.add(asset_id)
        if not isinstance(rel, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Invalid asset path or SHA-256")
        candidate = (root / rel).resolve(strict=True)
        if not candidate.is_file() or not candidate.is_relative_to(root):
            raise ValueError("Asset path escapes project directory or is not a regular file")
        if verify_hashes and sha256_file(candidate) != expected:
            raise ValueError(f"Asset integrity check failed: {asset_id}")
    scene_ids: set[str] = set()
    for scene in data["scenes"]:
        if not isinstance(scene, dict) or scene.get("asset_id") not in asset_ids:
            raise ValueError("Scene references a missing asset")
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not scene_id or scene_id in scene_ids:
            raise ValueError("Missing or duplicate scene ID")
        scene_ids.add(scene_id)
        duration = scene.get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0.1 <= duration <= 120:
            raise ValueError("Scene duration must be between 0.1 and 120 seconds")
        if "approved" in scene and not isinstance(scene["approved"], bool):
            raise ValueError("Scene approval must be a boolean")
    return data


def add_photo(root: Path, source: Path, duration: float = 4.0) -> dict[str, Any]:
    if not 0.1 <= duration <= 120:
        raise ValueError("duration must be between 0.1 and 120 seconds")
    source = source.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("Photo source must be a regular file")
    root = root.expanduser().resolve(strict=True)
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
    destination = root / "assets" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    asset = {"id": asset_id, "path": f"assets/{filename}", "sha256": digest, "kind": "image"}
    data["assets"].append(asset)
    data["scenes"].append({"id": f"scene-{len(data['scenes']) + 1}", "asset_id": asset_id, "duration_seconds": float(duration), "approved": False})
    try:
        _atomic_json(_project_file(root), data)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return asset


def set_scene_duration(root: Path, scene_id: str, duration: float) -> None:
    if not 0.1 <= duration <= 120:
        raise ValueError("duration must be between 0.1 and 120 seconds")
    root = root.expanduser().resolve(strict=True)
    data = load_project(root)
    scene = next((item for item in data["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene: {scene_id}")
    scene["duration_seconds"] = float(duration)
    _atomic_json(_project_file(root), data)


def set_scene_approval(root: Path, scene_id: str, approved: bool) -> None:
    if not isinstance(approved, bool):
        raise ValueError("approved must be true or false")
    root = root.expanduser().resolve(strict=True)
    data = load_project(root)
    scene = next((item for item in data["scenes"] if item["id"] == scene_id), None)
    if scene is None:
        raise ValueError(f"Unknown scene: {scene_id}")
    scene["approved"] = approved
    _atomic_json(_project_file(root), data)


def project_scene_paths(root: Path) -> list[tuple[Path, float]]:
    root = root.expanduser().resolve(strict=True)
    data = load_project(root)
    assets = {asset["id"]: asset for asset in data["assets"]}
    return [(root / assets[scene["asset_id"]]["path"], float(scene["duration_seconds"])) for scene in data["scenes"]]


def _safe_archive_name(name: str) -> PurePosixPath:
    if "\\" in name or "\x00" in name:
        raise ValueError("Archive contains an invalid path")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("Archive path traversal is not allowed")
    if name != "project.json" and not (len(path.parts) == 2 and path.parts[0] == "assets"):
        raise ValueError("Archive contains an unsupported file path")
    return path


def export_project_archive(root: Path, destination: Path, scene_ids: set[str] | None = None) -> Path:
    root = root.expanduser().resolve(strict=True)
    data = load_project(root)
    if scene_ids is not None:
        if not scene_ids or any(not isinstance(item, str) for item in scene_ids):
            raise ValueError("Select at least one valid scene ID")
        scenes = [scene for scene in data["scenes"] if scene["id"] in scene_ids]
        if len(scenes) != len(scene_ids):
            raise ValueError("One or more selected scene IDs do not exist")
        used = {scene["asset_id"] for scene in scenes}
        data["scenes"] = scenes
        data["assets"] = [asset for asset in data["assets"] if asset["id"] in used]
    destination = destination.expanduser().resolve()
    if destination.exists() or destination == root or root in destination.parents:
        raise FileExistsError("Archive output must be a new path outside the project")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".editai-archive-", suffix=".zip", dir=destination.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr("project.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            for asset in data["assets"]:
                archive.write(root / asset["path"], asset["path"])
        # Atomic exclusive publication: hard-link fails if another writer created destination.
        os.link(temporary, destination)
        temporary.unlink()
        return destination
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def import_project_archive(archive_path: Path, destination: Path) -> Path:
    archive_path = archive_path.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    if not archive_path.is_file() or archive_path.stat().st_size > MAX_ARCHIVE_FILE:
        raise ValueError("Archive is not a regular file or exceeds the size limit")
    if destination.exists() or destination == archive_path or archive_path in destination.parents:
        raise FileExistsError("Import destination must be a new directory separate from the archive")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".editai-import-", dir=destination.parent))
    try:
        with zipfile.ZipFile(archive_path, "r") as bundle:
            entries = bundle.infolist()
            if not entries or len(entries) > MAX_ARCHIVE_MEMBERS:
                raise ValueError("Archive member count is invalid")
            seen: set[str] = set()
            total = 0
            for info in entries:
                safe = _safe_archive_name(info.filename)
                if info.is_dir() or info.filename in seen:
                    raise ValueError("Directories and duplicate archive paths are not accepted")
                seen.add(info.filename)
                mode = (info.external_attr >> 16) & 0xFFFF
                if mode and (mode & 0o170000) == 0o120000:
                    raise ValueError("Symbolic links are not allowed in project archives")
                if info.file_size < 0 or info.file_size > MAX_MEMBER_SIZE:
                    raise ValueError("Archive member exceeds size limit")
                total += info.file_size
                if total > MAX_ARCHIVE_UNCOMPRESSED:
                    raise ValueError("Archive expands beyond the configured size limit")
                target = staging.joinpath(*safe.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                copied = 0
                with bundle.open(info, "r") as source, target.open("xb") as output:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > info.file_size or copied > MAX_MEMBER_SIZE:
                            raise ValueError("Archive member expands beyond its declared size")
                        output.write(chunk)
                if copied != info.file_size:
                    raise ValueError("Archive member size does not match its directory entry")
        if "project.json" not in seen:
            raise ValueError("Archive is missing project.json")
        load_project(staging)
        # Create destination exclusively; then move only the validated manifest and asset tree.
        destination.mkdir()
        try:
            (destination / "assets").parent.mkdir(exist_ok=True)
            if (staging / "assets").exists():
                os.replace(staging / "assets", destination / "assets")
            os.replace(staging / "project.json", destination / "project.json")
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        return destination
    finally:
        shutil.rmtree(staging, ignore_errors=True)
