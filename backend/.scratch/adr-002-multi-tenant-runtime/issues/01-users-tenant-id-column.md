# 01 — 用户租户绑定基线确认（结论：复用 UserTenant，不加列）

**What to build（实施后修正）：** 原计划"给 users 加 tenant_id 列"在探查后判定**方向错误**并撤回——用户→租户绑定**已由 `user_tenants` 关联表 + `resolve_tenant_id_for_user(db,user)` 提供**（super_admin/admin→None 平台级，其余→租户；youding_dev 已含真实绑定行）。本票改为：确认并锁定该解析器为唯一真相源，不引入第二套 users.tenant_id（避免多模型协作常见的双源漂移）。

**Blocked by:** None — 已完成（探查+撤回）

**Status:** done（superseded：无 schema 变更）

- [x] 确认 `user_tenants` 表 + `resolve_tenant_id_for_user` 在真 PG 正确解析（admin→None、tenant_admin→其租户）
- [x] 撤回误加的 users.tenant_id 列与迁移（head 回到单 102）
- [x] 确立 ADR-002 复用 UserTenant，不新增列

