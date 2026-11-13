import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "services/local_worker/editai_worker.py"
SPEC = importlib.util.spec_from_file_location("editai_worker", MODULE_PATH)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def test_registry_marks_pan_zoom_as_conventional_not_neural(self):
        operation = worker.CAPABILITIES["operations"][0]
        self.assertEqual(operation["id"], "photo.pan_zoom")
        self.assertFalse(operation["neural"])

    def test_render_rejects_same_input_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "photo.png"
            path.write_bytes(b"not a real image")
            with self.assertRaises(ValueError):
                worker.render_photo_animation(path, path, 1, 24)

    def test_render_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            output = Path(directory) / "output.mp4"
            source.write_bytes(b"fixture")
            output.write_bytes(b"preserve me")
            with self.assertRaises(FileExistsError):
                worker.render_photo_animation(source, output, 1, 24)
            self.assertEqual(output.read_bytes(), b"preserve me")

    def test_render_bounds_duration_and_frame_rate(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            source.write_bytes(b"fixture")
            with self.assertRaises(ValueError):
                worker.render_photo_animation(source, Path(directory) / "out.mp4", 0, 24)
            with self.assertRaises(ValueError):
                worker.render_photo_animation(source, Path(directory) / "out.mp4", 1, 0)


if __name__ == "__main__":
    unittest.main()
