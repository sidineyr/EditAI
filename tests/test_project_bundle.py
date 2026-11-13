import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "services/local_worker/project.py"
SPEC = importlib.util.spec_from_file_location("editai_project", MODULE_PATH)
project = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(project)


class ProjectBundleTests(unittest.TestCase):
    def make_project(self, parent: Path) -> Path:
        root = parent / "original project"
        source = parent / "photo with spaces.png"
        source.write_bytes(b"not a real png; project layer does not decode media")
        project.create_project(root, "Bundle test")
        project.add_photo(root, source, 2)
        return root

    def test_roundtrip_and_scene_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = self.make_project(parent)
            scene_id = project.load_project(root)["scenes"][0]["id"]
            project.set_scene_duration(root, scene_id, 3.25)
            project.set_scene_approval(root, scene_id, True)
            archive = parent / "portable project.zip"
            project.export_project_archive(root, archive)
            restored = project.import_project_archive(archive, parent / "restored")
            scene = project.load_project(restored)["scenes"][0]
            self.assertEqual(scene["duration_seconds"], 3.25)
            self.assertTrue(scene["approved"])
            self.assertEqual(len(project.project_scene_paths(restored)), 1)

    def test_export_selected_scenes_only(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = self.make_project(parent)
            photo2 = parent / "second.png"; photo2.write_bytes(b"other image")
            project.add_photo(root, photo2, 1)
            scenes = project.load_project(root)["scenes"]
            archive = parent / "selected.zip"
            project.export_project_archive(root, archive, {scenes[1]["id"]})
            imported = project.import_project_archive(archive, parent / "selected")
            self.assertEqual(len(project.load_project(imported)["scenes"]), 1)
            self.assertEqual(len(project.load_project(imported)["assets"]), 1)

    def test_rejects_traversal_archive_and_preserves_no_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            malicious = parent / "bad.zip"
            with zipfile.ZipFile(malicious, "w") as archive:
                archive.writestr("../escape.txt", "bad")
            destination = parent / "restored"
            with self.assertRaises(ValueError):
                project.import_project_archive(malicious, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((parent / "escape.txt").exists())

    def test_refuses_overwrite_archive_and_import_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = self.make_project(parent)
            archive = parent / "bundle.zip"; archive.write_bytes(b"keep")
            with self.assertRaises(FileExistsError): project.export_project_archive(root, archive)
            self.assertEqual(archive.read_bytes(), b"keep")
            valid_archive = parent / "valid.zip"
            project.export_project_archive(root, valid_archive)
            existing = parent / "existing"; existing.mkdir()
            with self.assertRaises(FileExistsError): project.import_project_archive(valid_archive, existing)

    def test_scene_changes_validate_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = self.make_project(parent)
            with self.assertRaises(ValueError): project.set_scene_duration(root, "missing", 2)
            scene_id = project.load_project(root)["scenes"][0]["id"]
            with self.assertRaises(ValueError): project.set_scene_duration(root, scene_id, 0)


if __name__ == "__main__":
    unittest.main()
