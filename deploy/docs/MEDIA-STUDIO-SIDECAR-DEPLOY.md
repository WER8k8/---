# 全媒体工作室 · Sidecar 与真实出海部署

## 内置真实链（默认，无需 sidecar）

满足以下条件即自动激活 `youding_self_hosted`：

- `ffmpeg` 在 PATH
- `edge-tts` 可用（`pip install edge-tts`）
- 听写：讯飞密钥 **或** 本机 `faster-whisper`

租户路径：`/client/video-overseas` → **一键出海** 或 **真实英文配音**。

## 真实 sidecar（可选，与内置链二选一或并存）

```powershell
# 终端 1：真实 sidecar（mode=production，禁止用 reference mock）
cd backend
.\.venv\Scripts\python.exe ..\scripts\youding-sidecar-real.py --port 9901

# backend .env
YOUDUB_WEBUI_BASE_URL=http://127.0.0.1:9901
CROSS_BORDER_PUBLIC_BASE_URL=http://127.0.0.1:8001
```

健康探测：`GET /api/youding/health` 须返回 `mode=production` 且 `produces_output=true`。  
`youding-sidecar-reference.py` 为 **mock**，backend **不会**计为已配置。

## GPU 口型精品（Linly / v2vt / 官方 YouDub）

须单独部署上游仓库，并封装为统一契约（见 `.project/opensource-sidecar-contract.json`）。  
未通过健康探测前，精品按钮不会出现，禁止假成片。

## Web 剪辑器嵌入

```env
FLY_CUT_EMBED_URL=http://127.0.0.1:5174
OPENCUT_EMBED_URL=http://127.0.0.1:5175
```

握手参数（Query）：`media_task_id`、`video_url`、`srt_url`、`script_en`。  
未配置 embed URL 时，剪辑器页仍展示 **优丁内置预览**（真实 mp4 + SRT 下载）。

## E2E 验收

```powershell
powershell -File scripts/start-dev-admin.ps1
cd backend
.\.venv\Scripts\python.exe ..\scripts\e2e_cross_border_overseas_flow.py
```

产物 handoff：`/client/distribute?media_task_id=<uuid>`。

## 诚实门禁

- 听写失败 → 报错，不生成占位中文稿
- sidecar 无 `output_url` 且无 `srt_url` → `SIDECAR_NO_OUTPUT`
- mock sidecar → `configured=false`
