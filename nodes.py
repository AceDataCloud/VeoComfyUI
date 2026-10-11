"""ComfyUI Veo graph nodes with native VIDEO output."""

from __future__ import annotations

import json
from io import BytesIO

from .client import (EXTEND_MODELS, MODELS, MOTION_TYPES, RATIOS, RESOLUTIONS,
                     STANDARD_MODELS, UPSAMPLE_ACTIONS, VeoError, download_video,
                     edit_objects, extend, reshoot, retrieve, retrieve_batch,
                     submit_video, upsample)


def _submitted(result):
    status, task_id, video_url, trace_id = result
    return {"ui": {"text": [f"Veo status: {status}", f"Task ID: {task_id or 'completed synchronously'}",
                            "Use Retrieve with this ID; do not resubmit to poll." if task_id and not video_url
                            else "Video is ready."]},
            "result": (status, task_id, video_url, trace_id)}


class AceVeoTextToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "A whale breaches at golden hour."}),
            "model": (list(STANDARD_MODELS), {"default": "veo31-fast"}),
            "resolution": (list(RESOLUTIONS), {"default": "default"}),
            "translation": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "task_id", "video_url", "trace_id")
    FUNCTION = "run"
    CATEGORY = "Ace Data Cloud/Veo"
    DESCRIPTION = "Submit one paid Veo text-to-video task. Retrieve the same task ID."
    OUTPUT_NODE = True

    def run(self, prompt, model, resolution, translation):
        return _submitted(submit_video("text2video", model, prompt, resolution=resolution,
                                       translation=translation))


class AceVeoImageToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "The scene gently comes to life."}),
            "image_urls": ("STRING", {"multiline": True, "default": ""}),
            "model": (list(STANDARD_MODELS), {"default": "veo31-fast"}),
            "resolution": (list(RESOLUTIONS), {"default": "default"}),
            "aspect_ratio": (list(RATIOS), {"default": "16:9"}),
            "translation": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Animate one public HTTPS image, or use two for first and last frames."
    OUTPUT_NODE = True

    def run(self, prompt, image_urls, model, resolution, aspect_ratio, translation):
        return _submitted(submit_video("image2video", model, prompt, image_urls=image_urls,
                                       resolution=resolution, aspect_ratio=aspect_ratio,
                                       translation=translation))


class AceVeoIngredientsToVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "Blend these references into one cinematic scene."}),
            "image_urls": ("STRING", {"multiline": True, "default": ""}),
            "model": ([MODELS[4]],),
            "resolution": (list(RESOLUTIONS), {"default": "default"}),
            "translation": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Blend 1–3 public HTTPS images with veo31-fast-ingredients."
    OUTPUT_NODE = True

    def run(self, prompt, image_urls, model, resolution, translation):
        return _submitted(submit_video("ingredients2video", model, prompt, image_urls=image_urls,
                                       resolution=resolution, translation=translation))


class AceVeoGet1080p:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_id": ("STRING", {"default": ""}),
            "model": (list(STANDARD_MODELS), {"default": "veo31-fast"}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Use the /veo/videos get1080p action on an existing video ID."
    OUTPUT_NODE = True

    def run(self, video_id, model):
        return _submitted(submit_video("get1080p", model, video_id=video_id))


class AceVeoExtend:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_id": ("STRING", {"default": ""}),
            "model": (list(EXTEND_MODELS), {"default": "veo31-fast"}),
            "prompt": ("STRING", {"multiline": True, "default": ""}),
            "aspect_ratio": (list(RATIOS), {"default": "16:9"}),
            "resolution": (["default", "720p", "1080p"], {"default": "default"}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Extend a supported existing Veo video ID."
    OUTPUT_NODE = True

    def run(self, video_id, model, prompt, aspect_ratio, resolution):
        return _submitted(extend(video_id, model, prompt, aspect_ratio=aspect_ratio, resolution=resolution))


class AceVeoEditObjects:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_id": ("STRING", {"default": ""}),
            "action": (["insert", "remove"], {"default": "insert"}),
            "prompt": ("STRING", {"multiline": True, "default": ""}),
            "image_mask_url": ("STRING", {"default": ""}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Insert or remove an object. Remove requires a public HTTPS mask URL."
    OUTPUT_NODE = True

    def run(self, video_id, action, prompt, image_mask_url):
        return _submitted(edit_objects(video_id, action, prompt, image_mask_url))


class AceVeoReshoot:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_id": ("STRING", {"default": ""}),
            "motion_type": (list(MOTION_TYPES), {"default": "STATIONARY"}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Reshoot a source Veo video with a selected camera movement."
    OUTPUT_NODE = True

    def run(self, video_id, motion_type):
        return _submitted(reshoot(video_id, motion_type))


class AceVeoUpsample:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "video_id": ("STRING", {"default": ""}),
            "action": (list(UPSAMPLE_ACTIONS), {"default": "1080p"}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Upsample an existing Veo video to 1080p, 4k, or GIF."
    OUTPUT_NODE = True

    def run(self, video_id, action):
        return _submitted(upsample(video_id, action))


class AceVeoRetrieve:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "task_id": ("STRING", {"default": ""}),
            "wait_seconds": ("INT", {"default": 240, "min": 0, "max": 240, "step": 5}),
        }}

    RETURN_TYPES = AceVeoTextToVideo.RETURN_TYPES
    RETURN_NAMES = AceVeoTextToVideo.RETURN_NAMES
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Read the same Veo task without another paid submission."
    OUTPUT_NODE = True

    def run(self, task_id, wait_seconds):
        status, task_id, video_url, trace_id = retrieve(task_id, wait_seconds)
        return {"ui": {"text": [f"Veo status: {status}", f"Task ID: {task_id}",
                                "Video is ready" if video_url else "Query this ID again later"]},
                "result": (status, task_id, video_url, trace_id)}


class AceVeoRetrieveBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"task_ids_json": ("STRING", {"multiline": True, "default": "[]"})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("results_json",)
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Read 1–20 existing Veo task IDs without creating new videos."
    OUTPUT_NODE = True

    def run(self, task_ids_json):
        rows = retrieve_batch(task_ids_json)
        return {"ui": {"text": [f"Retrieved {len(rows)} Veo tasks"]},
                "result": (json.dumps(rows),)}


class AceVeoLoadVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"video_url": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "run"
    CATEGORY = AceVeoTextToVideo.CATEGORY
    DESCRIPTION = "Load a completed Ace Data Cloud Veo video into native ComfyUI VIDEO."

    def run(self, video_url):
        if not video_url:
            raise VeoError("Task is still pending. Retrieve the same task ID again.")
        from comfy_api.latest import VideoFromFile

        return (VideoFromFile(BytesIO(download_video(video_url))),)
