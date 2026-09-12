# ADR-002: 多租户运行时强制（RLS 落地 + user→tenant 绑定）

- **状态**：提议（Proposed）—— 2026-09-05 B 组真 PG 审计后提出，待用户/架构拍板
- **背景来源**：审计 2026-09-05（维度 3/5 + IDOR 哨兵 + 3 套 RLS 验证 + as_uuid PG 修复）
- **裁决依据**：总纲多租户红线；本 ADR 是 ADR-001（租户归一）的"运行时执行"续篇。

## 1. 问题（全部有实测证据，非推测）

真 PG（youding_dev@5433，app 实际库）上 `tests/idor_tenant_isolation_verify.py` 实测：

| 控制 | 状态 | 证据 |
|---|---|---|
| C1 RLS 行安全 | ❌ 未启用 | `prospect_leads relrowsecurity=False force=False` |
| C2 app 连接角色 | ❌ superuser | `youding rolsuper=True` → PostgreSQL 中超级用户**无条件绕过所有 RLS** |
| C4 tenant_admin 越权 | ❌ 越权成立 | GET `/api/v1/rfq/{他租户id}` 直接返回他租户数据（rfq.py 列表/详情端点无租户过滤，docstring 明示"admin 看全部"） |
| user→tenant 绑定 | ✅ **其实已存在（本 ADR 早期误判，实施 T01 时已更正）** | `user_tenants` 关联表 + `resolve_tenant_id_for_user(db,user)` 已封装（super_admin/admin→None 平台级，其余→租户）；youding_dev 已有 2 行真实绑定。`users` 表无 tenant_id **列**，但绑定在关联表，无需新增列 |

**综合结论**：项目里有两套互不接线的租户机制——
- **机制 A（域名分租户）**：TenantMiddleware 从 Host 子域名解析租户 → OTel context → engine begin 事件 `SET LOCAL app.current_tenant_id`（`app/core/database.py:82`）。设计正确，但因 C1/C2（RLS 未开 + 超主连接），对 app 实际读写**完全不生效**。
- **机制 B（角色 + 端点）**：端点只按 `current_user.role` 判 sales 的 `assigned_to`，admin/tenant_admin 一律"看全部"。**注意：`resolve_tenant_id_for_user` 早已能从 `user_tenants` 解析出用户所属租户，但端点根本没调用它**——所以隔离缺口的根因不是"无绑定数据"，而是"端点没接这条既有解析链"。

即：**运行时多租户隔离当前为零**。uj_test@5432 上 65/0 的 RLS 验证证明的是"策略 DDL 正确"，而非"生产受保护"。

## 2. 为什么本轮没有直接"修"

任何单点强开都会立即击穿现网：
- 若对 pilot 表 `ENABLE + FORCE ROW LEVEL SECURITY` 但保持 youding 超主连接 → 超主仍绕过，无变化。
- 若改 app 连**非属主角色** + FORCE → 管理台（无域名租户上下文 → `SET LOCAL` 不触发 → current_setting 为空）将**读 0 行**（`mount_rls_pilot_if_enabled` 注释已自警）。
- 若补 tenant 列到 pilot 表并期望端点过滤 → 端点根本没有 `current_user.tenant_id` 可用（users 无该列）。

故修复是一个**必须先定义 user→租户模型**的架构变更，不能由 IDE 单方面落地（红线 R-IDEA 一致）。

## 3. 建议决策（三选一或组合，需产品/架构确认）

**方案 1（推荐，改动最小、语义最清晰）：复用 UserTenant 绑定 + 应用层过滤 + 非属主角色 + RLS 纵深**
> 实施修正（T01 探查后）：**无需给 users 加 tenant_id 列**——绑定已由 `user_tenants` 表 + `resolve_tenant_id_for_user` 提供。真正的缺口是"端点没调用这条既有链"，故方案 1 大幅简化：
1. ~~加 users.tenant_id~~ → **复用 `resolve_tenant_id_for_user`（已存在、已封装平台级/租户级语义）**。
2. 抽共享 helper `app/core/tenant_scope.py`（`scope_tenant_query` / `tenant_can_access`，委托解析器）。
3. 列表/详情端点接入 helper（租户用户限本租户；平台级 super_admin/admin 经解析器返回 None→放行全部）。**RFQ 已完成（tracer）**，其余端点按 ticket 03 铺开。
4. TenantMiddleware 租户来源从"仅域名"扩为"域名 OR 经 UserTenant 解析的当前用户租户"双通道，喂给 OTel（为 RLS SET LOCAL 服务）。
5. 运行时用**非 superuser、非表属主**的 `app_rw` 角色连 PG + pilot 表 ENABLE+FORCE RLS 作**纵深第二道**（role_grants_verify 已证角色模型可行 20/0）。

**实施进展（2026-09-05）**：
- ✅ T01（探查）：确认绑定存在于 UserTenant，撤回误加的 users.tenant_id 列。
- ✅ T02 tracer：`app/core/tenant_scope.py` + RFQ 列表/详情接入；IDOR 哨兵 A1/A2/A3 全 PASS（真 PG 实测，tenant_admin 不再跨租户读 RFQ）。全量回归 21 套零失败。
- ⏳ T03（铺开其余端点）、T04（中间件双通道）、T05（app_rw+RLS FORCE，D1/D2 转绿）、T06/T07/T09 见 tickets。

**方案 2（仅域名多租户，SaaS 子域模型）**：承认 app 只有"平台管理员跨租户"与"租户访客按域名隔离"两类，禁止 tenant_admin 这种既非平台又非域名的角色；RLS 按域名注入生效。需删除/重定义 tenant_admin 语义。

**方案 3（推迟）**：若近期只作内部/单租户运营，显式声明"多租户隔离未启用"，从对外承诺移除，RLS 与 ADR-001 继续挂账。

## 4. 影响与依赖
- 方案 1 与 ADR-001 §4 的回填迁移打通（orders/quotes/products.tenant_id 由 user.tenant_id 推导），使 104 从"无解"变"可写"。
- 需 IDOR 哨兵从"记录缺口"翻正为"断言隔离"（`idor_tenant_isolation_verify` 的 C3/C4 转绿、C1/C2 转 PASS）。
- 前端无破坏性改动（仍走 JWT）。

## 5. 本轮已顺带修复的前置项
- **PG-only 500**：`UUID(as_uuid=True)`→`False`（`app/core/database.py:165`），修复 products 等所有 `Mapped[str]`/schema 期望 str 的端点在真 PG 上因 UUID 对象校验失败而 500。SQLite 掩盖、真 PG 暴露，是本轮真 PG 测试最大收获。

---

*证据脚本：`tests/idor_tenant_isolation_verify.py`（隔离态势哨兵）；验证：uj_test@5432 三套 RLS/角色 65/0。*
