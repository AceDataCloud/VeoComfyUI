"""ComfyUI model choices and native VIDEO shape."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "veo_comfy", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
nodes = sys.modules["veo_comfy.nodes"]


class VeoNodeTests(unittest.TestCase):
    def test_all_five_dify_models_are_offered_in_compatible_nodes(self):
        text_models = set(nodes.AceVeoTextToVideo.INPUT_TYPES()["required"]["model"][0])
        ingredients = set(nodes.AceVeoIngredientsToVideo.INPUT_TYPES()["required"]["model"][0])
        self.assertEqual(len(text_models), 4)
        self.assertEqual(ingredients, {"veo31-fast-ingredients"})
        self.assertEqual(len(text_models | ingredients), 5)

    def test_submission_shows_task_id_without_claiming_video(self):
        with patch.object(nodes, "submit_video", return_value=("pending", "task-123", "", "trace-123")):
            value = nodes.AceVeoTextToVideo().run("whale", "veo31-fast", "default", False)
        self.assertEqual(value["result"], ("pending", "task-123", "", "trace-123"))
        self.assertIn("task-123", " ".join(value["ui"]["text"]))

    def test_loader_returns_native_video_object(self):
        fake_package = types.ModuleType("comfy_api")
        fake_latest = types.ModuleType("comfy_api.latest")
        class FakeVideo:
            def __init__(self, raw):
                self.raw = raw
        fake_latest.VideoFromFile = FakeVideo
        with patch.dict(sys.modules, {"comfy_api": fake_package, "comfy_api.latest": fake_latest}):
            with patch.object(nodes, "download_video", return_value=b"video-bytes"):
                (video,) = nodes.AceVeoLoadVideo().run("https://platform.cdn.acedata.cloud/a.mp4")
        self.assertEqual(video.raw.getvalue(), b"video-bytes")


if __name__ == "__main__":
    unittest.main()
