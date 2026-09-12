# ADR-002 方案 1 实施 Ticket 集（多租户运行时强制）

来源：`docs/adr/ADR-002-multi-tenant-runtime-enforcement.md` 方案 1。
拆解法：纵向 tracer-bullet；user→tenant 绑定与 DB 角色切换按 expand–contract 编排，保证每片可独立验证、CI 逐片绿。

## 关键设计澄清（recon 实测所得）
- `get_current_user` 返回**完整 User ORM 行** → 一旦 `users.tenant_id` 存在，任何端点可直接 `current_user.tenant_id` 过滤，**无需 JWT claim**。JWT/cookie 里的 tenant 只被**中间件**需要（中间件在 auth 依赖之前运行，看不到 current_user）。→ 应用层过滤轨（T01→T02→T03）与 RLS 纵深轨（T01→T04→T05）解耦，T02 不被 T04 挡。
- 现成可复用：`platform_account_service.resolve_tenant_scope(db,user)->str|None`（None=平台级全量）即 scope_tenant 概念雏形；`app/core/security/rls.set_tenant_context` 即 SET LOCAL 原语。T02/T03 是提炼+接线，非造轮子。

## 依赖与 frontier
```
T01 users.tenant_id 地基 + 写入路径
 ├─ T02 scope_tenant helper + RFQ 首条 tracer（app 层）
 │    └─ T03 扩展 app 层过滤到交易/CRM/获客/内容端点
 │         └─ T09 IDOR 哨兵 app 层翻正断言
 └─ T04 JWT/cookie 携带 tenant + 中间件双通道注入
      └─ T05 非属主 app_rw 角色 + RLS FORCE 灰度（纵深）
T06 租户注册/邀请流程补 tenant_id 写入（T01 的下游数据闭环）
T07 跨租户对象引用入参校验（建子资源引用他租户资源时拦截）
T08 数据迁移治理：users.tenant_id 回填策略 + 归档孤儿列清理（依赖 ADR-001 产品裁决）
```
可立即启动（无 blocker）：T01、T06、T08（可并行起草）。
Frontier 推进：T01 完成 → T02、T04 并行 → T02 完成 → T03 → T09；T04 完成 → T05。

## 实施状态（2026-09-05）
- ✅ **T01 完成（方向修正）**：绑定已存在于 `user_tenants` + `resolve_tenant_id_for_user`（真 PG 验证），撤回误加的 users.tenant_id 列/迁移。T01 文件已改写为"复用 UserTenant"。
- ✅ **T02 完成**：`app/core/tenant_scope.py`（委托解析器）+ RFQ 列表/详情接入；IDOR 哨兵应用层 A1/A2/A3 全 PASS（真 PG，seed 真实 User+UserTenant）；全量回归 21 套 rc=0。
- ✅ **T03 完成**：`opportunity`/`campaign`/`company` 列表+详情接 `scope_tenant_query`/`tenant_can_access`；哨兵 A4 真 PG 各列表无他租户行全 PASS。**project 模型无 tenant_id 列→跳过标 P0-B**；**quotes 端点无 auth+裸 dict / leads 是 user_id 维度→标需 auth 模型裁决跟进，未盲改**。
- ✅ **T06 实测确认无需改**：`tenants.py:1325` 管理员建租户成员路径已写 `user_tenants`（真 PG 2 行 tenant_admin/admin），无自助注册端点，符合 B2B 开通模型。
- ✅ **T07 完成**：`quotes.create_from_rfq` 加 `tenant_can_access` 跨租户引用校验 + 新报价继承 rfq.tenant_id；哨兵 A5 真 PG 实测跨租户建报价 403。
- 顺带 heal PG youding_dev 漂移列：`quotes.tenant_id`(→uuid)、`opportunities.company_id/contact_id/created_by`（均属 P0-B 归档线漂移，逐列补解 live 500）。全量回归 21/21 rc=0；A1–A5 应用层隔离全 PASS。
- ⏭ 下一组：T04 中间件双通道 → T05 非超主角色+RLS FORCE（D1/D2 转绿）→ T09 门禁翻正。遗留 D0：`api/v1/deerflow.py` 漏挂载+16 F821+被 `test_core_chain.py` 引用 → 裁决挂载修复 or 删测试。
- 不在此轮做：mass `ruff --fix`（worktree 非 git 无回滚）。

## 文件清单
- 01-users-tenant-id-column.md
- 02-app-layer-tenant-filter-helper-rfq-tracer.md
- 03-app-layer-filter-rollout.md
- 04-jwt-tenant-claim-middleware-injection.md
- 05-nonowner-app-role-rls-force.md
- 06-tenant-user-provisioning-write-path.md
- 07-cross-tenant-reference-validation.md
- 08-data-migration-governance.md
- 09-idor-sentinel-green-gate.md
