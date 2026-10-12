# Veo for ComfyUI by Ace Data Cloud

Generate and edit Veo videos with your Ace Data Cloud account, retrieve the **same task ID**, and load completed results as ComfyUI's native `VIDEO` type. These nodes call a hosted API; no local model or GPU is needed. Paid actions consume Credits at the [current Veo price](https://platform.acedata.cloud/models?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_en_pricing).

[简体中文](docs/README.zh-CN.md) · [Ace Data Cloud](https://platform.acedata.cloud?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_en_home) · [Issues](https://github.com/AceDataCloud/VeoComfyUI/issues)

| Nodes | Dify API action |
| --- | --- |
| **Text to Video / Image to Video / Ingredients to Video / Get 1080p** | `/veo/videos` actions `text2video`, `image2video`, `ingredients2video`, `get1080p` |
| **Extend Video** | `/veo/extend` |
| **Edit Objects** | `/veo/objects`, insert or remove |
| **Reshoot Video** | `/veo/reshoot`, 15 camera motion choices |
| **Upsample Video** | `/veo/upsample`, 1080p, 4k, or GIF |
| **Retrieve Task / Retrieve Tasks / Load Video** | Read existing IDs and decode an Ace media URL to `VIDEO` |

These nodes cover all **five model IDs** and seven tool definitions in the current [VeoDify](https://github.com/AceDataCloud/VeoDify) package. `veo3`, `veo3-fast`, `veo31`, and `veo31-fast` are available for text or first/last-frame image input. `veo31-fast-ingredients` requires 1–3 reference images. Extend accepts only `veo31-fast` and `veo31`. Availability, quality, resolution, and price vary by model.

## Install

Once the Registry version is active, open **ComfyUI-Manager → Custom Nodes**, search **Veo**, confirm publisher **acedatacloud** and package **Veo by Ace Data Cloud**, install, and restart. The Registry ID is `veo`; source is `AceDataCloud/VeoComfyUI`. Source availability and Registry upload alone do not prove Manager installation.

For local source testing:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/AceDataCloud/VeoComfyUI.git
cd VeoComfyUI
python -m pip install -r requirements.txt
```

This package targets ComfyUI 0.39.0 or newer because Load Video uses its native `VIDEO` type. Restart and search for **Veo**.

## Set your Ace Data Cloud key

1. Sign in to [Ace Data Cloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_en_api_key). If your account has no General application, choose **Initialize General Application**.
2. Open **General application** and check access to the service used by this package. A service-specific application key is limited to that service. Copy an existing API key, or choose **Manage Keys → Create** for a separate key named `ComfyUI`.
3. Copy only the token string, without `Bearer ` or quotation marks. A platform management token is not the API key these nodes use. If you enable **Allowed APIs**, include every submission and task-query path used by your workflow. Check current pricing and available Credits before a paid action.

Set a key with Veo access in the **actual ComfyUI process environment**, then restart:

```bash
export ACEDATACLOUD_API_KEY='paste-your-key-here'
python main.py --cpu
```

`ACEDATACLOUD_API_TOKEN` is also accepted. Keep the key out of workflows, screenshots, issues, and the repository. If you restrict API paths, allow `/veo/videos`, `/veo/extend`, `/veo/objects`, `/veo/reshoot`, `/veo/upsample`, and `/veo/tasks`.

## Generate and retrieve

Import [01-submit-text-to-video.json](examples/01-submit-text-to-video.json) with **File → Open**, choose a model and price, then run it **once**. Copy the task ID shown by Preview as Text. A submitted task is not a completed video. If submission times out without an ID, inspect Ace request history before paying again.

Image to Video accepts one public HTTPS URL for the first frame or two for first and last frames. Ingredients to Video accepts 1–3 public HTTPS URLs and only `veo31-fast-ingredients`. Enter a JSON array or one URL per line. The 4k choice is limited to Veo 3.1 models. `aspect_ratio` applies only to Image to Video. `get1080p` and Upsample take an existing **video ID**, not a URL.

Extend takes a supported original or extend result video ID. Edit Objects and Reshoot require an original Veo video ID; an extended result is not supported. Object removal requires a public HTTPS mask URL. The API also accepts base64 masks, but this UI keeps large mask data out of workflows. All paid nodes submit once and never retry automatically.

Import [02-retrieve-and-save.json](examples/02-retrieve-and-save.json), replace its placeholder task ID, and run. It connects **Retrieve Task → Load Video → Save Video**. Retrieve waits up to 240 seconds for the **same task**. If still pending, rerun only this retrieval workflow. The native `VIDEO` output also connects to other ComfyUI video nodes. Retrieve Tasks accepts a JSON array of 1–20 existing IDs and does not create a new video.

## Check usage and troubleshoot

Find the submission by task or trace ID in the [Ace Data Cloud Console](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_en_api_key). Read-only task queries and media downloads should not create another generation.

| Symptom | Action |
| --- | --- |
| Key missing or HTTP 401/403 | Check the key in the running ComfyUI process and Veo access. |
| HTTP 429 | Wait for the service limit; keep any accepted task ID. |
| Pending | Query the same task ID again; do not rerun a paid node. |
| Submission timeout or HTTP 5xx | Inspect request history before resubmitting. |
| Video download error | Confirm terminal success and an Ace CDN URL. |

Prompts and reference URLs are sent to `api.acedata.cloud`; completed videos are downloaded from Ace CDN. See [privacy notes](docs/PRIVACY.md). Only submit content you have permission to process.

## Development

```bash
python -m unittest discover -s tests -v
python -m py_compile __init__.py client.py nodes.py
```

`pyproject.toml` declares short Registry ID `veo`, publisher `acedatacloud`, and a 400×400 proportional resize of the [canonical Ace logo](https://cdn.acedata.cloud/assets/logo.png).
