# 04 — JWT/cookie 携带 tenant + 中间件双通道注入

**What to build:** 让访问令牌携带调用者 tenant（供**中间件**在 auth 依赖之前读取），TenantMiddleware 的租户来源从"仅域名"扩展为"域名 OR 令牌内 tenant"双通道，并写入 OTel context，使 admin 控制台（非子域名进入）也能触发事务级 `SET LOCAL app.current_tenant_id`。这是让既有 RLS DDL 真正对 app 读写生效的关键接线。

**Blocked by:** 01（用户需有 tenant_id 供签发）

**Status:** ready-for-agent

- [ ] 登录签发 access/refresh 时写入 tenant claim（NULL 用户不写或写空=平台级）
- [ ] TenantMiddleware：解析顺序 = 子域名命中优先 → 否则解码令牌 tenant → 注入 request.state 与 OTel
- [ ] 平台级用户（无 tenant）明确不注入 SET LOCAL（避免误锁其跨租户读）
- [ ] 真 PG 上验证：租户用户走 admin 路径时 `current_setting('app.current_tenant_id')` 已注入
- [ ] 不影响统一登录（UJ 票据）与 cookie 双模态；旧令牌无 claim 时降级不崩
