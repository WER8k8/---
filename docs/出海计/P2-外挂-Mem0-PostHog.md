# P2 外挂 · Mem0 与 PostHog

## Mem0 双写

| 环境变量 | 说明 |
|----------|------|
| `MEM0_API_URL` | Mem0 服务根 URL（如 `https://api.mem0.ai` 或自托管） |
| `MEM0_API_KEY` | 可选 Bearer |

**触发**：每次 `extract_insight_from_deerflow` 本地落库后，异步风格 HTTP POST（失败不阻断主流程）。

**状态**：`GET /api/v1/ubrain/commercial-os/integrations` → `mem0.configured`

## PostHog 埋点

| 环境变量 | 说明 |
|----------|------|
| `POSTHOG_PROJECT_API_KEY` 或 `POSTHOG_API_KEY` | 项目 API Key |
| `POSTHOG_HOST` | 默认 `https://us.i.posthog.com` |

**事件**：

| event | 时机 |
|-------|------|
| `flywheel_feedback_sync` | `feedback/sync` 完成 |
| `flywheel_deerflow_job_success` | DeerFlow 任务成功且飞轮钩子执行后 |

**状态**：`integrations.posthog.configured`

## 副驾 / 运维

- 飞轮 `GET .../commercial-os/status` 含 `integrations` 对象  
- 未配置时均为 no-op，不影响 P0 单测与副驾主路径  

## 验收

```powershell
$env:MEM0_API_URL = "https://your-mem0"
$env:POSTHOG_PROJECT_API_KEY = "phc_xxx"
# 跑一轮飞轮或 feedback/sync 后检查 Mem0 控制台 / PostHog Live events
```

单测：`tests/unit/test_swarm_round6_integrations.py`（mock HTTP，无真实外网）
