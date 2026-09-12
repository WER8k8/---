# 商业飞轮 OS — 开发总文档（整合版）

> **版本**：2026-05-25  
> **读者**：产品、全栈、测试、运维  
> **用途**：把创始人/产品已定的说明收敛为**一条开发主线**；本阶段做完本文档范围内的开发验收后，再进入 **演讲彩排 → 测试 → 上线部署**。

---

## 0. 执行顺序（全员遵守）

| 阶段 | 内容 | 状态 |
|------|------|------|
| **① 开发（当前）** | 字节 DeerFlow + 阿里 Accio 对标、三条断层飞轮、副驾与 API | 本文档 |
| **② 测试** | 单元/集成/E2E、30 天验真指标预演 | 待 ① 环境验收 |
| **③ 上线部署** | 迁移、HTTPS、cron、生产 env | 待 ② |
| **④ 演讲/录屏/彩排** | 七步实机、30 分钟彩排、对外 SKU 实机 | **最后**，见 [开发进度统计-未完成清单.md](./开发进度统计-未完成清单.md) §八 |

**夜间加速（可选）**：[夜间无人全自动开发模式.md](./夜间无人全自动开发模式.md) — 机械门禁 `scripts/night-autodev.ps1` + 队列 `night-autodev-queue.yaml`，仍属 ① 开发阶段。

**禁止**：在 ①③ 未收尾前，做演讲/录屏/七步彩排（一律后置到阶段 ④）。

**进度统计**：[开发进度统计-未完成清单.md](./开发进度统计-未完成清单.md)

---

## 1. 产品铁律（不可改向）

**卖货第一生产力 = 字节系深度研究（DeerFlow）+ 阿里系国际电商执行（AccioWork）对标复刻。**

| 大厂 | 角色 | 本系统 |
|------|------|--------|
| **字节 · DeerFlow** | 多 Agent 深度研究（望远镜） | `deerflow_research_service`、`deerflow_jobs`、`research_brief` |
| **阿里 · AccioWork** | 国际电商执行（卡车） | `accio_sales_service`、技能目录、`/client/copilot` |

- **主方向**：研究 → `Research Brief` → `accio_actions[]` → 编排执行 → 销售反馈回流；**复刻形态，不另起卖货范式**。
- **允许增强**：建材垂直、自有独立域、40 平台矩阵、三轨计费、**人审外发**（不自动发信/改价）。
- **不能 1:1**：阿里国际站私有数据、站内广告全自动、1688 自动下单等 — 标 `gap`，不删对标项。

详表：`docs/出海计/DeerFlow-Accio-能力对标与本系统映射.md`、`docs/出海计/Accio-Work对标与复刻路线.md`。

---

## 2. 商业飞轮 OS（三条断层 → 一个闭环）

### 2.1 断层与解法

| 柱 | 痛点 | 本系统实现 | 外挂（渐进） |
|----|------|------------|--------------|
| **记忆** | 研究做完 Accio 记不住 | `ubrain_research_insights`、`ubrain_tenant_memory`；`extract_insight`；Accio 前 `retrieve_insights_for_accio` | Mem0（`MEM0_API_URL`） |
| **执行** | 报告→操作人工搬运 | `ubrain_pipeline_runs`；`on_deerflow_job_finished` → 排队 `find_buyers` / `outreach_letter_pack` | n8n → `/commercial-os/webhook` |
| **反馈** | 卖得怎样研究不知道 | `ubrain_feedback_snapshots`；`collect_sales_feedback` → `research_hints` | PostHog（`POSTHOG_HOST`） |

### 2.2 数据流（开发实现须保持）

```text
用户话术 / Research Brief
  → DeerFlow Lite：Planner → Researcher → Reviewer → Writer
  → research_brief { findings[], controversies[], accio_actions[] }
  → on_deerflow_job_finished
       ├─ extract_insight（记忆）
       └─ run_pipeline_after_deerflow（执行，UBRAIN_AUTO_PIPELINE 默认开）
  → Accio：find_buyers → outreach_letter_pack → negotiation_draft …
  → collect_sales_feedback（反馈）→ merge_memory.research_hints
  → 下一轮 market_research 读 hints + prior insights
```

### 2.3 Accio 卖货三件套（执行层最小集）

| 能力 | 意图 | 服务 |
|------|------|------|
| 自动找客 | `find_buyers` | `accio_sales_service.find_buyers` → `buyer_prospect_leads` |
| 开发信 | `outreach_letter_pack` | 双语草稿，`human_send_required` |
| 自动谈单 | `negotiation_draft` | 多轮话术，不自动改价 |

副驾确认发送：`POST /api/v1/ubrain/prospects/confirm-send`（记录确认，不代发）。

---

## 3. 代码与数据资产（权威路径）

### 3.1 后端服务

| 模块 | 路径 |
|------|------|
| 飞轮桥接 | `backend/app/services/ubrain/commercial_os_bridge.py` |
| Research Brief | `backend/app/services/ubrain/deerflow_research_service.py` |
| DeerFlow 队列 | `backend/app/services/ubrain/deerflow_job_service.py` |
| Accio 执行 | `backend/app/services/ubrain/accio_sales_service.py` |
| 意图编排 | `backend/app/services/ubrain/orchestrator.py` |
| 技能目录 | `backend/app/data/accio_skill_catalog.json` |

### 3.2 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/ubrain/commercial-os/status` | 飞轮状态（`pillars`、洞察、最近编排） |
| GET | `/api/v1/ubrain/commercial-os/pipelines` | 最近编排记录（副驾列表） |
| GET | `/api/v1/ubrain/commercial-os/insights` | 历史研究检索 |
| GET | `/api/v1/ubrain/commercial-os/skill-catalog` | Accio 对标覆盖率 |
| GET | `/api/v1/ubrain/commercial-os/gaps` | 未实现技能 gap 列表 |
| GET | `/api/v1/ubrain/commercial-os/gap/{skill_id}` | 未实现 → HTTP 501 + gap 说明 |
| POST | `/api/v1/ubrain/commercial-os/research-brief` | 同步生成 Brief |
| POST | `/api/v1/ubrain/commercial-os/feedback/sync` | 销售反馈回流 |
| POST | `/api/v1/ubrain/commercial-os/webhook` | n8n / 旁路 DeerFlow（`X-N8N-Webhook-Secret`） |
| POST | `/api/v1/ubrain/chat` | 副驾统一入口（意图分发） |
| GET | `/api/v1/ubrain/jobs/{id}` | 异步 DeerFlow 任务状态 |

路由注册：`backend/app/api/v1/routes/ubrain_commercial_os.py`、`ubrain.py`。

### 3.3 数据库（Alembic）

| 迁移 | 表 |
|------|-----|
| `025_ubrain_accio_sales` | `ubrain_tenant_memory`、`buyer_prospect_leads` |
| `026_ubrain_commercial_os` | `ubrain_research_insights`、`ubrain_pipeline_runs`、`ubrain_feedback_snapshots` |

部署前：`cd backend && alembic upgrade head`

### 3.4 前端

| 页面 | 路径 |
|------|------|
| 商业飞轮 OS 副驾 | `frontend/admin/src/views/client/copilot.vue` |
| 路由 | `/client/copilot`（meta：商业飞轮 OS） |

副驾能力：三根支柱状态、跑飞轮、Research Brief、`accio_actions` 芯片、Accio 三件套、聊天与任务卡。

---

## 4. 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `UBRAIN_AUTO_PIPELINE` | `1` | `0` = DeerFlow 完成后不自动排队 Accio |
| `N8N_WEBHOOK_SECRET` | 空 | 配置后 webhook 须带同名 Header |
| `MEM0_API_URL` | 空 | 预留双写外部记忆 |
| `POSTHOG_HOST` | 空 | 预留行为分析 |

---

## 5. 副驾话术 → 意图（验收用）

| 用户说法 | 意图 | 行为 |
|----------|------|------|
| 跑一轮市场研究并自动找客 | `market_research` | 入队 DeerFlow；成功后飞轮钩子 |
| 同步销售反馈 / 销售反馈 | `sync_feedback` | `collect_sales_feedback` |
| 找…采购商 | `find_buyers` | 画像入库 |
| 生成 N 封开发信 | `outreach_letter_pack` | 需确认 |
| 压价怎么谈 | `negotiation_draft` | 话术包 |

---

## 6. 开发阶段任务（① 当前）

### 6.1 P0 — 飞轮可演示（必须先过）

| ID | 任务 | 验收 |
|----|------|------|
| D1 | 迁移 025/026 已应用 | `alembic current` 含 head |
| D2 | 副驾加载 `/commercial-os/status` 三根支柱 | 登录租户可见记忆/执行/反馈 |
| D3 | 生成 Research Brief | POST research-brief 返回 `accio_actions` ≥2 |
| D4 | 跑飞轮（async market_research） | job success 且 `commercial_os_hook.insight_id` |
| D5 | `UBRAIN_AUTO_PIPELINE=1` 时 pipeline 入队 | `last_pipeline.created_job_ids` 非空 |
| D6 | 同步反馈写 `research_hints` | sync 后 status 反馈柱 active |
| D7 | 单元测试绿 | 见 §7 |

### 6.2 P1 — 对标 gap 收敛（① 内可选并行）

按 `GET .../skill-catalog` 的 `implemented: false` 排期，**不删条目**：

- `image_sourcing`（以图搜品）
- `auto_shopify`（建站克隆 — 已有独立域则维持 gap 说明）
- `paid_ads_creative`、`supplier_rfq`

### 6.3 P2 — 外挂（① 验收后）

1. n8n 自托管 → `deerflow_done` webhook  
2. Mem0 双写 insights  
3. PostHog → 定时 `feedback/sync`  
4. 旁路部署官方 [deer-flow](https://github.com/bytedance/deer-flow) 回写 Brief  

见 `docs/出海计/商业OS飞轮-开源组件对接.md`。

---

## 7. 测试命令（开发门禁）

```powershell
Set-Location "backend"
python -m pytest tests/unit/test_commercial_os_flywheel.py tests/unit/test_accio_sales.py -q
python -m pytest tests/unit/test_framework_batch15.py -q
```

**通过标准**：飞轮 + Accio + webhook 相关用例全部 passed（当前基线 **16**）。

可选全量：`python -m pytest tests/unit -q`（按 CI 约定）。

路由门禁（改后端路由后）：`python scripts/check_mounted_routes.py`（仓库根目录）。

---

## 8. 阶段 ②③④ 清单（开发完成后再做）

### 8.1 演讲 / 录屏 / 彩排（④ 最后）

| 项 | 参考文档 | 说明 |
|----|----------|------|
| 七步实机 | `seven_step_framework_service`、ops 审计 API | 不替代飞轮主线演示 |
| 对外 SKU 话术 | `接下来怎么做-产品营销技术联合行动.md` | 谦逊验真，不保证电话数 |
| 验真指标 | `DeerFlow-Accio-本系统-验真话术与30天指标.md` | 30 天线索表 |

**彩排演示路径建议**：登录租户 → 商业飞轮 OS → 生成 Brief → 跑飞轮 → 展示洞察/编排 → 同步反馈 → 展示 `research_hints`。

### 8.2 测试（③）

| 类型 | 内容 |
|------|------|
| 集成 | chat → job → hook → pipeline → prospect |
| E2E | 副驾关键按钮（可选 Playwright） |
| 业务验真 | 手机必填、来源追踪、周报导出（与 `接下来怎么做` T1–T4 对齐） |

### 8.3 上线部署（④）

| 项 | 动作 |
|----|------|
| DB | `alembic upgrade head` |
| 配置 | `UBRAIN_AUTO_PIPELINE`、`JWT`、租户绑定 |
| 进程 | DeerFlow job runner / `jobs/run-pending` cron（若已配置） |
| 反馈 | 每周 `POST .../feedback/sync` 或定时任务 |
| HTTPS | 演示独立域（营销验真前置，见联合行动 T1） |

---

## 9. 与「验真 / 营销」文档的关系

| 主题 | 文档 | 关系 |
|------|------|------|
| 北极星（电话进系统） | `接下来怎么做-产品营销技术联合行动.md` | 飞轮为**提速工具**，验真尺不变 |
| 30 天指标 | `DeerFlow-Accio-本系统-验真话术与30天指标.md` | ② 演讲用 |
| 为何贵于 GEO | `网站效果论-为何值得比6980GEO贵.md` | 对外，非开发改向 |
| 保温厂试点 | `自有保温厂-30天试点与生存链.md` | 第一个飞轮租户 |

---

## 10. 合规（开发默认值）

- 采购商画像为**候选模板**，非阿里实名库；外发前人工核实。  
- `human_send_required` / 副驾二次确认：付钱、改价、对外发信**禁止**静默自动。  
- 商用前核对 Mem0、n8n 等许可证（见飞轮对接 doc §五）。

---

## 11. 子文档索引

| 文档 | 内容 |
|------|------|
| [DeerFlow-Accio-能力对标与本系统映射.md](./DeerFlow-Accio-能力对标与本系统映射.md) | 能力表 + 铁律 |
| [Accio-Work对标与复刻路线.md](./Accio-Work对标与复刻路线.md) | 不能抄什么、Phase A/B/C |
| [商业OS飞轮-开源组件对接.md](./商业OS飞轮-开源组件对接.md) | Mem0/n8n/PostHog |
| [UBrain-DeerFlow-Accio融合获客智能体.md](./UBrain-DeerFlow-Accio融合获客智能体.md) | 三合一架构 |
| [UBrain-X-AccioWork全维度能力蓝图.md](./UBrain-X-AccioWork全维度能力蓝图.md) | 全技能舰队 |
| [UBrain-X-全员实施任务书.md](./UBrain-X-全员实施任务书.md) | 历史任务分工（以本文 §6 为准） |

---

## 12. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-25 | 整合：铁律、飞轮三柱、实现路径、①→④ 顺序、测试与部署门禁 |

**维护**：产品改优先级只改 §0、§6；新增 Accio 技能只改 `accio_skill_catalog.json` + §3 API，并回写 §1 对标表。
