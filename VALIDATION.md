import importlib.util
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).parents[1] / "services/local_worker/project.py"
SPEC_PROJECT = importlib.util.spec_from_file_location("editai_project", PROJECT)
project = importlib.util.module_from_spec(SPEC_PROJECT)
assert SPEC_PROJECT and SPEC_PROJECT.loader
SPEC_PROJECT.loader.exec_module(project)

TIMELINE = Path(__file__).parents[1] / "services/local_worker/timeline.py"
SPEC_TIMELINE = importlib.util.spec_from_file_location("editai_timeline", TIMELINE)
timeline = importlib.util.module_from_spec(SPEC_TIMELINE)
assert SPEC_TIMELINE and SPEC_TIMELINE.loader
SPEC_TIMELINE.loader.exec_module(timeline)


class TimelineTests(unittest.TestCase):
    def test_build_timeline_sets_scene_starts_and_ends(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-project"
            source = Path(directory) / "scene.png"
            source.write_bytes(b"fixture")
            project.create_project(root, "Demo")
            project.add_photo(root, source, 2.0)
            payload = timeline.build_timeline(root)
            self.assertEqual(payload["project_title"], "Demo")
            self.assertEqual(payload["total_duration_seconds"], 2.0)
            self.assertEqual(payload["timeline"][0]["duration_seconds"], 2.0)
            self.assertEqual(payload["timeline"][0]["end_seconds"], 2.0)

    def test_validate_timeline_accepts_valid_sequence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-project"
            source = Path(directory) / "scene.png"
            source.write_bytes(b"fixture")
            project.create_project(root, "Demo")
            project.add_photo(root, source, 4.0)
            result = timeline.validate_timeline(root)
            self.assertTrue(result["valid"])
            self.assertEqual(result["problems"], [])


if __name__ == "__main__":
    unittest.main()
