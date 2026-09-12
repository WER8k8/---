# 视频矩阵 Worker 生产部署清单（VID-05）

每平台至少配置 **一种** Worker 后，`preflight_workers()` 返回 `ready=true`。

## 环境变量（`deploy/production/env.template`）

| 平台 | 变量 | 说明 |
|------|------|------|
| 抖音/多平台 SAU | `PUBLISH_SAU_ENABLED=true` + SAU 相关 token | 社媒自动上传 |
| B 站 | `PUBLISH_BILIUP_ENABLED=true` + cookie | biliup CLI |
| 小红书 | `PUBLISH_XHS_MCP_URL` | MCP 端点 |
| AiToEarn | `PUBLISH_AITO_EARN_ENABLED=true` | 第三方矩阵 |

## 验证

```powershell
# API 预检
curl http://127.0.0.1:8001/api/v1/hermes/ops/command-center -H "Authorization: Bearer ..."

# 或巡站 probe video_workers
curl -X POST http://127.0.0.1:8001/api/v1/hermes/ops/instruct -d '{"command":"patrol"}'
```

## 人审门（VID-06）

`matrix_publish` / `video_matrix_v1` 默认 `needs_confirmation`；真发须 `human_confirmed=true` + `media_task_id`。

## 文档

- `docs/MEDIA-FACTORY-CLOUD-STORAGE.md`
- 司令部 → 视频 Worker 卡片
