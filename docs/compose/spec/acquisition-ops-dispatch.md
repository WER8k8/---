---
feature: acquisition-ops-dispatch
status: delivered
updated: 2026-09-18
branch: feat/acquire-mobius-20260918
commits: 5d08166c..7ce2b087d9a8
---

# 作战台一键派发编排（compose-next#3）


## Report

**What was built** — 作战台「智能派发」：`POST /acquisition/dispatch` 复用 planner.decompose + （可选）parse_graph_to_tasks/advance_plan；前端预览后「确认派发」；询盘卡 stage=orchestrated 并写入 plan 备注；经验事件 ops_dispatch。派发结果诚实：无 DB 或 advance 失败时 dispatched=false 并说明原因。

**Verification** — pytest 获客全量（dispatch+persist+compose+e2e+planner+service）**51/51 PASS**；评审 0 CRITICAL；硬锁 ROUTE_PREFIX / get_current_user / 登录 / 薄荷主色未破。

**Journey log**
1. 预览与派发分开关：auto_dispatch=false 只出图，不假装已调度。
2. stage=orchestrated 作为派发后跟单卡契约。
3. dispatched 标志必须反映真实 advance 结果。
4. 派发失败仍保留已入库 plan 信息，便于排查。
5. 复用 orchestration 同链，不新建第二套编排入口。
## [S1] Problem

作战台已能预览任务图，但「干到底」需要**一键派发**：预览后可选真派发到爱马仕/任务面；失败要诚实，不能假装 dispatched。主理人要求 compose-next 一口气交付。

## [S2] Design

**工作区**：沿用 `agents-acquire-mobius-20260918-011631`。

**契约**：

1. `POST /acquisition/dispatch`（鉴权 get_current_user + Depends(get_db)）
   - Body：`{intent, tenant_id?, channel?, payload?, inquiry_id?, auto_dispatch}`
   - 流程：
     a. `planner_service.decompose(IntentEvent, db)` → graph + source  
     b. 若 `auto_dispatch` 且 db 可用：`parse_graph_to_tasks` + `advance_plan`（与 orchestration from-intent 同链）  
     c. 若 inquiry_id：materialize/update ops card stage=`orchestrated`，备注 plan_id/source  
     d. `record_acquisition_event(event="ops_dispatch", success=dispatched or not auto_dispatch)`  
   - 响应：`{plan_id, graph_source, node_count, nodes[], dispatched, task_ids[], persistence_note, experience, card?}`
   - 失败：拆解失败 422；落库失败 500；`auto_dispatch=False` 时只预览图并 `dispatched=false`

2. 前端 `acquisition-ops.vue`
   - 预览弹层增加「确认派发」→ `dispatchAcquisition({..., auto_dispatch:true})`
   - 成功提示：`已派发 plan_id / n 个节点`；失败显示原因
   - 发现 inquiry_id 时尝试刷新跟单卡

3. `api/acquisition.ts`：`dispatchAcquisition`

4. 测试
   - dispatch 无 db / auto_dispatch=false：返回 nodes + dispatched=false  
   - dispatch 与 mock decompose 成功：plan_id 存在  
   - 旧测试不回归  

5. 硬锁：不改登录/壳/主色；`ROUTE_PREFIX=""`；不新建平行编排入口（dispatch 内部复用 planner + supervisor）。

## [S3] Out of Scope

- Celery worker 实机执行 24 执行器业务逻辑  
- 生产 PG / 真实 ai_tasks 表结构变更  
- 前端 E2E 浏览器自动化  
- 合并 main  

## Tasks

- [x] T1: dispatch API + 调度串联 — acceptance: auto_dispatch=false 返回图；有 db 时可 attempt parse/advance (covers: S2.1)
- [x] T2: 前端确认派发按钮 — acceptance: 预览后可调用 dispatch 并提示结果 (covers: S2.2)
- [x] T3: 单测 — acceptance: 新测+旧测全 PASS (covers: S2.4)
- [x] T4: spec Report + 第二大脑 — acceptance: delivered (covers: S2; depends: T3)
