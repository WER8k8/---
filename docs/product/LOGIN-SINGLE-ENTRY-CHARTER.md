# 管理端登录入口硬锁（LOGIN-LOCK-01）

> **状态：生效** · 2026-06-02  
> **机器可读契约**：`.project/login-entry-lock.json`  
> **跨 IDE 入口**：仓库根 `AGENTS.md`、`frontend/admin/AGENTS.md`

## 决策（不可回退，除非 Owner 书面改 charter）

1. **只有一个登录页**：`/login` → `frontend/admin/src/views/login/index.vue`
2. **只展示平台超管登录 UI**（优丁平台 · 运营控制台）
3. **禁止**四门户 `?portal=tenant|agent|partner|platform` 切换登录页
4. **禁止**新建 `client/login.vue` 或 `login/{tenant,agent,partner}.vue` 等第二套页面
5. 旧 URL（`/client/login`、`/login/agent` 等）**仅允许** 301/redirect 到 `/login`，不得再带 `portal` 参数

## 允许的文件与常量

| 用途 | 路径 |
|------|------|
| 登录页 | `frontend/admin/src/views/login/index.vue` |
| 文案/开发凭据 | `frontend/admin/src/constants/loginPortalCopy.ts` |
| OAuth 回调 | `frontend/admin/src/views/login/oauth-callback.vue` |
| 路由 | `frontend/admin/src/router/index.ts`（`/login` 单入口 + legacy redirect） |

`loginPortalCopy.ts` 只导出：

- `PLATFORM_LOGIN_COPY`
- `DEV_PLATFORM_CREDENTIALS`
- `LOGIN_PATH` / `loginPortalPath()`
- `homePathForRole()`

## 登录后跳转（与登录页分离）

登录页统一；**登录成功后**仍按 JWT `role` 跳转（router guard / `homePathForRole`）：

- `admin` / `super_admin` → `/admin`
- `tenant_admin` → `/client/dashboard`
- 代理/省代 → `/agent/*` / `/partner/*`

## 已废止文档

以下文档描述的四门户方案 **已废止**，AI/人工改登录前必须先读本文：

- `docs/meetings/ECC-LOGIN-GLASS-PORTAL-PM-DESIGN-MKT.md`（历史 PM 设计包）

## 验证（改登录相关代码后必跑）

```powershell
# 仓库根
powershell -File scripts/verify-login-entry-lock.ps1

# 或仅 admin 子项
cd frontend/admin
npm run cert:login-lock
```

门禁已接入 `npm run cert:gate`（admin）。

## AI / 其他 IDE（Qoder、Cursor、CodeBuddy 等）

**开始改登录、路由、Landing 登录按钮前：**

1. 读 `.project/login-entry-lock.json`
2. 读本文
3. 跑 `verify-login-entry-lock.ps1`
4. 若需求是「租户/代理单独登录页」→ **Out of Scope**，请 Owner 先改 charter，不要擅自新建页面
