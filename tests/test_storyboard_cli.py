import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "services/local_worker/storyboard_cli.py"
SPEC = importlib.util.spec_from_file_location("editai_storyboard", MODULE_PATH)
storyboard = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(storyboard)

MODULE_PROJECT = Path(__file__).parents[1] / "services/local_worker/project.py"
SPEC_PROJECT = importlib.util.spec_from_file_location("editai_project", MODULE_PROJECT)
project = importlib.util.module_from_spec(SPEC_PROJECT)
assert SPEC_PROJECT and SPEC_PROJECT.loader
SPEC_PROJECT.loader.exec_module(project)


class StoryboardTests(unittest.TestCase):
    def test_storyboard_payload_contains_scene_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-project"
            source = Path(directory) / "view.png"
            source.write_bytes(b"fixture")
            project.create_project(root, "Demo")
            project.add_photo(root, source, 2.5)
            payload = storyboard.storyboard_payload(root)
            self.assertEqual(payload["project_title"], "Demo")
            self.assertEqual(len(payload["scenes"]), 1)
            self.assertEqual(payload["scenes"][0]["duration_seconds"], 2.5)

    def test_set_scene_prompt_updates_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo-project"
            source = Path(directory) / "view.png"
            source.write_bytes(b"fixture")
            project.create_project(root, "Demo")
            project.add_photo(root, source, 2.5)
            scene_id = project.load_project(root)["scenes"][0]["id"]
            storyboard.set_scene_prompt(root, scene_id, "sunrise over the city")
            updated = project.load_project(root)
            self.assertEqual(updated["scenes"][0]["prompt"], "sunrise over the city")


if __name__ == "__main__":
    unittest.main()
