# GPT 设计文档纠错与工程实现补充报告 V1.0

> 基准：对 `Desktop\新建文件夹 (2)` 下 6 份 GPT 设计文档逐条核对当前代码库（优丁 Global B2B AI Revenue Engine，worktree `上线网站.worktrees\agents-install-vscode-cline-deploy-strix`）实际状态后产出。
> 结论先行：**GPT 文档的战略分层（Control Plane / Execution Plane / Experience Engine）方向正确，但存在 4 类严重问题——术语互相矛盾、技术栈与现状不符、任务清单未对现有代码重新基线、多处"待建"模块实际已存在。** 正确做法不是按 TASK-001 从零新建 `ai-growth-os` 仓库，而是在现有 224 张表的模块化单体上做"对齐式改造"。

---

## 一、代码库现状扫描（证据版）

### 1.1 总体盘点

| 维度 | 现状 | 证据 |
|---|---|---|
| 后端 | Python + FastAPI + SQLAlchemy 2.0.29 + Alembic 1.13.1 + Celery 5.4.0 + Redis 5.0.3 | `backend/requirements.txt` |
| AI 层 | LangChain 多 Provider（NVIDIA NIM / DeepSeek / Anthropic / OpenAI / Gemini），1003 行 `ai_engine.py`；`MVP_LAUNCH=1` 时走 mock 降级 | `app/services/ai_engine.py`、`项目完成度盘点.md` |
| 前端 | **Nuxt 3 + Vue 3 + Tailwind + Pinia + ant-design-vue**，300+ 页面，独立 `admin` 应用 401 个 .vue | `frontend/package.json` |
| 数据库 | 224 张表，alembic 69 个版本，head ≈ `081_add_purchased_token_bonus` | `alembic_migrations/versions/`、`服务状态-2026-08-30.md` |
| API | 1616 条 openapi 路径（幽灵路由已清零），138 个路由文件，88 个模型文件 | `app/api/v1/routes/`、`app/models/` |
| 部署 | docker-compose（dev/prod/seo/cncfstack），非 K8s；运行中：后端 :8000、前端 :3000、admin :5174、PG :5433、Redis :6379、n8n :5678、Temporal :8233 | `docker-compose.*.yml`、`服务状态-2026-08-30.md` |
| 已知债 | SQLite 零依赖模式下 Celery 不可用（仅开发兜底）；PG/Redis 完整链路依赖 Docker；metrics 端点需认证 | `项目完成度盘点.md` |

### 1.2 GPT 文档要建的模块，代码里实际已存在的（关键发现）

| GPT 文档中的"待建"模块 | 代码库现状 | 位置 |
|---|---|---|
| Hermes 内部调度中心 | **已存在，67 个文件**：plugin runtime、flywheel、ECC 专家面板、站点巡检、greedy agency 等 | `app/services/hermes/` |
| DeerFlow 深度执行 | **已存在**：planner / executor / reviewer / state_machine / checkpoint，含 9 状态状态机（但 executor 内 4 处 `TODO` 未接真实服务） | `app/services/deerflow/` |
| n8n Adapter | **已存在**：webhook 触发 + 重试退避 + workflow_registry | `app/services/n8n/` |
| Agent 编排（Paperclip） | **已存在**：orchestrator / approval_gate（人审）/ budget_guard（预算护栏）/ goal_chain / heartbeat | `app/services/paperclip/` |
| UBrain 获客/销售 | **已存在，83 个文件**：lead scoring、邮件外发队列、找客（LinkedIn/Reddit/Quora/TikTok/WhatsApp）、AccioWork 卖货 | `app/services/ubrain/` |
| Experience / Evolution Engine | **已存在**：engine / canary（灰度）/ experience_store / version_control + 表 `EvolutionTaskRecord`/`ExperienceEntry`/`SkillVersion` | `app/services/evolution/`、`app/models/evolution.py` |
| ECC 专家库 | **部分存在**：`hermes/ecc_expert_panel.py` + 行业 skill（foreign_trade 下 8 个 skill + skill_registry） | `app/services/hermes/`、`app/services/foreign_trade/` |
| 官网生成 | **部分存在**：site_builder orchestrator + jtbd_site_service | `app/services/site_builder/` |
| SEO/GEO/AEO | **已存在**：geo_engine、geo_rank_guard、aeo_fact_audit_service、eeat_scorer、seo_matrix | `app/services/geo/`、`app/services/seo/`、`foreign_trade/aeo_fact_audit_service.py` |
| 计费/钱包/台账 | **已存在**（且经 18 项 P0/P1 修复）：token_ledger、wallet、payment、finance_ledger、commission_settlement、referral | `app/models/`、`项目完成度盘点.md` |
| 匹配引擎/计算器/RFQ | **已存在并实测可用**：product-match、热工/防火/用量计算器、RFQ 自动评分 | `项目完成度盘点.md` |

### 1.3 GPT 文档要建而代码库确实缺失的（真差距）

| 缺失项 | 说明 |
|---|---|
| DeepSeek Harness Adapter | 全库 0 命中 `harness adapter`；且 DSH 仍为 developer preview，**只应定义接口+桩实现** |
| Model Gateway（能力路由） | 现有 `ai_engine.py` 是多 Provider 单例 + 硬编码优先级，无能力标签、无按调用记账、无统一熔断 |
| MCP Registry 持久化 | 现状是 `agent_hub_service.py` 里的**内存 list**（`_custom_mcp_servers`），重启即丢，无权限/凭证模型 |
| 统一 Policy Engine | paperclip 有 approval_gate/budget_guard 但仅覆盖自身；缺全局工具权限裁决 |
| Credential Vault | 无集中加密凭证库；渠道 OAuth/密钥散落各 service |
| 统一 Task Trace 表 | 有 request_id + OpenTelemetry，但缺"任务→Agent→Skill→模型→成本→结果"的一条链 Trace 表 |
| Evidence 证据引擎 | 发布类任务无外部状态校验/截图证据机制 |
| Browser/终端执行层 | 无 Playwright/CDP 执行运行时（开发工具链有浏览器，业务侧没有） |
| 全表 RLS | 租户隔离靠中间件 + 各 service 手动过滤（BUG-10 曾出现 RLS 注入阻断），未全表启用 PostgreSQL RLS |

---

## 二、纠错清单（GPT 文档错误，按严重度排序）

### 2.1 术语级错误（必须统一，否则 Codex 会建出两套系统）

| # | 错误 | 出处 | 纠正 |
|---|---|---|---|
| E1 | **ECC 一词两义且互相冲突**：中文文档全部把 ECC 当"企业专家库"；《ECC to Experience Engine》却定义 ECC = Execution Context Container（V8 隔离沙箱） | `ECC to Experience Engine.md` L3-15 vs 《AI 企业私有智能中心》十九 | 冻结：**ECC = 企业专家知识库（Expert Knowledge Base）**；沙箱执行另命名为 **Sandbox/Work Runtime**。两份文档合并时必须改名，否则权限模型会挂错层 |
| E2 | **Hermes 一词两义**：早期文档指 Nous Research Hermes 模型，后纠正为 DeepSeek Harness；但 `open GPT技术文档.txt` 又把 Hermes 定义为"平台运维（巡站/雷达/告警）"，与《私有智能中心》的"内部任务总调度器"职责漂移 | `open GPT技术文档.txt` L5 | 冻结：**Hermes = 代码库自有内部编排模块**（`app/services/hermes/`，已存在），职责=任务理解/拆解/路由/护栏；平台巡检并入 Hermes 子能力，不单列 |
| E3 | **Accio Work 定位错位**：GPT 文档把 Accio 当"终端执行器（浏览器/终端）"；代码中 `accio_sales_service.py` 实际是"找客/开发信/谈单草稿（画像+人审发送）"的**业务服务**，不是通用执行运行时 | 《私有智能中心》二十五 | 冻结：Accio = 外贸获客业务能力（已实现）；"终端执行器"是**另一个缺失模块**，命名 Browser Runtime，不得混用 |
| E4 | "DeepSeek Hermes" 与 "DeepSeek Harness" 混用 | 《AI Native…架构设计》开头 | 统一为 **DeepSeek Harness（DSH）**，且标注：developer preview，禁止生产硬依赖 |

### 2.2 技术栈级错误

| # | 错误 | 纠正 |
|---|---|---|
| E5 | GPT 文档规定前端 Next.js 15 + Shadcn | 现网前端是 **Nuxt 3 + Vue3**（300+ 页 + 401 页 admin），推倒重写=自杀。**冻结：保持 Nuxt 3**，文档中所有 Next.js 字样作废 |
| E6 | 消息队列写了 RabbitMQ | 现网用 **Redis + Celery**，删除 RabbitMQ，避免多一套中间件 |
| E7 | 部署写了 Kubernetes + Helm | 现网是 docker-compose 单机栈。MVP 阶段维持 compose；K8s 列为 V3 以后再评估 |
| E8 | 《CODEX TASK-001》要求新建 `ai-growth-os/` 仓库从零初始化 | **作废**。应改造现有仓库；新仓库会导致 224 张表、1616 个 API、401 页 admin 全部重来 |
| E9 | 文档默认 PostgreSQL 16/Redis 7 | 可用，但需记录：当前 PG 在 :5433（Docker），SQLite 模式仅为开发兜底且 **Celery 在 SQLite 模式不可用**——任务异步化验收必须在 PG+Redis 环境 |

### 2.3 架构级矛盾

| # | 矛盾 | 裁决 |
|---|---|---|
| E10 | 《私有智能中心》架构图把 DeepSeek Harness 放在最顶层当"外层 AI Operating Layer"；《AI Native》后期又纠正"Harness 只是 Adapter，SaaS Control Plane 才是主人" | 采纳后者：**本系统（优丁后端）= Control Plane**；Harness/DeerFlow/n8n/Browser 全部是 Execution Plane 的可替换 Adapter |
| E11 | **三套任务状态机并存**：①CODEX 文档（CREATED/QUEUED/PLANNING/RUNNING/WAITING/RETRYING/COMPLETED）②open GPT 文档（…/SUCCESS/FAILED/LEARNING）③代码 `deerflow/state_machine.py`（CREATED/PLANNING/EXECUTING/REVIEW/WAIT_HUMAN/DONE/FAILED/RETRY/CANCELLED） | 冻结以**代码现状③为基线**扩展（见 §4.2 统一状态机），另两套作废 |
| E12 | GPT 计费设计（MeterEvent→Pricing→Invoice）要求全新建 | 现网已有 token_ledger/wallet/payment/finance_ledger 且做完幂等/行锁/回滚自愈（18 项 P0/P1 修复）。**禁止重建**，只做 Metering 事件层补强（见 §4.8） |
| E13 | 《CODEX TASK》把 Evolution/Experience 排到 MVP-6"未来项" | 代码已有 `evolution/` 四件套+表。应提前为"接线"任务而非"新建"任务 |
| E14 | 文档称"AI 自动修改生产规则后必须 Canary"，但没说与哪个模块对接 | 对接现有 `evolution/canary.py`；补充：Canary 对象=SkillVersion/SOP，灰度维度=租户百分比（见 §4.7） |

### 2.4 文档卫生问题

| # | 问题 | 处置 |
|---|---|---|
| E15 | `AI_Global_Growth_OS_CODEX_TASK_001_013_V1.0第二部.md` 与第一部**字节级完全相同**（SHA256 一致，均 537,517 字节） | 删除其一，避免 Codex 重复执行 |
| E16 | 该文件 69,504 行内部存在拼接痕迹（一级标题"# AI Global Growth OS"出现 2 次，TASK-013 之后混入了 Skill/MCP/Registry/营销 Agent 等后续章节） | 拆分为《底座篇》《能力篇》两份，防止上下文超限与任务边界混乱 |

---

## 三、差距矩阵（GPT 设计 × 代码现状 × 动作）

| GPT 设计项 | 现状 | 动作 |
|---|---|---|
| TASK-001 项目初始化 | ✅ 已有 | **跳过**（改造现有仓库） |
| TASK-002 多租户 Schema | ⚠️ 有 tenant 中间件+部分过滤，无全表 RLS | **补强**：分域推进 RLS + Repository 层强制 |
| TASK-003 企业私有数据空间 | ⚠️ 有 uploads/ 与 minio/qiniu/r2 服务 | **补强**：对象存储键前缀规范 `tenants/{tid}/...` + 访问守卫 |
| TASK-004 Event Bus / Outbox | ⚠️ 有 `core/event_bus.py`，无 Outbox 表 | **新建**：outbox 表 + 中继 |
| TASK-006/007 Auth+RBAC | ✅ 已有（含 JWT 轮换、黑名单、防爆破） | **保留**，仅补 Agent 级权限位 |
| TASK-008 Task Schema | ⚠️ 分散在 DeerflowJob/PaperclipTask | **统一**：新 `ai_tasks` 主表+兼容视图 |
| TASK-009 状态机 | ✅ 已有（deerflow） | **采纳为基线**并统一 |
| TASK-010 Harness Adapter | ❌ 无 | **新建**：接口+桩（不依赖 preview 版本） |
| TASK-011 Hermes Adapter | ✅ 已有 runtime，但无标准契约 | **改造**：包一层 Protocol |
| TASK-012 Model Gateway | ⚠️ ai_engine 多 Provider 但无路由/记账 | **重构**：见 §4.3 |
| TASK-013 Trace | ⚠️ 有 request_id/OTel | **新建**：`task_traces` 链式表 |
| Skill/MCP/Plugin Registry | ⚠️ skill_registry(文件级)、MCP 内存 list | **新建**：三类注册表持久化+版本+权限 |
| Policy Engine / Credential Vault | ⚠️ paperclip approval_gate/budget_guard | **升级**：全局 Policy + KMS 化凭证库 |
| Browser Runtime | ❌ 无 | **新建**（V2 阶段，Playwright+CDP+租户 Profile 隔离） |
| Experience/Evolution | ✅ 已有 | **接线**：任务完成→ExperienceTrace→评估→Canary |
| 7 种变现计费 | ✅ 已有计费核心 | **补强**：统一 MeterEvent 埋点 |

---

## 四、超详细实现设计补充（在现有仓库落地）

### 4.1 目标分层（冻结版）

```
Control Plane（现有 FastAPI 单体，唯一真相源）
├── identity/tenant/rbac          ← 已有
├── task（统一任务控制面，新）     ← 收编 DeerflowJob/PaperclipTask
├── policy（Policy Engine，新）    ← 升级 paperclip approval_gate/budget_guard
├── credential（Vault，新）        ← 复用 core/field_crypto + gm_crypto
├── registry（Skill/MCP/Plugin，新）
├── billing（已有：wallet/token_ledger/payment/finance_ledger）
└── experience（已有：evolution/*，接线）

Execution Plane（全部 Adapter 化，可替换）
├── HermesAdapter   → app/services/hermes（已有，包 Protocol）
├── DeerFlowAdapter → app/services/deerflow（已有，补 executor TODO）
├── N8nAdapter      → app/services/n8n（已有）
├── HarnessAdapter  → 桩（等 DSH GA）
├── ModelGateway    → 重构 ai_engine
└── BrowserRuntime  → 新（V2）
```

### 4.2 统一任务状态机（以代码为基线冻结）

```
CREATED → PLANNING → EXECUTING → REVIEW → DONE
                        │           │
                        ├→ RETRY(≤3, 指数退避) ─┘
                        ├→ WAIT_HUMAN（验证码/支付/高风险发布，禁止无限重试）
                        ├→ FAILED / CANCELLED / TIMEOUT
终态：DONE / FAILED / CANCELLED / TIMEOUT
```

- 新增列：`idempotency_key`、`checkpoint_json`、`budget_used`、`retry_count`。
- 迁移落点：新迁移 `082_unify_ai_tasks.py`，建 `ai_tasks` 表；`deerflow_jobs`/`paperclip_tasks` 保留，双写过渡 2 个迭代后降级为从表。

### 4.3 Model Gateway 重构（基于 `ai_engine.py`，不推倒）

1. 新文件 `app/services/model_gateway/`：`router.py`（能力标签路由）、`ledger.py`（成本记账）、`adapters/`（langchain 包装）。
2. 能力标签表 `model_capabilities`：`reasoning/coding/vision/writing/translation/structured_output/cheap/fast`。
3. 调用协议：业务只传 `required_capabilities + budget`，Router 返回候选序列，逐个尝试，429/超时自动降级（现有 ai_engine 已有多 Provider 雏形，抽出来即可）。
4. **每次调用写 `model_call_ledger`**（tenant_id、task_id、model、input/output_tokens、cost）→ 汇总进现有 `token_ledger`，计费不用改。
5. 保留 `MVP_LAUNCH` mock 门：Gateway 增加 `MockAdapter`，行为与现 `ai_engine` 的 mock 分支一致。

### 4.4 Skill / MCP / Plugin 注册表持久化

- 新迁移建表：`skills`（含 version、input/output schema、permissions、状态 DRAFT/TESTING/ACTIVE/DISABLED/ROLLBACK）、`mcp_servers`、`mcp_tools`、`plugins`、`*_versions`。
- 迁移动作：`agent_hub_service._custom_mcp_servers` 内存 list → 落 `mcp_servers` 表（保留同名函数签名做兼容层）；`foreign_trade/skill_registry.py` 的 8 个技能灌入 `skills` 表作为种子。
- 权限精确到 `read/write/execute/delete/publish`；任何 Agent 默认 NO ACCESS，显式授权。

### 4.5 Harness / Hermes Adapter 契约

```python
# app/orchestration/interfaces.py（新目录）
class AgentRuntime(Protocol):        # Harness 与 Hermes 共同实现
    async def create_session(self, ctx: TenantContext, profile: str) -> str: ...
    async def execute(self, session_id: str, task: dict) -> dict: ...
class DeepExecutionRuntime(Protocol):  # DeerFlow
    async def submit/get_status/cancel/resume(...)
class DistributionChannel(Protocol):   # n8n/渠道
    async def validate/publish/status/analytics(...)
```

- `HarnessAdapter`：接口先行 + `NotImplementedError` 桩 + 特性开关 `HARNESS_ENABLED=false`；DSH GA 前一切流量走 HermesAdapter。
- Hermes 禁用权限集写入 Policy：`RAW_SHELL / RAW_DB_WRITE / RAW_HOST_FILESYSTEM / UNSCOPED_BROWSER / UNSCOPED_CREDENTIALS`。

### 4.6 租户隔离与 RLS 推进方案（不炸现有功能）

1. 第一步（低风险）：Repository 层统一 `TenantContext` 注入（现有 `core/tenant_access.py` 扩展），静态检查禁止无租户过滤的业务查询（CI grep 规则）。
2. 第二步：选 6 张高风险表试点 PostgreSQL RLS（`leads/prospects`、`email_outreach`、`content_master`、`wallet`、`token_ledger`、`ubrain_tenant_memory`），策略用 `current_setting('app.tenant_id', true)`；**连接池钩子**：每次 checkout 设置、checkin 重置（`RESET app.tenant_id`），避免跨租户污染——这是 BUG-10 的根因防线。
3. 第三步：全表推开（每迭代 20 张），配套 `tests/security/test_tenant_isolation.py` 双租户穿透测试。
4. 对象存储：键前缀强制 `tenants/{tenant_id}/`，上传/下载走统一签名网关（复用现有 media_* 服务收口）。

### 4.7 Trace / Experience / Evolution 接线

- 新表 `task_traces`：`trace_id / task_id / tenant_id / agent_id / skill_id / skill_version / model / prompt_ref / tool_calls / result / cost / latency_ms / status`（prompt 正文存对象存储，表内只存引用，防爆库）。
- 接线：`ai_tasks` 终态钩子 → 写 `task_traces` → `evolution/experience_store.py` 收录（分级：Raw Trace → Validated Experience → Reusable Pattern → SOP → Skill，**非全部入库**，评估器阈值控制）。
- 失败经验：`failure_type/root_cause/skill_version` 入 `ExperienceEntry(kind='failure')`。
- 发布门禁：`Experience → SkillVersion(DRAFT) → 离线评估 → Canary 5%→25%→50%→100%（对接 evolution/canary.py，按租户百分比）→ 人工批准 → ACTIVE`。**禁止 AI 直接改生产规则**。

### 4.8 Revenue OS 补强（不重建，只埋点）

- 新表 `meter_events`（append-only）：`tenant_id / meter / quantity / unit / ref_id / ts`；业务侧在 7 个动作处埋点：ai_generation、content_publish、lead_generated、rfq_created、api_call、export、video_job。
- 汇总 Worker（Celery beat）：meter_events → 现有 `token_ledger`/`wallet` 扣减 → `finance_ledger` 入账；套餐配额检查走现有 `plan_gate_service`。
- 发票/订单/佣金沿用现有 `invoice_application`/`order`/`commission_settlement`，零重建。

### 4.9 Browser Runtime（V2，缺什么补什么）

- 技术：Playwright + CDP，容器化 `browser-worker`，每租户独立 Profile（cookies/storage 隔离），出站走现有 egress 服务。
- 合规红线（写死在 Policy）：**官方 API 优先**；仅对允许自动化的平台执行；模拟登录/绕验证码一律转 `WAIT_HUMAN`；凭证从 Credential Vault 短期下发，Agent 拿不到原始密钥。

### 4.10 新增迁移清单（alembic，按序）

| 迁移 | 内容 |
|---|---|
| 082_unify_ai_tasks | ai_tasks 主表 + 状态机枚举 + idempotency_key + checkpoint |
| 083_registries | skills / skill_versions / mcp_servers / mcp_tools / plugins / plugin_versions |
| 084_model_gateway | model_capabilities / model_call_ledger |
| 085_traces | task_traces + evidence（证据：外部 URL/截图引用/校验结果） |
| 086_meter_events | meter_events + 索引（tenant, meter, ts） |
| 087_credential_vault | credentials（SM4 加密，复用 gm_crypto）+ 授权关系表 |
| 088_rls_pilot | 6 张试点表启用 RLS + 策略 + 连接池钩子 |

---

## 五、修订后的开发路线（替代 GPT 的 TASK-001 全量清单）

| 阶段 | 内容 | 验收 |
|---|---|---|
| P0 契约层（1-2 周） | 4.5 接口 + 4.2 状态机统一 + Outbox | 一个任务从 API→Hermes→DeerFlow→终态→trace 全链路跑通（PG+Redis 环境） |
| P1 注册表与网关（2-3 周） | 4.4 三类注册表持久化 + 4.3 Model Gateway + 成本记账 | 换模型只改配置；每任务成本可查 |
| P2 安全收口（2-3 周） | 4.6 RLS 试点 + 4.7 Policy/Vault | 双租户穿透测试 0 泄漏；渠道密钥全部入库加密 |
| P3 经验飞轮接线（2 周） | 4.7 Trace→Experience→Canary | 一条真实任务产生经验条目并走完灰度门禁 |
| P4 商业化埋点（1-2 周） | 4.8 MeterEvent | 7 类动作计量与现有账单对账误差为 0 |
| P5 浏览器执行层（V2） | 4.9 Browser Runtime | 单租户单渠道合规发布 + 证据回传 |

## 六、验收红线（沿用并强化文档中 Codex 规则）

1. 每任务必须过：单测 / 集成 / mypy / ruff / 多租户隔离测试，输出 PASS/FAIL，禁止"应该可以"。
2. 任何第三方 Runtime 只经 Adapter；业务层零 `import deepseek_*`。
3. AI 建议一律 Draft→评估→Canary→人审，禁止直接改生产。
4. 长任务必须可恢复（checkpoint），禁止 `while True` 无限执行。
5. 所有模型调用必须落成本账；超预算即停并转人审。

---

## 附：一句话总结

GPT 文档给了正确的"目的地"（Control Plane / Execution Plane / 经验飞轮），但把"起点"写错了——**本项目的起点是一个已有 224 张表、含 Hermes/DeerFlow/n8n/Evolution/计费的存量系统**。正确执行方式是：作废重建式 TASK-001 清单，按本报告 §四 的 8 项改造（统一任务面、模型网关、注册表持久化、Adapter 契约、RLS、Trace 接线、计费埋点、浏览器层）增量演进。
