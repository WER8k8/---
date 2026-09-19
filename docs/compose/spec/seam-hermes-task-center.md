---
feature: seam-hermes-task-center
status: delivered
updated: 2026-09-19
branch: feat/seam-hermes-task-center
commits: 33fb5aea..07609e6d0a46f35af1e82b6c395cc20f3802d300
---

# SEAM-P0：Hermes 任务中心（功能域完整体驱动）

## Report

**What was built** — 优丁租户侧「Hermes 任务」功能域页（/client/tasks）：列出 hermes_plan 计划（含 GP-A 黄金路径/状态/节点摘要），抽屉查看子节点执行器与能力；GET /orchestration/hermes/tasks 与 /{plan_id} 读 i_tasks；GP-A 响应的 plan_id（TaskGraph id）可反查详情；履约队列「一键履约 · Hermes」提交后跳转任务中心。

**Verification** — pytest seam+annex **PASS**；live：golden-path/fulfillment → L1_template nodes=9；hermes/tasks?golden_path=GP-A 列表可见；详情按 graph.plan_id 可查节点。

**Journey log** — ① plan_id 勿与 ai_tasks 主键混淆，详情须按 idempotency/graph.plan_id 解析。② 双平面：任务中心=交互读、一键履约=任务写。③ 菜单无特权，业务名「Hermes 任务」。

## [S1] Problem
一键 PI/履约后优丁内看不到任务图，功能域像只改菜单名（完整体 S4）。

## [S2] Design
- API：/orchestration/hermes/tasks 列表 + /{plan_id} 详情（租户隔离）。
- UI：/client/tasks + 菜单「Hermes 任务」；履约提交后 outer.push(/client/tasks?plan=)。
- plan_id = TaskGraph.plan_id；详情兼容 idempotency_key=plan:{id} 与 input.plan_id。

## [S3] Out of Scope
附属独立台；外部 Key 真发；admin 超管专属任务台（可用 client 路径即可）。

## Tasks
- [x] T1: 后端 hermes 任务列表/详情 API — acceptance: 租户内 plan+节点（covers: S2）
- [x] T2: 前端 /client/tasks — acceptance: 列表/详情/?plan=（covers: S2; depends: T1）
- [x] T3: 菜单与履约闭环 — acceptance: 菜单 Hermes 任务；GP-A 后跳转（covers: S2; depends: T2）
- [x] T4: 测试与 live 验证 — acceptance: pytest 3 passed + live GP-A/DETAIL/LIST（covers: S2）

