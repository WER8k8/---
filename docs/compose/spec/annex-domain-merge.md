---
feature: annex-domain-merge
status: delivered
updated: 2026-09-19
branch: feat/annex-domain-merge
commits: f76947e4f6d985680cec2bf860c9fe0ac836ae7e..<pending-path-filtered-commit>
---

# 附属功能域融入优丁（GoodJob + TradeAI）

## Report

**What was built** — GoodJob/TradeAI 以**功能域菜单**（社媒拓客 / 外贸履约，无特权）并入优丁；身份侧 login/超管/管理台生产 410（保留 annex-ticket + uj-bridge）；Hermes 双平面契约（交互 API vs 任务 L1，DSH 非必经）；黄金路径 API：`POST /api/v1/orchestration/golden-path/fulfillment`（GP-A）与 `/outreach`（GP-B），履约队列页「一键履约 · Hermes」与 PI 动作接入任务面；TradeAI 技能名进入 planner 白名单；协议审计文档落盘。

**Verification** — `pytest` annex/planner 相关 **PASS**；`verify_annex_domain_merge.py` / `verify_annex_work_mode.py` / `verify_annex_identity_strip.py` **PASS**；`orchestration_selfcheck` **19/19**；评审后修复：可移植路径、`${msg}`、订单上下文按钮、去除「附属一/二」残留文案。

**Journey log** — ① Compose 工作区：智能判断→当前 AGENTS 路径 + `feat/annex-domain-merge`（非嵌套 worktree）。② 范围：智能判断→P0 收口 + GP-A 闭环 + P1 核心（非 P0–P3 全量）。③ 评审 critical：未提交混入无关脏文件→提交须 path-filter；live HTTP 依赖后端进程。④ 剥身份在 `_external`，主仓门禁为静态标记+可移植路径。⑤ 旧「附属执行台」叙事已从业务菜单与能力描述移除。

## [S1] Problem
GoodJob 与 TradeAI 需成为优丁**完整体功能域**（无隔阂、无特权菜单、Hermes 无缝驱动），而非第二套可登录系统。

## [S2] Design
- **双平面**：交互 CRUD → UJ API；任务面 → Hermes（默认 L1，DSH 非必经）。
- **功能域菜单**：社媒拓客 / 外贸履约，`privileged:false`，UJ RBAC。
- **身份**：附属 login/platform/admin → 410；保留 annex-ticket + uj-bridge。
- **GP-A**：`POST /orchestration/golden-path/fulfillment` → L1 `_fulfillment_graph`（含 goodjob_crm）。
- **GP-B**：`POST /orchestration/golden-path/outreach` → trade_ai_agent L1；技能进 FALLBACK 白名单。
- **协议审计**：`docs/annex-protocol-audit-2026-09-19.md`。
- **数据**：真相仅优丁 PG；无 Key 诚实 failed。

## [S3] Out of Scope
- 附属独立前端物理归档（P3）；外部 Key 真发；GoodJob Node Python 化；新建嵌套 git worktree。

## Tasks
- [x] T1: GP-A 一键履约 API — acceptance: golden-path/fulfillment 路由 + L1 含 goodjob_crm（covers: S2）
- [x] T2: 履约队列 Hermes 按钮 — acceptance: fulfillment.vue 调用 GP-A API，展示 plan_id（covers: S2; depends: T1）
- [x] T3: TradeAI 技能白名单 — acceptance: trade_ai.* / skill.social_scraper 在 FALLBACK_CAPABILITIES（covers: S2）
- [x] T4: 复合航道契约测试 — acceptance: golden_path helper + verify_annex_work_mode 全绿（covers: S2）
- [x] T5: 协议/出处审计文档 — acceptance: docs/annex-protocol-audit-2026-09-19.md（covers: S2）
- [x] T6: 门禁与回归 — acceptance: pytest annex+planner、verify_annex_*、selfcheck 19/19（covers: S2）
