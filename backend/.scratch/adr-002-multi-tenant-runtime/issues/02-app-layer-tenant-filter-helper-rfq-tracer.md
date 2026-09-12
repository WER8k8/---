# 02 — scope_tenant helper + RFQ 首条 tracer（app 层隔离）

**What to build:** 提炼一个共享的租户过滤 helper（复用/上收现成 `platform_account_service.resolve_tenant_scope` 语义），并在 **RFQ 列表 + 详情**两个端点接通端到端租户隔离：租户用户只看到本租户 RFQ、读不到他租户 RFQ；平台级用户（tenant_id=NULL）看全部。这是打通"一条完整纵向路径"的 tracer bullet，后续端点照此模式复制。

**Blocked by:** 01（需 users.tenant_id 可读）

**Status:** ready-for-agent

- [ ] 新增 `scope_tenant(query, current_user)` helper：tenant_id 非空则 `WHERE tenant_id=:tid`，NULL 放行；置于共享层，供后续端点复用
- [ ] RFQ 列表端点改用 scope_tenant（不再"admin 看全部"）；RFQ 详情对非本租户 id 返回 403/404
- [ ] 手工/脚本造两条分属租户 A/B 的 RFQ，以 A 的 tenant_admin 身份：列表只见 A、详情读 B 被拒
- [ ] `tests/idor_tenant_isolation_verify` 的 C3（列表）、C4（详情）对 RFQ **翻为 PASS**
- [ ] 现有依赖 admin 全量的回归/看板用例不因此破（用平台级 NULL 用户回归）
