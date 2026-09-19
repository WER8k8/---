---
feature: todo-reminder-board
status: delivered
updated: 2026-09-20
branch: feat/todo-reminder-board
commits: 6e841e23..eb333f4e
---

# 待办提醒板 · 销售任务中心接口接入

## Report

**What was built** — 「待办提醒板」销售任务中心与后端契约/引擎真正接线：① **status 单一真相**——以 `SalesTask` 模型 `open|done|cancelled` 为准；API 写入与列表 filter 接受 `pending|in_progress→open`、`completed→done`、`archived→cancelled` 别名并归一，修复前端改状态被旧白名单 400 拒绝的根因。② **中心页完整体**——`SalesTaskCenter.vue` 改用统一 `apiGet/apiPut/apiPost`；展示类型/优先级/**到期（逾期标红）**/状态；筛选 open/done/cancelled + 类型；板内新建任务（POST /tasks，sales 角色后端 403 诚实提示）；有 `rfq_id` 可跳 `/sales/rfqs?rfq_id=`。③ **follow-up 引擎前端接线**——侧栏调用 `GET /follow-up/best-send-time`、`POST /follow-up/next-action|should-stop|analyze`，枚举与后端 Stage/Trigger 对齐，失败诚实报错，不伪造外发成功。

**Verification** — pytest `test_sales_task_status_contract.py` **3 passed**；admin `npm run typecheck` **PASS**（并补 `WorkbenchItemDef.domain/privileged` 可选字段清 annex 注册表 TS 债）；live（`start-dev-admin -ForceRestart` 后）：`GET /tasks?status=open` 有数据；`PUT status=done/open` **code=0**；`POST /tasks` 创建成功 status=open；follow-up best-send-time / next-action / should-stop / analyze 均 200 且有 data。独立 Review：**无 critical**。

**Journey log** — ① 待办板「接口没接上」真因常是**契约分裂**：模型/种子已是 `open`，API 白名单却写 `pending/completed`——对齐 API 到模型，勿反向改种子。② `follow-up/*` 后端整包已挂载，前端零引用=能力不可见；接线即可，无需重写引擎。③ 前端销售任务请走 `@/utils/api` 的 apiGet/Post/Put + authHeaders，勿再手写 `admin_token` fetch。④ `/sales/rfqs?rfq_id=` 路由存在但 RfqPanel **尚未读取 query**（软缺口，非本轮伪造详情）。⑤ 树内 `hermes/runtime.py` 等脏文件与本特性无关，path-filter 提交勿混入。

## [S1] Problem
「待办提醒板」落在销售任务中心（`/sales/tasks`）：页面已请求 `/api/v1/tasks`，但**接口契约与数据真相不一致**，跟进提醒能力整包未接线：

1. **status 枚举分裂**：`SalesTask` 模型与种子/列表过滤用 `open | done | cancelled`；`sales_task.py` 更新白名单却是 `pending | in_progress | completed | cancelled | archived` → 前端改「已完成」会被 400 拒绝。
2. **提醒字段未展示**：`due_at` / `task_type` / `priority` / `rfq_id` 等模型字段在列表中几乎不可见，逾期无法一眼识别。
3. **follow-up 引擎零前端引用**：后端 `/api/v1/follow-up/*`（best-send-time、next-action、should-stop、analyze、multi-channel-strategy）已挂载且 live 可用，前端无任何调用。
4. **无板内创建**：后端 `POST /api/v1/tasks` 存在，中心页无新建表单；RFQ 提交会自动建 `rfq_response` 任务，但板内看不到关联跳转。

## [S2] Design

### 状态契约（单一真相 = 模型）
- **Canonical**：`open`（待处理）、`done`（已完成）、`cancelled`（已取消）——与 `SalesTask.status` 默认值及注释一致。
- **API 别名（写入归一化）**：`pending|in_progress` → `open`；`completed` → `done`；`archived` → `cancelled`。
- **列表 filter**：接受 canonical + 别名，查询前归一化。
- **禁止**：更新接口拒绝前端已在用的 `open/done`；禁止另造第四套状态。

### 销售任务中心 UI（`views/sales/SalesTaskCenter.vue`）
- 使用 `apiGet/apiPut/apiPost` + `authHeaders()`（统一鉴权，弃用裸 `localStorage.admin_token` 手写 fetch）。
- 列表列：任务标题、类型、优先级、**到期（逾期标红）**、状态、操作。
- 筛选：status（open/done/cancelled）+ 可选 task_type。
- 状态更新：仅发送 canonical；别名由后端归一。
- **新建任务**抽屉：title 必填；description / task_type / priority / due_at / rfq_id / lead_id 可选 → `POST /tasks`。
- **关联跳转**：有 `rfq_id` 时链到 `/sales/rfqs`（query 提示）；不伪造不存在的详情 API。
- **跟进提醒侧栏（接线 follow-up）**：
  - `GET /follow-up/best-send-time` → 展示建议发送时刻（诚实展示 timezone）。
  - `POST /follow-up/next-action`（trigger + current_stage）→ 下一步动作建议。
  - `POST /follow-up/should-stop` → 是否应停止跟进。
  - `POST /follow-up/analyze` → 策略矩阵摘要（只读）。
  - 无数据/失败 → 诚实空态/错误，不 mock 成功。

### follow-up 引擎枚举（前端常量，须与后端一致）
- Stage: `initial | follow_up_1 | follow_up_2 | follow_up_3 | breakup | stopped`
- Trigger: `no_response | opened_no_reply | clicked_no_reply | replied | bounced | unsubscribed | scheduled`
- 非法枚举由后端 400 返回，前端展示 message，不吞错。

### 权限与硬锁
- 列表/改状态：`admin | super_admin | tenant_admin | sales`（保持后端现有）。
- 创建：保持后端 `admin | super_admin | tenant_admin`（sales 只读/改状态；UI 创建失败时诚实提示 403）。
- 不改 LOGIN/ROLE-SHELL/DESIGN-TOKEN；不新建第二登录。

### 测试边界
- 后端单测：status 归一化（open/done 与别名）；非法 status → None。
- 前端：typecheck；路由仍指向 `SalesTaskCenter`。
- Live：登录后 `GET /tasks` 200 有 items；`PUT status=done` 可成功；`GET /follow-up/best-send-time` 200。

## [S3] Out of Scope
- 客户端 dashboard / 获客作战台 / 超管今日待办大一统重构；
- Hermes 任务中心与销售任务合并；
- 真实 WhatsApp/邮件外发；
- Paperclip 公司任务 API；
- RfqPanel 消费 `?rfq_id=` 深链高亮（软缺口，后续特性）；
- 远端 push/PR。

## Tasks
- [x] T1: 后端 status 契约对齐 — acceptance: 归一 open/done/cancelled + 别名；pytest 绿（covers: S2）
- [x] T2: SalesTaskCenter 列表/筛选/状态更新 — acceptance: 统一 api 客户端；due_at/类型/优先级可见；live 改状态成功（covers: S2; depends: T1）
- [x] T3: 新建任务 + RFQ 关联提示 — acceptance: 板内 POST /tasks 成功；rfq_id 行跳转 `/sales/rfqs?rfq_id=`（covers: S2; depends: T2）
- [x] T4: follow-up 提醒侧栏接线 — acceptance: best-send-time/next-action/should-stop/analyze 可调用并展示；失败诚实提示（covers: S2; depends: T2）
- [x] T5: 回归验证 + Review + Finalize — acceptance: pytest + typecheck + live 探针；review 无 critical；spec delivered（covers: S2; depends: T1–T4）
