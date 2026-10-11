"""Veo action/model, async task, billing-boundary, and media checks."""

import os
import unittest
from unittest.mock import Mock, patch

import client


class VeoClientTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"ACEDATACLOUD_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)

    @patch("client.requests.post")
    def test_text_generation_submits_once_with_supported_model(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "task-123", "trace_id": "trace-123"}
        result = client.submit_video("text2video", "veo31-fast", "A whale breaches")
        self.assertEqual(result, ("pending", "task-123", "", "trace-123"))
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "https://api.acedata.cloud/veo/videos")
        self.assertEqual(post.call_args.kwargs["json"]["action"], "text2video")

    @patch("client.requests.post")
    def test_ingredient_model_requires_images_and_action(self, post):
        with self.assertRaises(ValueError):
            client.submit_video("text2video", "veo31-fast-ingredients", "A scene")
        with self.assertRaises(ValueError):
            client.submit_video("ingredients2video", "veo31-fast", "A scene",
                                image_urls='["https://example.org/a.png"]')
        with self.assertRaises(ValueError):
            client.submit_video("ingredients2video", "veo31-fast-ingredients", "A scene",
                                image_urls='["https://127.0.0.1/a.png"]')
        post.assert_not_called()

    @patch("client.requests.post")
    def test_image_and_ingredient_payloads_have_correct_limits(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "task-123"}
        client.submit_video("image2video", "veo3", "Animate", image_urls='["https://example.org/a.png"]',
                            aspect_ratio="9:16")
        first = post.call_args.kwargs["json"]
        self.assertEqual(first["image_urls"], ["https://example.org/a.png"])
        self.assertEqual(first["aspect_ratio"], "9:16")
        client.submit_video("ingredients2video", "veo31-fast-ingredients", "Blend",
                            image_urls='["https://example.org/a.png","https://example.org/b.png"]')
        second = post.call_args.kwargs["json"]
        self.assertEqual(second["action"], "ingredients2video")
        self.assertNotIn("aspect_ratio", second)

    @patch("client.requests.post")
    def test_4k_and_get1080p_validation(self, post):
        with self.assertRaises(ValueError):
            client.submit_video("text2video", "veo3", "A scene", resolution="4k")
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "upscale-123"}
        self.assertEqual(client.submit_video("get1080p", "veo3", video_id="video-123")[1], "upscale-123")
        self.assertEqual(post.call_args.kwargs["json"]["video_id"], "video-123")

    @patch("client.requests.post")
    def test_each_advanced_dify_endpoint_uses_its_contract(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"task_id": "task-123"}
        client.extend("video-123", "veo31-fast", resolution="1080p")
        client.edit_objects("video-123", "insert", "Add a bird")
        client.reshoot("video-123", "LEFT_TO_RIGHT")
        client.upsample("video-123", "4k")
        self.assertEqual([call.args[0] for call in post.call_args_list], [
            "https://api.acedata.cloud/veo/extend", "https://api.acedata.cloud/veo/objects",
            "https://api.acedata.cloud/veo/reshoot", "https://api.acedata.cloud/veo/upsample",
        ])
        self.assertEqual(post.call_args_list[0].kwargs["json"]["model"], "veo31-fast")
        self.assertEqual(post.call_args_list[2].kwargs["json"]["motion_type"], "LEFT_TO_RIGHT")

    @patch("client.requests.post")
    def test_remove_requires_public_mask_before_paid_submission(self, post):
        with self.assertRaises(ValueError):
            client.edit_objects("video-123", "remove")
        with self.assertRaises(ValueError):
            client.edit_objects("video-123", "remove", image_mask="https://127.0.0.1/mask.jpg")
        post.assert_not_called()

    @patch("client.requests.post")
    def test_submission_timeout_never_retries_or_leaks_key(self, post):
        post.side_effect = client.requests.Timeout("Bearer test-key")
        with self.assertRaises(client.VeoError) as caught:
            client.submit_video("text2video", "veo31-fast", "A whale")
        post.assert_called_once()
        self.assertNotIn("test-key", str(caught.exception))

    @patch("client.requests.post")
    def test_pending_preview_is_not_terminal_success(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {
            "id": "task-123", "finished_at": None,
            "response": {"data": [{"state": "pending", "video_url": "https://platform.cdn.acedata.cloud/a.mp4"}]},
        }
        self.assertEqual(client.retrieve_once("task-123")[:3], ("pending", "task-123", ""))

    @patch("client.requests.post")
    def test_terminal_task_returns_video_url(self, post):
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {
            "id": "task-123", "finished_at": 1753435250.969,
            "response": {"success": True, "data": [{"state": "succeeded",
                "video_url": "https://platform.cdn.acedata.cloud/veo/a.mp4"}]},
        }
        self.assertEqual(client.retrieve_once("task-123")[:3],
                         ("succeeded", "task-123", "https://platform.cdn.acedata.cloud/veo/a.mp4"))

    @patch("client.requests.get")
    def test_video_loader_rejects_non_ace_hosts(self, get):
        for url in ("https://127.0.0.1/a.mp4", "https://platform.cdn.acedata.cloud.evil.test/a.mp4",
                    "http://platform.cdn.acedata.cloud/a.mp4"):
            with self.assertRaises(client.VeoError):
                client.download_video(url)
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
