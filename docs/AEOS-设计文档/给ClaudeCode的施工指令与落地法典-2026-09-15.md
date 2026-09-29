# 给 Claude Code 的施工指令与落地法典 · 生产上线冲刺版

> **发起方**：Antigravity 谷歌首席架构师 × 系统工程组  
> **接收执行方**：Claude Code（命令行 / CLI / IDE 专属施工工程师）  
> **制定时间**：2026-09-15 04:35:00  
> **文档性质**：最高优先级施工交接任务书（P0 级精准修复 + 生产准入攻坚）  
> **协作铁律**：**先探后写（Probe Before Write）、一行代码原则、交付求真、不假交付**。

---

## 目录
- [0. 核心交接背景与当前状态](#0-核心交接背景与当前状态)
- [1. 不可撼动的两大最高工程铁律与五大硬锁](#1-不可撼动的两大最高工程铁律与五大硬锁)
- [2. 任务包一（P0 · 立即执行）：补齐 7 大 L1 模板，使测试 618/618 全绿](#2-任务包一p0--立即执行补齐-7-大-l1-模板使测试-618618-全绿)
- [3. 任务包二（P0 · 立即执行）：修复数据类型与多租户定序暗病](#3-任务包二p0--立即执行修复数据类型与多租户定序暗病)
- [4. 任务包三（P0 · 准备上线）：207 张空表注水与计费真闸门开启](#4-任务包三p0--准备上线207-张空表注水与计费真闸门开启)
- [5. Claude Code 专属自检验证命令集（必须全绿）](#5-claude-code-专属自检验证命令集必须全绿)

---

## 0. 核心交接背景与当前状态

经过谷歌工程总监级实代码深度盘查：
1. **现状与优势**：
   - 全系统 24 个执行器声明的 52 项原子能力在 `ExecutorRegistry` 中 100% 在册；
   - Admin 前端 96 条业务菜单路由 Playwright 客户端直通巡检 **96/96 PASS（0 Failures / 0 Warnings）**；
   - 数据库 234 张表物理运行在原生 PostgreSQL 15.8 @5433，Alembic 单 head 为 113；
   - 基础门禁脚本（`verify_executors.py` 24/24 PASS, `orchestration_selfcheck.py` 19/19 PASS, `fake_scan.py` HIGH=0）。
2. **当前断点与瓶颈**：
   - 刚跑完的后端全量 pytest 测试套件：**618 items 中 594 passed / 23 failed**；
   - 这 23 个测试失败的原因完全查明：**单测写了 7 大 L1 模板的断言，但 `planner_service.py` 中遗漏了这 7 个图的实现**！
   - 本交接书的目标就是指导 Claude Code 用最快速度清零这 23 个失败，并清除数据库 UUID 与多租户的暗病，直奔公网生产上线。

---

## 1. 不可撼动的两大最高工程铁律与五大硬锁

### 1.1 两大铁律（违反即返工）
- **铁律一：彻底搞清代码库里有什么**：
  绝不凭空手搓新文件！24 个执行器已在 `backend/app/services/hermes/executors/`，76 个 Skill 已在 `skills/`，156 个路由模块已在 `routes/`。
- **铁律二：每次写代码必须“先探后写”（Probe Before Write）**：
  动代码前必须跑 `tools/probe.py`、`tools/capability_ledger.py`、`tools/verify_executors.py`，绝不盲目开敲。遵循**“一行代码原则”**。

### 1.2 五大硬锁（绝对红线）
1. `LOGIN-LOCK-01`：唯一登录路由 `/login`，禁止创建第二套登录页；
2. `ROLE-SHELL-LOCK-01`：四壳固定（`/client/*`, `/admin`, `/partner`, `/agent/*`）；
3. `DESIGN-TOKEN-LOCK-01`：管理后台薄荷绿 `#4a9b8c` 单真源，严禁改杂色；
4. `SYSTEM-LOCK-02`：八大子系统法定不可裁减；
5. `ENV-LOCK-01`：数据库为原生 PG 15.8 @5433（单 head 113），严禁切回 SQLite。

---

## 2. 任务包一（P0 · 立即执行）：补齐 7 大 L1 模板，使测试 618/618 全绿

### 2.1 故障根因与文件定位
- **受影响测试**：
  - `backend/tests/unit/test_planner_fulfillment.py`（7 个失败）
  - `backend/tests/unit/test_planner_undriven_drivers.py`（16 个失败）
  - `backend/scripts/verify_hermes_executor_coverage.py`（报错 `ImportError: cannot import name '_fulfillment_graph'`）
- **核心文件**：[`backend/app/services/hermes/planner_service.py`](file:///c:/Users/Administrator/Documents/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend/app/services/hermes/planner_service.py)

### 2.2 实施方案：在 `planner_service.py` 补齐 7 个模板生成函数

请在 `planner_service.py` 中导出并实现以下 7 个 TaskGraph 模板函数，并挂入 `_TEMPLATES` 匹配逻辑：

#### ① `_fulfillment_graph(plan_id: str, event_id: str, payload: dict) -> TaskGraph`
- **业务**：外贸 7 步履约与单证套打全闭环（严格 8 个节点）：
  - `n1`: `inquiry.capture`（执行器 `inquiry`）
  - `n2`: `order.create`（执行器 `order`，`depends_on=["n1"]`，`input_from={"inquiry_id": "n1.output.inquiry_id"}`）
  - `n3`: `document.generate_pi`（执行器 `goodjob_crm`，`depends_on=["n2"]`，`input_from={"order_id": "n2.output.order_id"}`）
  - `n4`: `billing.meter`（执行器 `billing`，`depends_on=["n3"]`，定金核销，`input_from={"order_id": "n2.output.order_id"}`）
  - `n5`: `crm.sync_stage`（执行器 `goodjob_crm`，`depends_on=["n4"]`，生产阶段推进）
  - `n6`: `document.generate_trade_docs`（执行器 `goodjob_crm`，`depends_on=["n5"]`，CI/PL 箱单）
  - `n7`: `logistics.track`（执行器 `logistics`，`depends_on=["n6"]`，海运物流轨迹）
  - `n8`: `billing.meter`（执行器 `billing`，`depends_on=["n7"]`，尾款核销）
- **触发意图**：含 `履约`、`生成PI`、`跟踪物流`、`订单物流`、`出PI`、`发货`。

#### ② `_social_outreach_graph(...) -> TaskGraph`
- **业务**：全网社媒与 WhatsApp 矩阵拓客：
  - `n1`: `prospect.scrape`（执行器 `trade_ai_agent`）
  - `n2`: `outreach.whatsapp`（执行器 `trade_ai_agent`，`depends_on=["n1"]`）
  - `n3`: `inbox.classify`（执行器 `trade_ai_agent`，`depends_on=["n2"]`）
- **安全阀**：`approval_required=["outreach.whatsapp"]`（触达高危动作必须人审挂起）。
- **触发意图**：含 `whatsapp`、`社媒`、`私域`。

#### ③ `_product_launch_graph(...) -> TaskGraph`
- **业务**：产品上架全链路：
  - `n1`: `product.create`（执行器 `product`）
  - `n2`: `media.render`（执行器 `media`，`depends_on=["n1"]`）
  - `n3`: `seo.optimize`（执行器 `seo`，`depends_on=["n2"]`）
  - `n4`: `engagement.send`（执行器 `engagement`，`depends_on=["n3"]`）
- **安全阀**：`approval_required=["engagement.send"]`。
- **触发意图**：含 `发布新产品`、`产品上架`。

#### ④ `_research_analysis_graph(...) -> TaskGraph`
- **业务**：市场研析与海关数据推理：
  - `n1`: `research.deep_run`（执行器 `research`）
  - `n2`: `wangcai.ask`（执行器 `wangcai`）
  - `n3`: `ai.reason`（执行器 `ai_engine`，`depends_on=["n1", "n2"]`）
- **触发意图**：含 `市场分析`、`海关数据`、`可行性分析`。

#### ⑤ `_lead_generation_graph(...) -> TaskGraph`
- **业务**：Geo 拓客与价值计费：
  - `n1`: `lead.search`（执行器 `lead`）
  - `n2`: `browser.scrape`（执行器 `browser`，`depends_on=["n1"]`）
  - `n3`: `billing.meter`（执行器 `billing`，`depends_on=["n2"]`）
- **触发意图**：含 `拓客`、`线索`、`买家挖掘`。

#### ⑥ `_browser_evidence_graph(...) -> TaskGraph`
- **业务**：浏览器合规取证与垂直论坛获客：
  - `n1`: `browser.scrape`（执行器 `browser`）
  - `n2`: `forum.post`（执行器 `forum`，`depends_on=["n1"]`）
- **触发意图**：含 `取证`、`论坛`、`竞品追踪`。

#### ⑦ `_ubrain_assistant_graph(...) -> TaskGraph`
- **业务**：知识库与大模型对话：
  - `n1`: `ubrain.chat`（执行器 `ubrain`）
  - `n2`: `ai.chat`（执行器 `ai_engine`，`depends_on=["n1"]`）
- **触发意图**：含 `ubrain`、`知识库`、`外贸助手`。

### 2.3 验证目标
改完后执行：
```bash
python scripts/verify_hermes_executor_coverage.py
# 👉 期望：24 个执行器全部被驱动！退出码 0

& .\.venv\Scripts\python.exe -m pytest tests/unit/test_planner_fulfillment.py tests/unit/test_planner_undriven_drivers.py
# 👉 期望：23 个失败全部转绿！
```

---

## 3. 任务包二（P0 · 立即执行）：修复数据类型与多租户定序暗病

### 3.1 修复 `model_call_ledger` UUID 转换报错
- **文件**：`backend/app/services/model_gateway/ledger.py`
- **问题**：向 `model_call_ledger` 写入 `tenant_id` 时，当传入 mock 字符（如 `"t1"`）时，PostgreSQL 抛出 `invalid input syntax for type uuid: "t1"`。
- **修复方法**：在写入 SQL 或 ORM 前，校验 `tenant_id` 是否为合法 UUID；若不是，使用 `uuid.uuid5(uuid.NAMESPACE_DNS, str(tenant_id))` 安全转换为确定性 UUID，或置为 NULL，禁止让 PG 抛出语法错误。

### 3.2 修复多租户非确定性上下文（Non-Deterministic Tenant Context）
- **文件**：`backend/app/services/tenant_scenario_service.py` L152-L157
- **问题**：`resolve_tenant_id_for_user` 中使用了无定序的 `.first()`。
- **修复方法**：
  ```python
  # 改为有明确时间倒序的确定性解析：
  link = (
      db.query(UserTenant)
      .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
      .order_by(UserTenant.created_at.desc())
      .first()
  )
  ```

### 3.3 消除 TradeAI 明文凭据警告
- **文件**：`backend/config/dev/.env`
- **修复方法**：生成并配置 `CREDENTIAL_ENCRYPTION_KEY`：
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  填入 `.env`，确保海外社媒账号密码落库为 AES/Fernet 密文。

---

## 4. 任务包三（P0 · 准备上线）：207 张空表注水与计费真闸门开启

### 4.1 执行 207 张空表注水工程（`seed.py`）
- 编写/增强 `backend/seed.py`，向以下外贸核心业务表注入基准数据：
  1. `hs_code_mappings`：注入 100 条建材、五金、机电 HS 海关编码与关税税率；
  2. `product_boq_profiles`：注入建材 22 参数（容重、厚度、导热系数、集装箱排柜容积）基准字典；
  3. `exchange_rate_logs`：注入 USD、EUR、SAR（沙特里亚尔）、AED（阿联酋迪拉姆）汇率快照；
  4. `proforma_invoice_templates`：注入国际商会英文形式发票排版模版。
- 目标：将有数据的表从 27 张提升到 60 张以上，运行 `python tools/db_probe.py --density` 检验。

### 4.2 生产计费闸门开启（关闭白嫖模式）
- **文件**：`backend/app/core/config.py` 与 生产配置
- **操作**：
  将 `TASK_CONTROL_ENABLED` 从 `False` 切换为 `True`；
  测试钱包扣减链路：当租户 Token 余额为 0 时，Hermes 调度器正确挂起并返回 402 告警，彻底筑牢资损防线。

---

## 5. Claude Code 专属自检验证命令集（必须全绿）

在完成上述修改后，Claude Code 必须在根目录下完整运行以下自检链条：

```powershell
# 1. 验证 24 执行器白名单与 52 能力契约
python tools/verify_executors.py

# 2. 验证执行器 100% 被驱动脚本
python 上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\scripts\verify_hermes_executor_coverage.py

# 3. 验证静态编排冒烟全绿
python tools/smoke_orchestration.py

# 4. 验证全景架构 19 项红线门禁全绿
python 上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend\scripts\orchestration_selfcheck.py

# 5. 验证后端全量测试套件（必须 618/618 PASS，0 FAILURES）
cd 上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend
.\.venv\Scripts\python.exe -m pytest -q --tb=line -m "not slow"
```

---

> **【致 Claude Code 的一句话】**：  
> 优丁的发动机和骨架已经由 Antigravity 团队全部打磨完毕。请严格执行本法典的任务包一与任务包二，将 23 个测试清零，把暗病消灭，我们即可携手向用户交付一个真正具备商业化公网实力的外贸 AI 操作系统！
