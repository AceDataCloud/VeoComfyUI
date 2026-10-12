# Ace Data Cloud 的 ComfyUI Veo 节点

通过 Ace Data Cloud 生成和编辑 Veo 视频，按**同一个任务 ID**查询完成结果，再把视频作为 ComfyUI 原生 `VIDEO` 使用。节点调用云 API，无需本地显卡。收费以[当前 Veo 价格](https://platform.acedata.cloud/models?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_zh_cn_pricing)为准。

[English guide](../README.md)

## 获取 API Key

1. 登录 [Ace Data Cloud → 应用](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_zh_cn_api_key)。新账户没有通用应用时，先选择**初始化通用应用**。
2. 打开**通用应用**，确认已开通本节点使用的服务。单服务应用的 Key 只限该服务。可复制已有 API Key；需要独立 Key 时，选择**管理 Key → 创建**，命名为 `ComfyUI`。
3. 只复制 Token 字符串，不加 `Bearer ` 或引号。平台管理 Token 不能代替节点调用 API 的 Key。若启用**允许的 API**限制，需同时包含工作流用到的提交和任务查询路径；收费动作前核对当前价格与 Credits 余额。

本包覆盖当前 [VeoDify](https://github.com/AceDataCloud/VeoDify) 的 **5 个 model ID 与 7 个工具定义**：文生视频、首尾帧图生视频、多图融合、`get1080p`、延长、物体增删、镜头重拍、清晰度提升、单任务/批量查询。额外的 Load Video 节点把结果接入 ComfyUI `VIDEO`。

## 安装与 Key

Registry 版本激活后，在 **ComfyUI-Manager → Custom Nodes** 搜索 **Veo**，确认发布者 `acedatacloud` 和包名 **Veo by Ace Data Cloud**，安装并重启。Registry ID 为 `veo`，源码为 `AceDataCloud/VeoComfyUI`。本地源码可用不代表市场安装成功。

源码安装：

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/AceDataCloud/VeoComfyUI.git
cd VeoComfyUI
python -m pip install -r requirements.txt
```

要求 ComfyUI 0.39.0 或更新版本。将有 Veo 权限的 Key 放在**实际 ComfyUI 进程环境**的 `ACEDATACLOUD_API_KEY`（也接受 `ACEDATACLOUD_API_TOKEN`），然后重启。不要把 Key 写进工作流、仓库或截图。

## 使用

导入 [01-submit-text-to-video.json](../examples/01-submit-text-to-video.json)，选定模型和价格后只运行一次，记录任务 ID。`veo3`、`veo3-fast`、`veo31`、`veo31-fast` 可用于文生视频或 1–2 张图的首尾帧视频；`veo31-fast-ingredients` 只用于 1–3 张参考图融合。输入公开 HTTPS URL，可用 JSON 数组或每行一条。4k 仅限 Veo 3.1 模型。

延长支持 `veo31-fast` 和 `veo31`。物体增删和镜头重拍要求原视频 ID，不能用延长结果；移除物体需要公开 HTTPS 蒙版 URL。`get1080p`、Upsample 使用已有视频 ID，不能填视频 URL。

导入 [02-retrieve-and-save.json](../examples/02-retrieve-and-save.json)，填入**同一个任务 ID**，运行 **Retrieve Task → Load Video → Save Video**。240 秒后仍 pending 时，只重跑查询工作流。批量查询节点可查询 1–20 个已有 ID。

提交超时或 HTTP 5xx 时，先到 [Ace Data Cloud 控制台](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veocomfyui_readme_zh_cn_api_key)按任务或 Trace ID 核对是否受理，再决定是否重新收费提交。详见[隐私说明](PRIVACY.md)。
