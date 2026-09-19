---
feature: hermes-drive-chain-deep-dive
status: delivered
updated: 2026-09-20
branch: feat/hermes-deep-dive
commits: 6e841e23..309ebc61
---

# Hermes 驱动链路深挖（四轨完整体）

## Report

**What was built** — 在 Hermes 可派发基线之上完成四轨深挖：① **L1 节点业务闭环**——`content_deep.seo_meta` 去掉不可达 except，引擎不可用诚实 `degraded`（含 `engine_error`）；`content_deep.knowledge` 存储不可用降级摘要；acquisition 缺实体 honest skip；单测覆盖 degraded/failed/引擎失败分支。② **GP-B 完整体前端**——社媒拓客功能域 `AnnexEmbedPage` 增「一键触达 · Hermes」，外贸履约域增「一键履约 · Hermes」；`api/orchestration.ts` 暴露 `goldenPathFulfillment` / `goldenPathOutreach`；成功跳转 `/client/tasks?plan=`。③ **询盘第二任务面路径**——`inquiries.vue` 详情保留交互「生成 PI」，新增「Hermes 履约」提交 GP-A（payload 带 inquiry 上下文）并跳转任务中心。④ **真桥与附属进程**——GoodJob `GOODJOB_BASE_URL`（5188/4188 双端 `/api/health` 与 `/api/uj-bridge/health` 均 200）；TradeAI `:8010` 以本地 SQLite 起服，health `identity=uj-annex`，login **410**（设计内剥身份）；未配置桥路径保持诚实 failed。另补 `WorkbenchItemDef.domain/privileged` 可选字段以清掉 annex 注册表 typecheck 阻塞。

**Verification** — pytest `test_hermes_deep_batch3` + annex 相关 **PASS**（含引擎不可用/degraded 新用例）；`verify_annex_domain_merge` / `verify_annex_work_mode` / `verify_annex_identity_strip` **全过**；`orchestration_selfcheck` **19/19**；`hermes-drive-chain-manual-e2e.ps1` **36/36**（task_avg≈183ms）；live 节点抽样：`knowledge_seo` 四节点全 `done`（非配置缺）；GP-B 在 TradeAI 起服后 `prospect.scrape=executing`，`outreach.whatsapp=wait_human`（审批闸，设计内）；GP-A `order.create`/`document.generate_pi` 人审闸 `wait_human/paused`；admin `npm run typecheck` **PASS**。独立 Review：无 critical；残留为文档化口径（见 Journey）。

**Journey log** — ① 驱动链路验收不能只看 `dispatched=true`：须读节点 `status/error`，区分审批闸（wait_human）、诚实 degraded、配置缺 failed。② `knowledge_seo` 曾 `created` 滞后，advance_plan 推进后全 done——是调度时序不是业务洞。③ GoodJob 端口：文档/example 写 API **4188**，`connect_external_bridges` 与 runtime env 用 **5188**；实测两端 `/api/uj-bridge/health` 皆 200，未配置仍诚实 failed。④ TradeAI 本地无头：`DATABASE_URL=sqlite` + 项目根 `.env.dev`；真相仍在优丁 PG。⑤ 审批闸 `wait_human` 是黄金路径契约（PI/order/whatsapp），勿当故障修掉。

## [S1] Problem
Hermes 驱动链路已能 L1 派发且任务中心可读，但深挖仍有隔阂：① 节点级业务结果未系统分类（配置缺 vs 代码洞 vs 诚实降级），`knowledge_seo` 等场景节点质量不稳；② GP-B 仅有 API，社媒拓客功能域无「一键触达 · Hermes」；③ 询盘页 PI 仍走交互接口，未接任务面 GP-A；④ GoodJob/TradeAI 真桥与本地进程未收口，`GOODJOB_BASE_URL`/TradeAI:8010 缺失时应诚实 failed 且可本地验证。

## [S2] Design

### 双平面与黄金路径（不变）
- 交互 CRUD → 优丁 API 同步；多步/外发/单证 → Hermes L1（DSH 非必经）。
- GP-A：`POST /api/v1/orchestration/golden-path/fulfillment` → `_fulfillment_graph`。
- GP-B：`POST /api/v1/orchestration/golden-path/outreach` → `_social_outreach_graph`（trade_ai_agent 三能力）。
- 任务中心：`/client/tasks`；plan_id = TaskGraph.plan_id；详情兼容 `plan:{id}`。
- 无特权：菜单为业务功能域名；禁止附属第二登录/特权壳。

### 轨 A · L1 节点业务闭环
- 验收不只 `dispatched=true`：复跑 S1–S16，记录每节点 `status ∈ {succeeded, degraded, failed, skipped}` 与 error 语义。
- 允许：`degraded`+说明、`failed`+`not_configured`/`bridge_disabled`/明确业务错误、审批闸 `wait_human`。
- 禁止：5xx 裸崩、静默 success、死代码 except 吞掉真实错误路径。
- 代码契约：
  - `content_deep.seo_meta`：引擎不可用 → 模板 `degraded`（如实 + `engine_error`）；缺 product_name → `failed`。
  - `content_deep.knowledge`：队列存储不可用 → `degraded` 摘要（pending=0 + note）。
  - `content_deep.acquisition`：缺 content_id/inquiry_id → `degraded` honest skip。

### 轨 B · GP-B 功能域前端
- 落点：`AnnexEmbedPage.vue`（trade-ai「一键触达 · Hermes」；goodjob「一键履约 · Hermes」）。
- 行为：`goldenPathOutreach` / `goldenPathFulfillment` → 成功 `router.push(/client/tasks?plan=)`；失败展示后端 error。
- API：`api/orchestration.ts` 增 `goldenPath*`。

### 轨 C · 询盘第二路径（任务面 PI）
- `inquiries.vue` 保留交互 PI；新增「Hermes 履约」→ GP-A + inquiry 上下文 → 任务中心。

### 轨 D · 真桥与附属进程
- GoodJob：`GOODJOB_BASE_URL`；健康才认为桥可用；未配置诚实 failed。端口口径：API 文档 4188，runtime/bridge 探针 5188；实测双端 health/uj-bridge 皆可。
- TradeAI：`:8010`，根 `.env.dev` + `START_MINIMAL`；本地 DB 可用 SQLite（真相仍优丁 PG）；login 410。
- 无外部 Key：禁止假 sent/假 PI。

## [S3] Out of Scope
- 生产外部 AI/WhatsApp/邮件 Key 真发；
- DSH 改为每单必经；
- 附属独立登录/管理台复活；
- `_external` 完整入库或 GoodJob Node→Python 重写；
- 远端 push/PR（Finish 阶段由主理人决定）；
- GP-B 关键词/国家表单化输入（API payload 已支持，UI 未做控件）；
- `/admin` 壳下独立 Hermes 任务中心路由（现统一 `/client/tasks`）。

## Tasks
- [x] T1: 驱动链路基线复跑 + 节点状态分类 — acceptance: 脚本/接口跑通，输出各场景节点 status/error 分类表，标出代码洞 vs 配置缺（covers: S2 轨 A）
- [x] T2: L1 执行器业务闭环修复 — acceptance: content_deep 去掉不可达 except；knowledge 不可用时 degraded；knowledge_seo 场景节点无 5xx/假成功；单测覆盖关键分支（covers: S2 轨 A; depends: T1）
- [x] T3: GP-B 前端一键触达 — acceptance: 社媒拓客功能域按钮调用 golden-path/outreach，成功跳 /client/tasks?plan=；orchestration.ts 含 goldenPath* API（covers: S2 轨 B）
- [x] T4: 询盘 Hermes 履约路径 — acceptance: inquiries 详情可提交 GP-A 并跳转任务中心；交互 PI 不回归（covers: S2 轨 C）
- [x] T5: 本地真桥与进程收口 — acceptance: GoodJob 桥 health 可用；TradeAI 8010 可起且 login 410；未配置路径诚实 failed 有实测（covers: S2 轨 D）
- [x] T6: 回归与 live 验证 — acceptance: pytest/verify/selfcheck + drive-chain e2e + 关键 API live 结果写入 Report；假成功扫描无新增 HIGH（covers: S2）
- [x] T7: 独立 Review + Spec Finalize — acceptance: review 通过（无 critical）；status=delivered + commits 范围（covers: S2; depends: T1–T6）
