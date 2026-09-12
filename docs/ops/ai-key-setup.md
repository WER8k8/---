# AI Key 配置指南（管理端 + 后端）

> 对应任务：第二阶段 · AI Key 配置  
> 管理端入口：`/integrations/ai-config`（`AiConfig.vue`）  
> 后端门控：`backend/app/services/ai_engine.py`

## 1. 最低可用（本地开发）

在 `backend/.env` 中至少配置 **一个** 提供商，或启用 MVP 模式：

```env
ENVIRONMENT=development
MVP_LAUNCH=1
REDIS_ENABLED=false

# 推荐：DeepSeek（成本友好）
AI_DEEPSEEK_API_KEY=sk-...
AI_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

`MVP_LAUNCH=1` 时无 Key 也可启动 API，但 AI 回复为 **mock**（响应带 `mode: mock`），**不得**对客户宣称智能回复已上线。

## 2. 生产路径（必须）

生产环境 **禁止** 长期依赖 `MVP_LAUNCH=1`。须配置：

| 变量 | 用途 |
|------|------|
| `AI_DEEPSEEK_API_KEY` | 默认对话 / 谈单 |
| `AI_NVIDIA_API_KEY` | NIM 免费额度 GPU 推理 |
| `AI_OPENAI_API_KEY` | 可选兜底 |
| `JWT_SECRET_KEY` | ≥32 字符，独立强密钥 |

重启后端：

```powershell
powershell -File scripts/start-dev-admin.ps1 -ForceRestart
```

## 3. 管理端配置

1. 超管登录 → **集成 → AI 配置**
2. **添加提供商**：名称、类型、API Key、Base URL
3. **添加模型**：绑定提供商，类型 chat/embedding/image
4. 点击 **探测可用性** — 未配置 Key 的模型应显示「未检测/不可用」，不得假绿

Key 注册链接已在页面底部（OpenAI / DeepSeek / NVIDIA / Anthropic / Gemini）。

## 4. 验证

```powershell
cd backend
$env:MVP_LAUNCH="0"
$env:AI_DEEPSEEK_API_KEY="sk-..."   # 填入真实 Key
python -c "from app.services.ai_engine import AIEngine; AIEngine(); print('OK')"
```

```powershell
cd frontend/admin
npm run cert:gate
```

## 5. 相关 Sidecar（非 LLM）

| 能力 | 变量 |
|------|------|
| GEO Headless 探针 | `HEADLESS_PROBE_SIDECAR_URL` |
| AI 找客 | `AI_FIND_CUSTOMER_URL` |
| 行为分析 | `USER_ACTION_ANALYTICS_URL` |

## 6. 抖音评论 Worker（ITER-03b）

生产路径须配置 `DOUYIN_APP_ID` + `DOUYIN_APP_SECRET`，并任选：

- **AiToEarn**：`AITOEARN_API_KEY` + 租户槽位 → `POST /api/v1/client/douyin-comments/pull`
- **Inbox 文件**：`DOUYIN_COMMENT_INBOX_DIR` 指向 SAU 导出 JSON

开发彩排（不冒充生产）：

```powershell
# Admin 谈单页 →「投递测试评论（5c）」或：
curl -X POST http://127.0.0.1:8001/api/v1/client/douyin-comments/rehearsal-ingest -H "Authorization: Bearer <token>"
```

未配置 Key 时返回 `reason: aitoearn_not_configured`，不会写入假评论。

## 7. AiToEarn 全栈对齐（Publish / Engage / Analytics）

| 模块 | 变量 / 入口 | 说明 |
|------|-------------|------|
| **Publish** | `AITOEARN_API_KEY` + 超管分配租户槽位 | `/client/distribute` 视频分发；支持 `scheduled_at` 定时 |
| **Engage** | 同上 + 矩阵号 | `/client/engage` 拉评 + `auto_send_via_aitoearn` 真回复 |
| **Analytics** | `AITOEARN_API_KEY` | `/client/cross-platform` 跨平台看板 |
| **能力探针** | — | `GET /api/v1/aitoearn/hub/capabilities` |

```env
AITOEARN_API_KEY=sk-...
AITOEARN_API_BASE=https://mcp.aitoearn.cn
```

**超管分配矩阵槽位（O-2）**：

1. 登录超管 → **租户管理** (`/tenants/dashboard`)
2. 租户行点击 **AiToEarn** → 查看未分配池 → **自动分配**
3. 或 API：`POST /api/v1/publish/video/admin/auto-assign-aitoearn-slot?tenant_id=<uuid>`

本地骨架：`powershell -File scripts/bootstrap-owner-env.ps1`

**未配 Key 时**：Publish/Engage API 返回 503 或明确错误，**禁止**假成功。

**Monetize（CPS/CPE/CPM 任务市场）**：本系统使用自有套餐/佣金，**未复刻** AiToEarn 交易市场。
