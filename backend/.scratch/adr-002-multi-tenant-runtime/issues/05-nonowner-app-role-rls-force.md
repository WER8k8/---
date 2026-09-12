# 05 — 非属主 app_rw 角色 + RLS FORCE 灰度（纵深防御）

**What to build:** 应用不再用 superuser 连库。建非属主 `app_rw` 角色（有 DML、无 DDL、非 superuser），app 以该角色连 PG；对 pilot 表 `ENABLE + FORCE ROW LEVEL SECURITY`。因 T04 已保证租户上下文注入，FORCE 不会误锁。role_grants_verify 已验证该角色模型可行（20/0），本票把它接到运行时。RLS 作为应用层过滤（T03）之外的**第二道防线**。

**Blocked by:** 04（SET LOCAL 运行时生效，否则 FORCE 会锁死无上下文请求）

**Status:** ready-for-agent

- [ ] 迁移/脚本：建 app_rw 角色 + GRANT（表属主仍为迁移角色，app 用 app_rw）
- [ ] pilot 表 ENABLE+FORCE RLS；`mount_rls_pilot_if_enabled` 扩到目标表集并真正对 app_rw 生效
- [ ] app 连接串切到 app_rw（非超主）；`idor_tenant_isolation_verify` C2（app 角色非 superuser）翻 PASS
- [ ] 双租户穿透：app_rw + 无 SET LOCAL 时读 0 行（证明 FORCE 生效）、有 SET LOCAL 时只见本租户
- [ ] 灰度：先 pilot 表，验证后再扩；Celery/后台任务路径确认租户注入或用受控旁路
