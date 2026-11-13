import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "services/local_worker/editai_worker.py"
SPEC = importlib.util.spec_from_file_location("editai_worker", MODULE_PATH)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(worker)
project = worker


class WorkerTests(unittest.TestCase):
    def test_registry_marks_pan_zoom_as_conventional_not_neural(self):
        by_id = {op["id"]: op for op in worker.CAPABILITIES["operations"]}
        self.assertFalse(by_id["photo.pan_zoom"]["neural"])
        self.assertFalse(by_id["photos.montage"]["neural"])

    def test_refuses_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "photo.png"
            path.write_bytes(b"not a real image")
            with self.assertRaises(ValueError):
                worker.render_photo_animation(path, path, 1, 24)

    def test_render_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"; output = Path(directory) / "output.mp4"
            source.write_bytes(b"fixture"); output.write_bytes(b"preserve me")
            with self.assertRaises(FileExistsError): worker.render_photo_animation(source, output, 1, 24)
            self.assertEqual(output.read_bytes(), b"preserve me")

    def test_render_bounds_duration_and_frame_rate(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"; source.write_bytes(b"fixture")
            with self.assertRaises(ValueError): worker.render_photo_animation(source, Path(directory) / "out.mp4", 0, 24)
            with self.assertRaises(ValueError): worker.render_photo_animation(source, Path(directory) / "out.mp4", 1, 0)

    def test_project_asset_roundtrip_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "my project"
            source = Path(directory) / "a photo ü.png"; source.write_bytes(b"synthetic fixture bytes")
            worker.create_project(root, "Test project")
            worker.add_photo(root, source, 2.5)
            data = worker.load_project(root)
            self.assertEqual(data["title"], "Test project")
            self.assertEqual(len(worker.project_scene_paths(root)), 1)
            copied = root / data["assets"][0]["path"]
            copied.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "integrity"):
                worker.load_project(root)

    def test_project_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"; source = Path(directory) / "x.png"
            source.write_bytes(b"fixture"); worker.create_project(root, "Test")
            worker.add_photo(root, source)
            manifest = root / "project.json"; data = json.loads(manifest.read_text())
            data["assets"][0]["path"] = "../../outside.png"
            manifest.write_text(json.dumps(data))
            with self.assertRaises((ValueError, FileNotFoundError)):
                worker.load_project(root)


if __name__ == "__main__": unittest.main()
