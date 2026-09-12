# frontend/admin — AI 协作约束

## 登录入口（硬锁 LOGIN-LOCK-01）

**先读：** `../../.project/login-entry-lock.json` · `../../docs/product/LOGIN-SINGLE-ENTRY-CHARTER.md`

- 唯一登录页：`src/views/login/index.vue`，路由 `/login`
- 唯一文案：`src/constants/loginPortalCopy.ts`（仅 `PLATFORM_LOGIN_COPY`）
- 不要创建 `src/views/client/login.vue` 或 `src/views/login/*.vue` 多文件门户

验证：

```bash
npm run cert:login-lock
```

## 角色壳入口（硬锁 ROLE-SHELL-LOCK-01）

**先读：** `../../.project/role-shell-lock.json` · `src/constants/roleShellLock.ts`

| 场景 | 路由 | 组件/目录 |
|------|------|-----------|
| 租户自用后台 | `/client/today` | `src/views/client/` |
| 超管管租户 | `/admin/tenants` | `src/views/tenants/dashboard.vue`（**禁止** `views/admin/tenants.vue`） |
| 唯一登录 | `/login` | `src/views/login/index.vue`（租户也走这里，靠 JWT 分流） |

```bash
npm run cert:role-shell-lock
```

## 送检门禁

```bash
npm run cert:gate
```
