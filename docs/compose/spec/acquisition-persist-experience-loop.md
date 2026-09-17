---
feature: acquisition-persist-experience-loop
status: delivered
updated: 2026-09-18
branch: feat/acquire-mobius-20260918
commits: 67e9d342..PREVIEW
---

# 获客落库与经验闭环（compose-next#2）


## Report

**What was built** — 获客闭环落库与经验反哺：`repo.py` 双写既有 Inquiry/ProspectLead（无 DB 诚实失败）；`experience_feed.py` 将 reply_ingest / ops_touch / ops_loss / intent_preview 写入 EvolutionEngine（失败不断链）；API 四接口返回 persistence/experience 观测字段；前端与菜单沿用上一轮作战台。

**Verification** — `pytest` 获客全量（persist + compose + e2e + planner + service）**PASS**（评审修复后子集 35/35，本地全量复跑 47/47）；硬锁 ROUTE_PREFIX + get_current_user + 登录/薄荷主色未破。

**Journey log**
1. 新路由必须 `Depends(get_db)`，`db: Any=None` 会让生产永远降级。
2. ProspectLead 多租户唯一键含 tenant_id，落库必须写入。
3. 单测直调 FastAPI 时 Depends 占位需 `_resolve_db` 过滤，不能当真 Session。
4. 经验写入 best-effort：Evolution 优先，失败不阻断获客主流程。
5. 复用 Inquiry/ProspectLead/evolution_*，不建平行账本。
## [S1] Problem

获客作战台与调度图已在内存层可演示，但：询盘/线索未稳定写入既有 PG 模型；流失/跟进不进经验环；主理人要求「一口气干到底」——闭环要落到**可持久、可反哺**，而不只是点一下卡片。

## [S2] Design

**工作区**：沿用 `agents-acquire-mobius-20260918-011631` / `feat/acquire-mobius-20260918`。

**契约**：

1. **双写仓储** `services/acquisition/repo.py`
   - `persist_inquiry(...)`：若 `db` 可用则写入 `Inquiry`（name/phone/email/message/tenant_id/assigned_to/source_channel/attribution_channel）；DB 失败或未初始化 → 返回 `{persisted: false, reason}`，**不抛断主流程**。
   - `persist_prospect_lead(...)`：可选写入 `ProspectLead`（email/company/country/first_name/title/source→枚举近似，未知 source→MANUAL_IMPORT）；同样诚实降级。
   - 内存 OpsCard/Buyer 逻辑保持（UI 已依赖）；DB 询盘/线索为「业务真相源补写」。

2. **经验闭环** `services/acquisition/experience_feed.py`
   - `record_acquisition_event(db, *, tenant_id, event, inquiry_id, detail, success)`：
     - 优先 `EvolutionEngine.record_task_execution` / `ExperienceStore`（若可 import 且 db 非 None）
     - 事件名：`reply_ingest` / `ops_touch` / `ops_loss` / `intent_preview`
     - 失败事件（loss）→ 仍写入 evolution 记录 success=False + detail
     - 无 db 或 evolution 失败 → 返回 `{recorded: false}`，不阻断 API
   - `record_terminal_acquisition`：包装 terminal_hook 若存在；否则上式。

3. **API 接线** `routes/acquisition.py`
   - `reply-ingest`：在现逻辑后 best-effort `persist_inquiry` + `persist_prospect_lead` + `record_acquisition_event(reply_ingest)`；响应增加 `persistence` 与 `experience` 字段。
   - `ops-card/{id}/loss`：追加 `record_acquisition_event(ops_loss, success=False)`。
   - `ops-card/{id}/touch`：追加 `ops_touch`（success=true）。
   - `intent/preview`：追加 `intent_preview`（不记业务成功，仅拆解观测）。
   - 鉴权：继续 `get_current_user`；`ROUTE_PREFIX=""` 不变。

4. **调度闭环增强** `planner_service`（小幅）
   - `decompose` 返回后不改签名；在 acquisition 场景由 API 层记 experience（避免 planner 强依赖 DB）。
   - 不新增执行器；不破三道安全阀。

5. **测试**
   - repo：有 mock session 写入字段；无 db 时 persisted=false 且 reason 非空
   - experience_feed：无 db → recorded=false；有 mock store → recorded=true
   - API：reply-ingest 响应含 persistence/experience；loss 触发 success=False 事件（可 mock）
   - 回归：既有 38 测不得回归失败

6. **硬锁**：不改登录/四壳/薄荷主色；不新建平行账本（只写 inquiry/prospect_leads/evolution_*）。

## [S3] Out of Scope

- Alembic 迁移与 PG 实机（本环境 SQLite 可缺表；代码必须诚实降级）
- 语言桥真实翻译引擎接入
- Wallet 读 token_ledger 真余额
- 前端 typecheck 全量清基线
- 合并 main / 推远端（Finish 由主理人决定）

## Tasks

- [x] T1: acquisition/repo.py 双写仓储 — acceptance: 无 db persisted=false；mock db 写 Inquiry 字段 (covers: S2.1)
- [x] T2: acquisition/experience_feed.py — acceptance: 无 db recorded=false；可调用 evolution (covers: S2.2)
- [x] T3: API 四接口接线 persistence/experience — acceptance: reply-ingest/loss/touch/preview 均带观测字段 (covers: S2.3)
- [x] T4: 单元测试新增 — acceptance: 新测 + 旧测全 PASS (covers: S2.5)
- [x] T5: spec Report + 第二大脑 — acceptance: delivered 与 22 号日志续写 (covers: S2; depends: T4)
