---
feature: acquisition-mobius-chain
status: delivered
updated: 2026-09-18
branch: feat/acquire-mobius-20260918
commits: f5cb60d2..2c800773b5eb
---

# 获客莫比乌斯链（智慧调度 → 跟单卡 → 好用闭环）

## Report

**交付结论（2026-09-18 review 后补丁）**：主链已焊进代码——菜单/路由/服务/前端作战台/planner L1 模板/pytest。首轮 review 发现并已修复两项 CRITICAL：

1. `routes/acquisition.py` 缺 `ROUTE_PREFIX=""` → auto_discovery 双挂载 `/acquisition/acquisition/*`，前端 HTTP 404（单测直调 handler 未暴露）。已补 `ROUTE_PREFIX=""` + 路径/鉴权回归测试。
2. 获客 API 未挂 `get_current_user`（与 p2_enhancement / client 路由不一致，多租户数据裸奔）。已全量接入鉴权依赖。
3. 前端作战台硬编码 `tenant_id='demo'` → 已改为 `/client/dashboard` 解析真实租户（失败时仅演示回落 demo）。

诚实降级契约保持：translate 无引擎 `degraded=true, translated=original`；wallet 无账本 `hard_block_enabled=false, token_balance=null`。外发节点（outreach.letter / whatsapp / PI / order.create）approval_required 在 planner L1+L2 均强制。硬锁未破：唯一 `/login`、`/client/*` 壳、薄荷 `#4a9b8c` 未改。

**残余风险**：内存 Store（PG 迁移在 S3 out of scope）；wallet 未接 token_ledger；Playbook 种子仅 IN/SA/EU/AF。

**Tasks 回填**：T1–T6 已落地（见代码+pytest）；本 Report 即 T7 交付记录。

## [S1] Problem

唯一目标：**AI 智能化获客要好用，傻子都行**。此前调度、跟单卡、Playbook 分散且未进租户 UI，业务员找不到入口；回复进线无法一键建档；会话无翻译；计费无硬拦提示。主理人要求 `/compose-next` 一口气把获客主链焊到可演示闭环。

## [S2] Design

**主链**：意图 → DSH/爱马仕 L1 拓扑（已实现）→ 作战台 UI → 跟单卡六格 → Playbook → 流失因果 → 预览 API。

**工作区**：既有 linked worktree `agents-acquire-mobius-20260918-011631`（分支 `feat/acquire-mobius-20260918`），不新建 worktree。

**契约**：

1. **菜单**：`proShellMenus.ts` 租户壳增加「获客作战台」→ `/client/acquisition-ops`（不破 ROLE-SHELL-LOCK；不新建登录页；主色不改）。
2. **API 扩展**（`routes/acquisition.py`）：
   - `POST /acquisition/reply-ingest`：body `{tenant_id,inquiry_id,buyer_id?,channel?,message,country?,grade?,owner_user_id?,contact_*?}` → 可选 upsert buyer → materialize ops card → record touch → 返回 `{card,summary}`。
   - `POST /acquisition/translate`：body `{text,from_lang?,to_lang?}` → `{original,translated,provider,degraded}`；无翻译引擎时 `degraded=true` 且 `translated=original`（诚实降级，禁止编造译文）。
   - `GET /acquisition/wallet-status?tenant_id=` → `{token_balance,plan,hard_block_enabled,message}`；余额与套餐未知时返回诚实默认 `hard_block_enabled:false` + 说明，不编造余额。
3. **服务**（`services/acquisition/`）：
   - `translate_service.py`：占位/可插拔；默认 identity + degraded。
   - `wallet_guard.py`：`check_and_report(tenant_id)`；未接 ledger 时返回 unknown，不拦请求、不假报成功。
4. **前端**：
   - `acquisition-ops.vue`：调用 reply-ingest/translate/wallet-status；翻译框显示 degraded 提示；侧栏菜单可见。
   - `api/acquisition.ts` 同步新接口。
5. **测试**：pytest 覆盖 reply-ingest 三步、translate degraded、wallet unknown；**不得**因 UI 无后端而假绿。
6. **Out of scope 硬锁**：不改 `/login`、不改四壳路由前缀、不改薄荷主色 `#4a9b8c`。

**错误行为**：缺 inquiry_id → 400；translate 无引擎 → 200 + degraded；wallet 无账本 → 200 + hard_block_enabled=false + message。

## [S3] Out of Scope

- PG 迁移与生产 Liquibase/Alembic（内存 Store 保留，后续波次）
- WhatsApp/Meta 真通道与 LinkedIn OAuth
- 莫比乌斯经验 PG 双源统一（已有设计文档，不在本 feature）
- 软著打包、官网 Nuxt 双形态收敛
- 全量前端 typecheck 清基线错误

## Tasks

- [x] T1: 菜单项「获客作战台」— acceptance: proShellMenus 租户区含 `/client/acquisition-ops`，cert 路由不越壳 (covers: S2.1)
- [x] T2: reply-ingest API + 服务串联 — acceptance: pytest 覆盖建档→建卡→跟进三步与 summary 六格 (covers: S2.2)
- [x] T3: translate API 诚实降级 — acceptance: 无引擎时 degraded=true 且译文=原文 (covers: S2.3)
- [x] T4: wallet-status 诚实响应 — acceptance: 无账本不假余额、不误 hard-block (covers: S2.4)
- [x] T5: 前端作战台接新 API — acceptance: acquisition-ops 使用 reply-ingest；显示翻译/wallet 提示 (covers: S2.5)
- [x] T6: 单元测试全绿 — acceptance: acquisition+planner+e2e pytest 全部 PASS (covers: S2)
- [x] T7: 第二大脑/规格交付记录 — acceptance: spec Report 回填 + 00/22 索引更新 (covers: S2; depends: T6)

