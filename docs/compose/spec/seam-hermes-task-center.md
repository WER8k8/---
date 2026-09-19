---
feature: seam-hermes-task-center
status: in-progress
updated: 2026-09-19
branch: feat/seam-hermes-task-center
commits: 33fb5aea..<head>
---

# SEAM-P0：Hermes 任务中心（功能域完整体驱动）

## Report

## [S1] Problem
一键 PI/履约已能提交 Hermes，但优丁内**看不到**任务图/节点/状态，功能域仍像「改菜单名」；完整体要求 S4：任务与证据在优丁任务中心可见。

## [S2] Design
- **交互平面**：`GET /orchestration/hermes/tasks`、`GET /orchestration/hermes/tasks/{plan_id}`（租户隔离，读 `ai_tasks`）。
- **任务平面**：`golden-path/fulfillment|outreach` 派发后，前端进入 **Hermes 任务中心** 查看 plan 与子节点。
- **UI**：`/client/tasks`（及 admin 可达），业务名「Hermes 任务」，**无特权**；列表+详情+按 plan 过滤。
- **契约**：列表含 `plan_id`（parent 任务 id）、`status`、`node_count`、`graph_source`/`golden_path`（来自 input_json）、`error` 摘要；子节点 `hermes_node:*` 挂 parent。
- **闭环**：fulfillment 页提交 GP-A 后展示 plan_id，并提供「查看任务」跳转 `/client/tasks?plan=`。

## [S3] Out of Scope
- 附属独立后台；外部 Key 真发；P3 前端归档。

## Tasks
- [ ] T1: 后端 hermes 任务列表/详情 API — acceptance: 按租户返回 plan 与节点，契约字段齐全（covers: S2）
- [ ] T2: 前端 `/client/tasks` 任务中心页 — acceptance: 可列表/刷新/看节点状态，支持 `?plan=`（covers: S2; depends: T1）
- [ ] T3: 菜单与履约页闭环 — acceptance: 菜单「Hermes 任务」；履约提交后可跳转任务中心（covers: S2; depends: T2）
- [ ] T4: 测试与门禁 — acceptance: pytest + verify 脚本绿（covers: S2）
