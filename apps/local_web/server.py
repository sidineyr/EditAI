#!/usr/bin/env python3
"""Small local web UI for EditAI projects. Uses only the Python standard library."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import os
import shutil

try:
    from services.local_worker.project import add_photo, create_project, load_project
except ImportError:  # pragma: no cover
    from project import add_photo, create_project, load_project


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>EditAI local studio</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; background: #111827; color: #f3f4f6; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
    .panel { background: #1f2937; border-radius: 12px; padding: 1rem; }
    input, button, textarea { width: 100%; box-sizing: border-box; margin-top: 0.5rem; }
    button { background: #2563eb; color: white; border: none; border-radius: 8px; padding: 0.75rem; }
    textarea { min-height: 90px; }
    code { background: #0f172a; padding: 0.2rem 0.4rem; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>EditAI local studio</h1>
  <p>Offline, local-first creative workbench for simple photo projects.</p>
  <div class="grid">
    <div class="panel">
      <h2>New project</h2>
      <input id="title" placeholder="Project title" />
      <input id="name" placeholder="Folder name" />
      <button onclick="createProject()">Create</button>
    </div>
    <div class="panel">
      <h2>Add photo</h2>
      <input id="projectName" placeholder="Project folder" />
      <input id="sourcePath" placeholder="Absolute path to image file" />
      <input id="seconds" type="number" value="4" min="0.1" max="120" step="0.1" />
      <button onclick="addPhoto()">Add photo</button>
    </div>
    <div class="panel">
      <h2>Project summary</h2>
      <input id="summaryProject" placeholder="Project folder" />
      <button onclick="loadSummary()">Load summary</button>
      <pre id="summary"></pre>
    </div>
  </div>
  <script>
    const base = '/api';
    async function jsonPost(url, payload) {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Request failed');
      return data;
    }
    async function createProject() {
      const payload = { title: document.getElementById('title').value, name: document.getElementById('name').value };
      const result = await jsonPost(base + '/projects', payload);
      document.getElementById('summary').textContent = JSON.stringify(result, null, 2);
    }
    async function addPhoto() {
      const payload = {
        project: document.getElementById('projectName').value,
        source_path: document.getElementById('sourcePath').value,
        seconds: Number(document.getElementById('seconds').value)
      };
      const result = await jsonPost(base + '/projects/' + payload.project + '/assets', payload);
      document.getElementById('summary').textContent = JSON.stringify(result, null, 2);
    }
    async function loadSummary() {
      const project = document.getElementById('summaryProject').value;
      const response = await fetch(base + '/projects/' + project);
      const data = await response.json();
      document.getElementById('summary').textContent = JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""


class EditAIHandler(BaseHTTPRequestHandler):
    workspace = Path(__file__).resolve().parents[2] / "workspace"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
            return
        if parsed.path.startswith("/api/projects/"):
            project_name = parsed.path.rsplit("/", 1)[1]
            project_dir = self.workspace / project_name
            if not project_dir.exists():
                self.send_json(404, {"error": "project not found"})
                return
            try:
                self.send_json(200, load_project(project_dir))
            except Exception as exc:  # pragma: no cover
                self.send_json(500, {"error": str(exc)})
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/projects":
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
            name = str(payload.get("name", "")).strip()
            title = str(payload.get("title", "Untitled")).strip()
            if not name:
                self.send_json(400, {"error": "project name is required"})
                return
            self.workspace.mkdir(parents=True, exist_ok=True)
            project_dir = self.workspace / name
            if project_dir.exists():
                self.send_json(409, {"error": "project already exists"})
                return
            create_project(project_dir, title)
            self.send_json(200, {"created": True, "path": str(project_dir), "title": title})
            return
        if parsed.path.startswith("/api/projects/") and parsed.path.endswith("/assets"):
            project_name = parsed.path.split("/api/projects/")[1].split("/assets")[0]
            project_dir = self.workspace / project_name
            if not project_dir.exists():
                self.send_json(404, {"error": "project not found"})
                return
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
            source_path = str(payload.get("source_path", "")).strip()
            seconds = float(payload.get("seconds", 4.0))
            if not source_path:
                self.send_json(400, {"error": "source_path is required"})
                return
            source = Path(source_path).expanduser().resolve(strict=True)
            if not source.is_file():
                self.send_json(400, {"error": "source file does not exist or is not a regular file"})
                return
            try:
                asset = add_photo(project_dir, source, seconds)
                self.send_json(200, {"added": True, "asset": asset, "project": str(project_dir)})
            except Exception as exc:  # pragma: no cover
                self.send_json(500, {"error": str(exc)})
            return
        self.send_json(404, {"error": "not found"})

    def send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = "127.0.0.1", port: int = 8765, workspace: Path | None = None) -> None:
    if workspace is not None:
        EditAIHandler.workspace = workspace.expanduser().resolve()
    else:
        EditAIHandler.workspace = Path(__file__).resolve().parents[2] / "workspace"
    EditAIHandler.workspace.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), EditAIHandler)
    print(f"EditAI local web UI listening on http://{host}:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="editai-local-web")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--workspace", type=Path, default=None)
    args = parser.parse_args()
    serve(args.host, args.port, args.workspace)
