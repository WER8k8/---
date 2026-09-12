# DeerFlow 2.0 旁路部署（DF-12）

## 环境变量

```env
DEERFLOW_VERSION=2.0
DEERFLOW_SIDECAR_URL=https://your-deerflow-host:8002
DEERFLOW_SIDECAR_SECRET=shared-secret
DEERFLOW_GATEWAY_URL=https://your-deerflow-host:8001
DEERFLOW_LANGGRAPH_URL=https://your-deerflow-host:2024
```

## DeerFlow 2.0 架构

DeerFlow 2.0 是字节跳动开源的超级智能体框架，基于 LangGraph + LangChain 构建。

| 组件 | 端口 | 说明 |
|------|------|------|
| Gateway API | 8001 | REST API 网关 |
| LangGraph Server | 2024 | Agent 运行时引擎 |
| Nginx | 2026 | 统一访问入口 |

核心特性：子 Agent 编排、Docker 沙箱、Markdown Skills、长期记忆

## 健康检查

司令部 **集成栈** 卡片或：

```bash
curl -s http://127.0.0.1:8001/api/v1/hermes/ops/command-center \
  -H "Authorization: Bearer $TOKEN" | jq .data.integrations.deerflow_sidecar
```

响应示例：
```json
{
  "configured": true,
  "url": "http://localhost:8002",
  "version": "2.0",
  "is_v2": true,
  "healthy": true,
  "health_path": "/health",
  "version_info": "2.0.0",
  "services": {
    "gateway": "running",
    "langgraph": "running",
    "sandbox": "ready",
    "memory": "active"
  }
}
```

旁路会探测 `/health`、`/api/health`、`/v1/health`、`/api/v1/health`；失败时自动回退本机 `deerflow_lite`。

## 研究请求

### Gateway API

`POST {GATEWAY_URL}/v1/chat` · body: 
```json
{
  "tenant_id": "xxx",
  "message": "研究保温建材出口市场",
  "skill": "deep-search",
  "mode": "ultra"
}
```

### 传统接口（兼容）

`POST {SIDECAR_URL}/v1/research` · body: `{ "tenant_id", "message" }`

## 验收

1. `healthy: true`  
2. `is_v2: true`  
3. 租户触发 `market_research` 任务，`result.mode` 含 `deerflow_sidecar_v2`  
4. 旁路不可用时 Lite 版仍成功（无 5xx）