# 商业 OS 飞轮 · 三条断层闭合与开源对接

> 2026-05-25  
> 目标：DeerFlow + AccioWork 从「王炸组合」进化为**可自我进化的全自动商业操作系统**。

---

## 一、三条断层与本系统解法

| 断层 | 痛点 | 本仓库已实现（无需外购即可跑） | 推荐外挂（渐进） |
|------|------|-------------------------------|------------------|
| **记忆** | DeerFlow 研究一次性，Accio 记不住 | `ubrain_research_insights` + `ubrain_tenant_memory`；任务成功自动 `extract_insight`；Accio 找客/开发信前 `retrieve_insights_for_accio` | **Mem0** / Zep（`MEM0_API_URL`） |
| **执行** | 报告→操作需人工搬运 | `ubrain_pipeline_runs`；`on_deerflow_job_finished` 自动排队 `find_buyers`→`outreach_letter_pack`；`UBRAIN_AUTO_PIPELINE=1` 默认开 | **n8n** → `POST /api/v1/ubrain/commercial-os/webhook` |
| **反馈** | 卖得怎样 DeerFlow 不知道 | `ubrain_feedback_snapshots`；`collect_sales_feedback` 汇总询盘/找客/发送率；写入 `research_hints` 反哺下一轮 | **PostHog**（`POSTHOG_HOST` 埋点扩展） |

质量门（Ragas 轻量）：`quality_score` 启发式打分，低于阈值可触发重跑（后续接 Ragas 库）。

---

## 二、架构（与您的 Mermaid 对齐）

```text
DeerFlow 任务成功
  → extract_insight（记忆层）
  → run_pipeline_after_deerflow（编排层）
  → enqueue Accio 任务（find_buyers / outreach_letter_pack）
Accio 执行（开发信/找客）
  → 询盘 + buyer_prospect_leads 状态
  → collect_sales_feedback（反馈层）
  → merge_memory.research_hints
  → 下一轮 market_research 自动读 hints
```

可选外挂：

- **Browser Use** → 矩阵发布 / 非 API 平台（见 `browser_profile` + 发布 Worker）
- **GraphRAG** → 将 `entities_json` 同步到 Neo4j（P2，见 `GraphRAG-占位与Neo4j对接.md`；`status.integrations.graphrag` 已占位）

---

## 三、API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/ubrain/commercial-os/status` | 飞轮状态（洞察数、编排数、上次反馈） |
| GET | `/api/v1/ubrain/commercial-os/pipelines` | 最近编排记录 |
| GET | `/api/v1/ubrain/commercial-os/insights` | 检索历史研究 |
| POST | `/api/v1/ubrain/commercial-os/feedback/sync` | 手动同步销售反馈 |
| POST | `/api/v1/ubrain/commercial-os/webhook` | n8n 回调（`X-N8N-Webhook-Secret`） |

副驾话术：

- `跑一轮市场研究并自动找客` → `market_research`（可 `async_job: true` 入队）
- `同步销售反馈到研究记忆` → `sync_feedback`

**n8n 回调示例**（body 见 `docs/出海计/examples/n8n-deerflow-done.json`）：

```powershell
$body = Get-Content "docs/出海计/examples/n8n-deerflow-done.json" -Raw
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/ubrain/commercial-os/webhook" `
  -Headers @{ "X-N8N-Webhook-Secret" = $env:N8N_WEBHOOK_SECRET } `
  -ContentType "application/json" -Body $body
```

**定时反馈**（任务计划）：`scripts/ubrain-feedback-sync.ps1`，需 `UBRAIN_API_TOKEN`。

环境变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `UBRAIN_AUTO_PIPELINE` | `1` | `0` 关闭 DeerFlow 完成后自动排队 Accio |
| `N8N_WEBHOOK_SECRET` | 空 | 配置后 n8n 须带同名 Header |
| `MEM0_API_URL` | 空 | 预留；非空时可双写外部记忆 |
| `POSTHOG_HOST` | 空 | 预留事件上报 |

---

## 四、优先落地顺序（与您建议一致）

1. **已内置** n8n 等价编排 + Mem0 等价记忆表（本迭代）
2. 接 **n8n** 自托管：DeerFlow 容器/webhook → 本系统 `/commercial-os/webhook`
3. 接 **Mem0** Docker：双写 `ubrain_research_insights`
4. **PostHog** 埋点：商品页/开发信链接点击 → `feedback/sync` 定时拉取
5. GraphRAG / Browser Use / Ragas 按客户规模再加

---

## 五、合规提醒

- 采购商画像为**模板级候选**，非阿里站内实名库；外发前人工核实。
- 禁止未确认自动发信/自动改价；`human_send_required` 始终为 true。
- 商用前核对 Mem0（Apache 2.0）、n8n（Fair-code）等许可证。

---

## 相关

- `docs/出海计/UBrain-X-AccioWork全维度能力蓝图.md`
- `docs/出海计/UBrain-DeerFlow-Accio融合获客智能体.md`
- `backend/app/services/ubrain/commercial_os_bridge.py`
