# 赚钱闭环 · 开源学习专章（ARCH-04）

只抄 **契约与编排**，不整库 fork。

| 项目 | 抄什么 | 不抄什么 | 本仓库落点 |
|------|--------|----------|------------|
| **DeerFlow** | Research Brief JSON、`accio_actions` | 全量 Agent 运行时 | `deerflow_research_service` · sidecar URL |
| **n8n** | Webhook 事件形状 | 自托管 UI 逻辑 | `POST /ubrain/commercial-os/webhook` · `deploy/examples/n8n/` |
| **Mem0** | 洞察双写 API | 向量库 schema | `flywheel_integrations.sync_insight_to_mem0` |
| **PostHog** | `capture` 事件 | 前端 SDK 全量 | `capture_posthog_event` 服务端 |
| **Accio** | 工作台 + 确认门 + 步骤卡 | 国际站私有 API | `copilot.vue` · `commercial_os_bridge` |

## 集成原则

1. 租户只见「市场研究 / 获客执行 / 卖货飞轮」  
2. Hermes 只做运维与编排，不替租户自动外发  
3. 所有外挂未配置时 **no-op**，核心飞轮仍可跑 Lite 版

## 参考路径

- 架构：`docs/HERMES-FLYWHEEL-ARCHITECTURE-v1.md`  
- 写库边界：`docs/HERMES-FLYWHEEL-WRITE-CONSTITUTION.md`  
- n8n 示例：`deploy/examples/n8n/`
