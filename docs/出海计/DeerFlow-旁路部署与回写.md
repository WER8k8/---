# DeerFlow 2.0 旁路部署与回写

本系统默认使用进程内 **DeerFlow Lite**（`deerflow_research_service`）。生产可旁路官方/自建 DeerFlow 2.0，研究完成后仍通过同一飞轮钩子入队 Accio。

## 1. 环境变量

| 变量 | 说明 |
|------|------|
| `DEERFLOW_VERSION` | 版本标识，`2.0` 启用 2.0 模式 |
| `DEERFLOW_SIDECAR_URL` | 旁路服务根 URL，如 `https://deerflow.internal:8002` |
| `DEERFLOW_SIDECAR_SECRET` | 可选 Bearer，请求头 `Authorization` |
| `DEERFLOW_GATEWAY_URL` | DeerFlow 2.0 Gateway API 地址，如 `http://localhost:8001` |
| `DEERFLOW_LANGGRAPH_URL` | DeerFlow 2.0 LangGraph Server 地址，如 `http://localhost:2024` |

未配置时：`market_research` 仅走本机 Lite，行为与现网单测一致。

## 2. DeerFlow 2.0 架构

DeerFlow 2.0 是字节跳动开源的超级智能体框架，基于 LangGraph + LangChain 构建。

| 组件 | 端口 | 说明 |
|------|------|------|
| Gateway API | 8001 | REST API 网关，前端交互入口 |
| LangGraph Server | 2024 | Agent 运行时引擎，线程状态管理 |
| Nginx | 2026 | 统一访问入口，请求路由 |

核心特性：
- **子 Agent 编排**：Lead Agent 动态派生子 Agent 并行执行
- **Docker 沙箱**：每个任务运行在独立容器中，安全隔离
- **Markdown Skills**：可扩展的技能系统，按需加载
- **长期记忆**：跨会话持久化记忆

## 3. 旁路契约（建议）

### 3.1 DeerFlow 2.0 Gateway API

旁路服务提供其一：

| 方法 | 路径 | Body |
|------|------|------|
| POST | `/v1/chat` | `{"tenant_id":"<uuid>","message":"...","skill":"deep-search","mode":"ultra"}` |
| POST | `/v1/research` | `{"tenant_id":"<uuid>","message":"..."}` |
| POST | `/threads` | `{"configurable":{"tenant_id":"<uuid>"}}` |
| POST | `/threads/{thread_id}/runs` | `{"input":{"message":"..."},"configurable":{"tenant_id":"<uuid>"}}` |

### 3.2 响应格式

响应 JSON（或 `{ "data": { ... } }` 包装）需含：

- `research_brief` 和/或 `accio_actions`（≥2 条更佳）
- 可选 `executive_summary`、`category`、`skill`、`execution_mode`

本系统 `run_market_research_v2` 命中旁路后标记 `mode: deerflow_sidecar_v2`。

## 4. 回写飞轮（无需旁路改代码）

**方式 A — 本系统队列（推荐联调）**

1. 副驾或 API 入队 `POST /api/v1/ubrain/chat` → `market_research`（async）
2. `POST /api/v1/ubrain/jobs/run-pending` 消费任务  
3. 成功 → `on_deerflow_job_finished` → 洞察 + 编排

**方式 B — n8n / 旁路直接 webhook**

旁路 DeerFlow 完成后 POST：

`POST /api/v1/ubrain/commercial-os/webhook`  
Header: `X-N8N-Webhook-Secret`  
Body: 见 `docs/出海计/examples/n8n-deerflow-done.json`

## 5. 健康检查

```text
GET /api/v1/ubrain/commercial-os/deerflow-sidecar
```

返回 `configured`、`healthy`、`version`、`is_v2`、`fallback`。

## 6. 部署拓扑（示意）

```text
[租户副驾] → [FastAPI 本系统]
                 ├─ DEERFLOW_VERSION=2.0 → 2.0 模式
                 │   ├─ DEERFLOW_GATEWAY_URL 已设 → Gateway API
                 │   └─ DEERFLOW_LANGGRAPH_URL 已设 → LangGraph Server
                 ├─ DEERFLOW_SIDECAR_URL 已设且 healthy → HTTP 旁路研究
                 └─ 未配置 → Lite 研究
                 → deerflow_jobs / commercial_os_hook
                 → Accio 找客 / 开发信队列
```

## 7. cron 建议

```powershell
# 租户 JWT 或内部服务账号
$env:SMOKE_TOKEN = "..."
powershell -File scripts/cron-deerflow-jobs.ps1
```

## 8. 验收

1. 未配置旁路：`pytest tests/unit/test_commercial_os_flywheel.py` 全绿  
2. 配置旁路 mock：`tests/unit/test_swarm_round7_deerflow_sidecar.py`  
3. D2–D6 API：`tests/unit/test_flywheel_d2_d6_api.py`  
4. 2.0 模式验证：检查 `is_v2: true` 和版本信息