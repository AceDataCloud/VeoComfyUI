"""Fixed-host Veo API client. Paid submissions are never retried."""

from __future__ import annotations

import ipaddress
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import requests

BASE_URL = "https://api.acedata.cloud"
VIDEO_HOSTS = {"cdn.acedata.cloud", "cdn.acedata2.cloud", "platform.cdn.acedata.cloud",
               "platform2.cdn.acedata.cloud"}
MAX_VIDEO_BYTES = 128 * 1024 * 1024
COMPLETE = {"complete", "completed", "succeed", "succeeded", "success", "finished"}
FAILED = {"failed", "error", "cancelled", "canceled", "rejected"}
MODELS = ("veo3", "veo3-fast", "veo31", "veo31-fast", "veo31-fast-ingredients")
STANDARD_MODELS = MODELS[:4]
EXTEND_MODELS = ("veo31-fast", "veo31")
RESOLUTIONS = ("default", "1080p", "4k", "gif")
RATIOS = ("16:9", "9:16")
UPSAMPLE_ACTIONS = ("1080p", "4k", "gif")
MOTION_TYPES = (
    "STATIONARY", "STATIONARY_UP", "STATIONARY_DOWN", "STATIONARY_LEFT", "STATIONARY_RIGHT",
    "STATIONARY_DOLLY_IN_ZOOM_OUT", "STATIONARY_DOLLY_OUT_ZOOM_IN", "UP", "DOWN",
    "LEFT_TO_RIGHT", "RIGHT_TO_LEFT", "FORWARD", "BACKWARD", "DOLLY_IN_ZOOM_OUT",
    "DOLLY_OUT_ZOOM_IN",
)


class VeoError(RuntimeError):
    """A customer-safe error without raw API data or credentials."""


def _credential() -> str:
    token = os.environ.get("ACEDATACLOUD_API_KEY") or os.environ.get("ACEDATACLOUD_API_TOKEN")
    if not token or not token.strip():
        raise VeoError("Set ACEDATACLOUD_API_KEY in the ComfyUI process environment and restart.")
    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise VeoError("Ace Data Cloud API key is empty.")
    return token


def _post(path: str, payload: dict[str, Any], *, read_only: bool = False) -> dict[str, Any]:
    token = _credential()
    for attempt in range(3 if read_only else 1):
        try:
            response = requests.post(
                BASE_URL + path, json=payload,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=(10, 60 if read_only else 45), allow_redirects=False,
            )
            break
        except requests.RequestException as exc:
            if read_only and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise VeoError(
                f"Veo {'query' if read_only else 'submission'} connection failed "
                f"({type(exc).__name__}). Inspect request history before another paid submission."
            ) from None
    if not 200 <= response.status_code < 300:
        raise VeoError(
            f"Ace Data Cloud returned HTTP {response.status_code}. Check access, balance, and request history."
        )
    try:
        body = response.json()
    except ValueError:
        raise VeoError("Ace Data Cloud returned invalid JSON.") from None
    if not isinstance(body, dict):
        raise VeoError("Ace Data Cloud returned an unexpected response.")
    if body.get("success") is False or body.get("error"):
        raise VeoError("Veo reported an error. Inspect its task or trace ID.")
    return body


def public_https(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("Reference media must use public HTTPS URLs.")
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("Reference media must use public HTTPS URLs.")
    if host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith(".local"):
        raise ValueError("Reference media must use public HTTPS URLs.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Reference media must use public HTTPS URLs.")
    return url


def parse_urls(value: str, *, maximum: int, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        if allow_empty:
            return []
        raise ValueError("Reference image URLs are required.")
    raw = value.strip()
    if raw.startswith("["):
        try:
            urls = json.loads(raw)
        except ValueError:
            raise ValueError("Reference images must be a JSON URL array or one URL per line.") from None
    else:
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(urls, list) or not all(isinstance(item, str) for item in urls):
        raise ValueError("Reference images must be a JSON URL array or one URL per line.")
    urls = list(dict.fromkeys(public_https(item) for item in urls))
    if len(urls) > maximum or (not allow_empty and not urls):
        raise ValueError(f"Use {'0–' if allow_empty else '1–'}{maximum} reference images.")
    return urls


def _result(body: dict[str, Any], *, retrieved: bool) -> Any:
    result: Any = body.get("response", body) if retrieved else body
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            result = {}
    return result or {}


def _video_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"request", "request_body", "input", "prompt"}:
                    continue
                if key == "video_url" and isinstance(child, str) and child.startswith("https://"):
                    urls.append(child)
                elif isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return list(dict.fromkeys(urls))


def _states(value: Any) -> tuple[list[str], bool]:
    states: list[str] = []
    failed = False

    def walk(item: Any) -> None:
        nonlocal failed
        if isinstance(item, dict):
            if item.get("success") is False or item.get("error"):
                failed = True
            for key, child in item.items():
                if key in {"state", "status"} and isinstance(child, str):
                    states.append(child.lower())
                elif key in {"data", "content", "task"}:
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return states, failed


def normalize(body: dict[str, Any], task_id: str = "", *, retrieved: bool = False) -> tuple[str, str, str, str]:
    result = _result(body, retrieved=retrieved)
    inner = result if isinstance(result, dict) else {}
    task_id = str(task_id or body.get("task_id") or inner.get("task_id") or body.get("id") or "")
    trace_id = str(inner.get("trace_id") or body.get("trace_id") or "")
    states, failed = _states(result)
    urls = _video_urls(result)
    unfinished = retrieved and "finished_at" in body and body["finished_at"] is None
    if (failed or any(state in FAILED for state in states)) and not unfinished:
        raise VeoError("Veo task failed. Inspect its task or trace ID.")
    done = not unfinished and ((states and all(state in COMPLETE for state in states)) or
                               (retrieved and body.get("finished_at")) or (urls and not states))
    if done:
        if not urls:
            raise VeoError("Veo task finished without a video URL.")
        return "succeeded", task_id, urls[0], trace_id
    if task_id:
        return "pending", task_id, "", trace_id
    raise VeoError("No task ID or completed video was returned. Inspect request history before resubmitting.")


def _video_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("An existing Veo video ID is required; do not enter a URL.")
    return value.strip()


def submit_video(action: str, model: str, prompt: str = "", *, image_urls: str = "",
                 video_id: str = "", resolution: str = "default", aspect_ratio: str = "16:9",
                 translation: bool = False) -> tuple[str, str, str, str]:
    if action not in {"text2video", "image2video", "ingredients2video", "get1080p"}:
        raise ValueError("Unsupported Veo video action.")
    if model not in MODELS or resolution not in RESOLUTIONS or aspect_ratio not in RATIOS:
        raise ValueError("Unsupported Veo model, resolution, or aspect ratio.")
    if resolution == "4k" and not model.startswith("veo31"):
        raise ValueError("4k is available only with Veo 3.1 models.")
    payload: dict[str, Any] = {"action": action, "model": model, "async": True}
    if action == "get1080p":
        if model not in STANDARD_MODELS:
            raise ValueError("Ingredients model cannot upscale a prior video.")
        payload["video_id"] = _video_id(video_id)
    else:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A Veo prompt is required.")
        payload["prompt"] = prompt.strip()
        payload["translation"] = bool(translation)
        if resolution != "default":
            payload["resolution"] = resolution
        if action == "text2video":
            if model not in STANDARD_MODELS:
                raise ValueError("Ingredients model requires image references.")
        elif action == "image2video":
            if model not in STANDARD_MODELS:
                raise ValueError("Use Ingredients to Video for the ingredients model.")
            payload["image_urls"] = parse_urls(image_urls, maximum=2)
            payload["aspect_ratio"] = aspect_ratio
        else:
            if model != "veo31-fast-ingredients":
                raise ValueError("Ingredients to Video requires veo31-fast-ingredients.")
            payload["image_urls"] = parse_urls(image_urls, maximum=3)
    return normalize(_post("/veo/videos", payload))


def extend(video_id: str, model: str, prompt: str = "", *, aspect_ratio: str = "16:9",
           resolution: str = "default") -> tuple[str, str, str, str]:
    if model not in EXTEND_MODELS or aspect_ratio not in RATIOS or resolution not in {"default", "720p", "1080p"}:
        raise ValueError("Unsupported Veo extend option.")
    payload: dict[str, Any] = {"video_id": _video_id(video_id), "model": model, "async": True}
    if prompt.strip():
        payload["prompt"] = prompt.strip()
    if aspect_ratio != "16:9":
        payload["aspect_ratio"] = aspect_ratio
    if resolution != "default":
        payload["resolution"] = resolution
    return normalize(_post("/veo/extend", payload))


def edit_objects(video_id: str, action: str, prompt: str = "", image_mask: str = "") -> tuple[str, str, str, str]:
    if action not in {"insert", "remove"}:
        raise ValueError("Object action must be insert or remove.")
    if action == "insert" and not prompt.strip():
        raise ValueError("An insertion prompt is required.")
    if action == "remove" and not image_mask.strip():
        raise ValueError("A public HTTPS mask URL is required for removal.")
    payload: dict[str, Any] = {"video_id": _video_id(video_id), "action": action, "async": True}
    if prompt.strip():
        payload["prompt"] = prompt.strip()
    if image_mask.strip():
        payload["image_mask"] = public_https(image_mask)
    return normalize(_post("/veo/objects", payload))


def reshoot(video_id: str, motion_type: str) -> tuple[str, str, str, str]:
    if motion_type not in MOTION_TYPES:
        raise ValueError("Unsupported Veo motion type.")
    return normalize(_post("/veo/reshoot", {"video_id": _video_id(video_id),
                                           "motion_type": motion_type, "async": True}))


def upsample(video_id: str, action: str) -> tuple[str, str, str, str]:
    if action not in UPSAMPLE_ACTIONS:
        raise ValueError("Unsupported Veo upsample action.")
    return normalize(_post("/veo/upsample", {"video_id": _video_id(video_id),
                                            "action": action, "async": True}))


def retrieve_once(task_id: str) -> tuple[str, str, str, str]:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("A Veo task ID is required.")
    task_id = task_id.strip()
    return normalize(_post("/veo/tasks", {"action": "retrieve", "id": task_id}, read_only=True),
                     task_id, retrieved=True)


def retrieve(task_id: str, wait_seconds: int) -> tuple[str, str, str, str]:
    if not isinstance(wait_seconds, int) or not 0 <= wait_seconds <= 240:
        raise ValueError("Wait seconds must be 0–240.")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = retrieve_once(task_id)
        if result[0] != "pending" or time.monotonic() >= deadline:
            return result
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def retrieve_batch(task_ids_json: str) -> list[dict[str, str]]:
    try:
        ids = json.loads(task_ids_json)
    except (TypeError, ValueError):
        raise ValueError("Task IDs must be a JSON array.") from None
    if not isinstance(ids, list) or not ids or len(ids) > 20 or not all(isinstance(i, str) and i.strip() for i in ids):
        raise ValueError("Use 1–20 nonempty task IDs.")
    body = _post("/veo/tasks", {"action": "retrieve_batch", "ids": ids}, read_only=True)
    items = body.get("items") or body.get("data") or []
    if not isinstance(items, list):
        raise VeoError("Veo returned an unexpected batch response.")
    rows: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or item.get("task_id") or "")
        try:
            status, _, video_url, trace_id = normalize(item, item_id, retrieved=True)
        except VeoError:
            status, video_url, trace_id = "failed", "", ""
        rows.append({"task_id": item_id, "status": status, "video_url": video_url, "trace_id": trace_id})
    return rows


def download_video(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in VIDEO_HOSTS or parsed.username or parsed.password:
        raise VeoError("Video URL must be an Ace Data Cloud HTTPS media link.")
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(10, 90), allow_redirects=False) as response:
                if response.status_code != 200:
                    raise VeoError(f"Video download returned HTTP {response.status_code}.")
                claimed = int(response.headers.get("Content-Length", "0"))
                if claimed > MAX_VIDEO_BYTES:
                    raise VeoError("Video exceeds the 128 MiB limit.")
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_VIDEO_BYTES:
                        raise VeoError("Video exceeds the 128 MiB limit.")
                    chunks.append(chunk)
            if not size:
                raise VeoError("Video download was empty.")
            return b"".join(chunks)
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise VeoError(f"Video download failed ({type(exc).__name__}).") from None
    raise AssertionError("unreachable")
