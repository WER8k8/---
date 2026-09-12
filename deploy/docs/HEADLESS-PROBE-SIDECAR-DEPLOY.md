# Headless 排名探针 Sidecar（P1）

增长工具中 `headless_exploration` 通道（搜狗、Kimi、Perplexity 等）需 **Playwright / Browser Use** 外置 Worker。主站只发起探针、存快照，**不伪造排名**。

## 环境变量

```env
HEADLESS_PROBE_SIDECAR_URL=https://your-headless-worker
HEADLESS_PROBE_SIDECAR_TOKEN=shared-secret
# 仅本地开发无 Sidecar 时允许 stub（响应 probe_mode=stub，不得当生产终态）
HEADLESS_PROBE_ALLOW_STUB=0
```

## Sidecar HTTP 契约

`POST /v1/headless-probe`

```json
{
  "engine_id": "kimi",
  "keyword": "保温建材",
  "target_url": "https://www.example.com"
}
```

响应示例：

```json
{
  "engine_id": "kimi",
  "keyword": "保温建材",
  "found": true,
  "rank_hint": 3,
  "cited_url": "https://www.example.com/page",
  "evidence_snippet": "...",
  "probe_mode": "headless"
}
```

## 主站 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/growth-tools/ai-traffic/headless-status` | Sidecar 就绪态 |
| POST | `/api/v1/growth-tools/ai-traffic/headless-probe` | 触发 batch（最多 8 引擎） |
| GET | `/api/v1/growth-tools/ai-traffic/overview` | 合并最近快照到 platform_cards |

未配置 Sidecar 且非 development → `503 HEADLESS_PROBE_NOT_CONFIGURED`

## 验收

```powershell
curl -X POST http://127.0.0.1:8001/api/v1/growth-tools/ai-traffic/headless-probe `
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" `
  -d '{"keyword":"test","target_url":"https://example.com","limit":3}'
```
