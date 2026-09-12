# AI Hunter 找客 Sidecar（P1）

主站 **不** 内置 Google/B2B/Maps 深度爬虫。部署 [AI_Find_Customer](https://github.com/xiongQvQ/AI_Find_Customer) 或兼容 HTTP 服务后，由 Accio `find_buyers` / Admin「客户开发」优先调用。

## 环境变量（backend `.env` 或 `backend/config/dev/.env`）

```env
AI_FIND_CUSTOMER_URL=https://your-ai-hunter-host
AI_FIND_CUSTOMER_TOKEN=shared-secret
```

可选：若上游只有原生 Hunt API，可部署本仓薄适配层，主站仍指向适配层 URL：

```env
AI_FIND_CUSTOMER_URL=http://127.0.0.1:8092
AI_FIND_CUSTOMER_TOKEN=dev-sidecar-token
AI_HUNTER_UPSTREAM_URL=http://127.0.0.1:8080
```

## Sidecar HTTP 契约（优丁标准）

### 健康检查

`GET /health` 或 `/v1/health` 或 `/api/v1/health` → HTTP 200

### 找客（同步）

`POST /v1/find-prospects`

```json
{
  "tenant_id": "uuid",
  "query": "中东 保温建材 分销商",
  "region": "中东",
  "category": "保温建材",
  "count": 8
}
```

响应（每条 **必须** 含 `evidence_url`，否则主站丢弃）：

```json
{
  "prospects": [
    {
      "title": "Example Distributor",
      "company": "Example Co",
      "country_code": "AE",
      "email": "buyer@example.com",
      "evidence_url": "https://example.com/about",
      "confidence": 0.82,
      "source": "google"
    }
  ]
}
```

## 上游 AI_Find_Customer 原生 API（主站已自动兼容）

若 `AI_FIND_CUSTOMER_URL` 直接指向上游 FastAPI（默认前缀 `/api/v1`），主站会在 `/v1/find-prospects` 失败后自动：

1. `POST /api/v1/hunts`
2. 轮询 `GET /api/v1/hunts/{id}/status`
3. 读取 `GET /api/v1/hunts/{id}/result` 中的 `leads[]`
4. 将 `lead.website` 映射为 `evidence_url`

**禁止**自动 SMTP/WhatsApp 群发；`enable_email_craft` 始终为 false。

## 薄适配层（推荐 dev/staging）

路径：`deploy/examples/ai-find-customer-sidecar/`

### 开发一键（无真实上游时）

```powershell
# 启动 mock 上游 :8080 + 适配层 :8092，并写入 backend/config/dev/.env
powershell -File scripts/start-ai-find-customer-dev.ps1

# 重启 backend 加载 env
powershell -File scripts/start-dev-admin.ps1 -ForceRestart

# 验收
cd backend
.\.venv\Scripts\python.exe ..\scripts\verify-ai-find-customer-sidecar.py --smoke-find
```

Mock 上游：`deploy/examples/ai-hunter-upstream-mock/`（响应 `mode=mock` + `probe_mode=stub`，诚实非实盘）。

### 真实上游（O-4）

```powershell
# 一键：clone → 上游 :8080 → 适配层 :8092 → backend .env (ALLOW_DEV_STUB=0)
powershell -File scripts/run-o4-b2b-upstream-wire.ps1

# 已手动 clone 时
powershell -File scripts/run-o4-b2b-upstream-wire.ps1 -SkipClone -UpstreamRoot D:\refs\AI_Find_Customer

# 验收（须真实上游 + API keys；mock 会诚实 FAIL）
cd backend
.\.venv\Scripts\python.exe ..\scripts\validate-o4-b2b-upstream-wire.py
```

上游 README：`uvicorn api.app:app --host 127.0.0.1 --port 8080`（在 `deploy/upstreams/AI_Find_Customer/backend`）  
必填：`backend/.env` 内 `MINIMAX_API_KEY`、`TAVILY_API_KEY`、`SERPER_API_KEY`（见上游 `.env.example`）。

### 手动 / 真实上游

```powershell
# 终端 1：上游 AI Hunter（clone xiongQvQ/AI_Find_Customer 后按其 README 启动 backend）
# 终端 2：适配层
$env:AI_HUNTER_UPSTREAM_URL='http://127.0.0.1:8080'
$env:AI_FIND_CUSTOMER_TOKEN='dev-sidecar-token'
python scripts/ai-find-customer-sidecar-adapter.py --port 8092

# 或 Docker
docker compose -f deploy/examples/ai-find-customer-sidecar/compose.yml up -d
# 或 dev 栈 profile
docker compose -f docker-compose.dev.yml --profile sidecars up -d ai-find-customer-adapter
```

主站 backend 配置：

```env
AI_FIND_CUSTOMER_URL=http://127.0.0.1:8092
AI_FIND_CUSTOMER_TOKEN=dev-sidecar-token
```

## 主站行为

| 场景 | 结果 |
|------|------|
| Sidecar 可用且有 evidence | `mode: ai_find_customer_sidecar`，写入 `buyer_prospect_leads` |
| 未配置 / 失败 / 无 evidence | 回退 `accio_buyer_discovery` 画像模板 |
| 一律 | `human_verify_required: true` |

Admin 入口：`/sales/customer-finder` → `POST /api/v1/super-agent/sales/customer-finder`  
UBrain：`intent=find_buyers` → `find_buyer_prospects()`

## 验收

```powershell
# Sidecar 状态（无需登录）
python scripts/verify-ai-find-customer-sidecar.py

# 配置 smoke（需 Sidecar 已部署）
python scripts/verify-ai-find-customer-sidecar.py --smoke-find

# 集成状态 API（需 admin JWT）
curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:8001/api/v1/foreign-trade/integrations/sidecars/status
```

Admin 登录后打开「客户开发」，搜索关键词；Sidecar 命中时提示「须人工核实 evidence_url」。

## Out-of-Scope

- 不把 Streamlit/React 找客 UI 嵌入 Admin
- 主镜像不做深度爬虫
- 无 evidence_url 的线索不得落库为「已验证客户」
