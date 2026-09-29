# 🔌 Trade AI Agent × GoodJob CRM → Hermes 总线 详细对接方案

> **版本**：v1.0 ｜ **编制**：2026-09-09 ｜ **性质**：设计方案（含现状判据）
> **范围**：把 `_external/trade-ai-agent`（FastAPI·全域拓客WhatsApp）与 `_external/goodjob-crm`（Node·7步履约单证¥WhatsApp翻译）真正接入 Hermes DAG 执行总线，取代当前 **mock 桩**执行器。
> **一句话结论**：执行器壳已建、`_external` 两个子系统是**完整实体**，但当前 executor = **纯桩**（返回假数据、从不真调子模块）。本方案给出「桩→真桥」的契约、状态机、单证、WhatsApp、Saga、自检六件套落地清单。

---

## 0. 现状判据（本次实测，非推演）

| 对象 | 现状 | 证据 |
|---|---|---|
| `executors/trade_ai_agent_executor.py` | **纯 mock**：`prospect.scrape` 返回 `buyer{i+1}@…-intl.com` 假线索、`whatsapp_outreach` 直接 `status:"sent"` 从不真发、`inbox.classify` 是 if-else 关键词 | 源码 read |
| `executors/goodjob_crm_executor.py` | **纯 mock**：PI 只返回硬编码 seller 字典（`doc_status:"draft_approved"`）、`im.translate` 返回 `[Translated to {lang}]` 前缀、无 DB/PDF/真翻译 | 源码 read |
| `_external/trade-ai-agent` | ✅ 真实 FastAPI 系统：13 个 router（`whatsapp/outreach/email/workflow/customer/skill…`），自带 `app.core.agent` + skills 注册 + `SkillRegistry` | `api/v1/` + `main.py` |
| `_external/goodjob-crm` | ✅ 真实 Node/TS 系统：`uj-bridge-routes.ts`、`agent-api-contracts.ts`、`local-runner-*`、`whatsapp-service.ts`（whatsapp-web.js + Twilio 双通道）、`customs-export.ts`、单证工作室 | `src/` 结构 |
| walkthrough「4节点全绿+WhatsApp触达」 | ⚠️ 是**桩空跑**通过，非真执行；自检 18/19/19 口径仍漂移 | 对比 executors + walkthrough |

> ⚠️**红线**：当前 `orchestration_selfcheck` 的 Check 14/15/16 判定说明接近「外观通过」。必须把自检升级为**真实桥接冒烟**（调用真端口/真方法并断言副作用），否则对接状态永远是假绿。

---

## 1. 对接形态选型（三选一，推荐 A）

| 形态 | 说明 | 适用 | 结论 |
|---|---|---|---|
| **A. 异步 HTTP Bridge（推荐）** | Hermes adapter 通过 HTTP 调 `_external` 的成熟 API（trade-ai FastAPI `/api/v1/*`；goodjob `uj-bridge` / `agent-api-contracts`），返回 JSON 回写 `ai_tasks.output_json` | 两子系统均有现成 API 面，隔离干净、可异步、可扩展 | ✅ 首选 |
| B. 进程内 import（trade-ai 同为 Python） | 直接把 `app.core` / skills 呈 import 进 Hermes | trade-ai 可省 HTTP；但强耦合、venv 冲突 | 🟡 仅 trade-ai 局部 |
| C. 直接读子系统的 DB 表 | 跳过 API，连 trade_ai/goodjob 的库 | 快但有击穿风险、绕开鉴权 | ❌ 不推 |

> goodjob 自带 `uj-bridge-routes.ts` 就是「优丁主系统↔GoodJob」官方桥接，**首选让 Hermes 走它**，不必自造契约。

---

## 2. Hermes↔子系统的能力契约映射

### 2.1 Trade AI Agent（`trade_ai_agent` executor → `http://<trade-ai>:8000/api/v1/`）

| Hermes capability | 真调用端点 | 返回 → Hermes output 字段 |
|---|---|---|
| `prospect.scrape` | `POST /api/v1/customer/search`（潜客挖掘） | `prospects` / `leads` 真实线索数组 |
| `outreach.whatsapp` | `POST /api/v1/whatsapp/send`（模板/自由消息） | `channel/recipient/wa_message_id/status=delivered` |
| `outreach.email` | `POST /api/v1/email/send` 或 `/api/v1/outreach/start` | `email_status=queued/accepted` |
| `inbox.classify` | `POST /api/v1/conversation/classify`（LLM 意图） | `detected_intent`（真 intent，非关键词） |
| 状态查询 | `GET /api/v1/stats` / 各任务 `GET …/{id}` | 节点 `trace_id` 关联 |

> 注意 trade-ai 自带 Redis/Celery（FLOWER@5555）、PG `trade_ai`，是独立进程；Hermes 以异步任务方式调用后轮询结果，不阻塞 DAG。

### 2.2 GoodJob CRM（`goodjob_crm` executor → `uj-bridge`/`agent-api-contracts`）

| Hermes capability | 真调用面 | 返回 → output |
|---|---|---|
| `crm.sync_stage` | goodjob `prospect-candidate-pipeline` / `lead-finder-launch` 状态机 | `current_stage`、`lead_id` |
| `document.generate_pi` | goodjob 单证工作室 PI 生成（`trade-document-*` / swagger 契约） | `pi_number`、`total_amount`、**docId/PDF URL** |
| `document.generate_trade_docs` | CI/PL 套打 + `customs-export.ts` | `commercial_invoice`、`packing_list`、导出文件 |
| `im.translate` | 接 goodjob `ai-model-runtime` 或主系统 ModelGateway 真翻译（非 `[Translated]` 桩） | `translated_text` 真译文 |
| WhatsApp 收发 | `whatsapp-service.ts`（whatsapp-web.js LocalAuth / Twilio 双通道） | `wa_message_id`、`status` |

> `agent-api-contracts.ts`（85KB）是 GoodJob 提供给 Agent 的官方契约，Hermes bridge 直接对齐它，避免臆造字段名。

---

## 3. 七步履约 + JsonPath 数据总线串联（真执行版）

复用通用规格书 `$.node.output.path` 协议，连通后示例：

```json
{
  "plan_id": "plan_b2b_growth_8891",
  "nodes": [
    {"id":"node_research","executor":"trade_ai_agent","capability":"prospect.scrape",
     "sop_ref":"skills://customer-research","input":{"keyword":"insulation","target_country":"UAE"}},
    {"id":"node_quotation","executor":"goodjob_crm","capability":"document.generate_pi",
     "depends_on":["node_research"],
     "input_from":{"buyer_name":"node_research.output.prospects[0].company_name",
                   "contact_email":"node_research.output.prospects[0].email"}},
    {"id":"node_crm_stage","executor":"goodjob_crm","capability":"crm.sync_stage",
     "depends_on":["node_quotation"],"input":{"stage":"quoted"}},
    {"id":"node_message","executor":"goodjob_crm","capability":"im.translate",
     "depends_on":["node_quotation"],"input":{"text":"Ready to send PI","target_lang":"ar"}},
    {"id":"node_outreach","executor":"trade_ai_agent","capability":"outreach.whatsapp",
     "depends_on":["node_quotation","node_message"],
     "input_from":{"whatsapp":"node_research.output.prospects[0].whatsapp"}},
    {"id":"node_notify","executor":"n8n_dispatch","capability":"webhook.whatsapp",
     "depends_on":["node_outreach"]}
  ]
}
```

流转：**拓客(trade-ai 真数据) → JsonPath 取线索 → PI(goodjob 真单证) → 7步建档 → WhatsApp 双向翻译 → 真触达 → n8n 回执**。全链路透传 `trace_id`。

---

## 4. 六件套落地清单（P0—P2，拒绝概念）

### P0 ❗真实桥接（替换 mock，投入最大价值）
1. **trade-ai client**：新增 `backend/app/services/hermes/clients/trade_ai_client.py`（`httpx.AsyncClient`，base_url 走配置 `TRADE_AI_API=/_external` 或本地端口），实现上述 4 能力 + 错误/重试。
2. **goodjob client**：新增 `goodjob_client.py`，对齐 `uj-bridge-routes.ts` + `agent-api-contracts.ts`。
3. **改造两 executor**：`run()` 内改用 client 真发，移除硬编码假数据。
4. **启动**：trade-ai（`uvicorn --port 8000`）与 goodjob（`npm run start:mysql` / `dev:worker`）纳入编排启动脚本，给固定端口，禁冲突（trade-ai 8000 需与主后端 8000/8001 错开，用 `--port 8010` 或独立 host）。

### P1 状态机 / 补偿 / 计费真实化
5. **Saga 真补偿**：`document.generate_pi` 成功后若下游失败 → 调 goodjob 删除孤儿单证 + 主系统 `wallet_service.refund_tokens()` 退 token。
6. **Token 计量**：把每次真调用计入 `meter_events` / `token_ledger`（当前 mock 无常量）。
7. **WhatsApp 状态回写**：`sendMessage` 返回真 `wa_message_id` 回写 ai_tasks，供取证书店。

### P2 自检与收敛
8. **升级自检 Check 14/15/16**：改为「真实桥接冒烟」——断言 `GET /api/v1/stats` 200、`whatsapp-service` 客户端存在、`uj-bridge` 连通；统一门禁项数为**单一真值**（以 `orchestration_selfcheck.py` 实跑输出为准，现行 18/19/14 三口径并入本方案废单）。
9. **同一契约双目录同步**：worktree 与 `主要备份\上线网站\backend` 同步 4 个新增文件 + 2 个 executor 改动（项目双目录陷阱铁律）。
10. **集成测试**：重写 `tests/test_aeos_full_loop_dag.py` 为真执行版（可在 test 环境用 fake provider / 本地达到，但**必须有副作用断言**，禁止桩通过）。

---

## 5. 验收判据（一条线划清「真桥 vs 桩」）

| 判据 | 桩(现状) | 真桥(交付后) |
|---|---|---|
| trade-ai 拓客 | `buyer{i}@…-intl.com` | 来自真实 API 的线索 & status |
| WhatsApp 发送 | `status:"sent"` | 有 `wa_message_id` / deliver 回执 |
| PI 生成 | 硬编码字典 | 返回 docId + 真 PDF/URL |
| im.translate | `[Translated:…]` | 真译文 & 语言标记 |
| 自检 | 外观通过 | 真端口冒烟 + 业务副作用断言 |

---

## 6. 风险与口径现状

- **trade-ai(8000) vs 主后端(8000/1) 端口冲突**：必须先错端口再起，否则自拌。
- **goodjob 依赖**：MySQL store（`CRM_STORE=mysql`）、BullMQ 需 Redis；n8n/Redis 已在，MySQL 需确认本机 3306 可用。
- **tempa多执行器注册**：`__init__.py` 已自动注册 4 执行器正确，勿改坏现有 accio/deerflow。
- **双目录陷阱**：所有新增/改动都必须同步 `工作区↔主要备份` 两处，避免 3000/8000 起错版本。

---

*EOF · TradeAI×GoodJob→Hermes 对接方案 v1.0 · 2026-09-09 · 现状判据基于源码实测*