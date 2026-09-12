# 01 · Vue Vben Admin 5 — `@vben/web-antd`

> **本地路径**：`_ref/vue-vben-admin-full`（1806 文件，含 `apps/web-antd`）  
> **勿用**：`_ref/vue-vben-admin`（旧 sparse，仅 24 文件）  
> **上游**：https://github.com/vbenjs/vue-vben-admin · v5.7.0  
> **状态**：✅ 本地深读完成（`vue-vben-admin-full` @ `04fbb7a`）  
> **角色**：优丁 **唯一 Admin 底座**

---

## 核心结论（先看）

| 项 | 定案 |
|----|------|
| 抽取策略 | **整库 fork** → `frontend/admin-vben`，保留 monorepo packages |
| 权限 | `packages/effects/access` → `generateAccessible` + `backend` 模式 |
| 布局 | `@vben/layouts` BasicLayout（**非 Ant Design Layout**，Tailwind/shadcn 壳） |
| Ant Design | 仅 **adapter/** + 表单/表格/feedback |
| 菜单 API | 默认 `GET /menu/all` → 改 BFF `GET /admin-bff/menu/routes?shell=` |
| 登录 | `authStore.authLogin` → token + userInfo + accessCodes |

---

## Monorepo 地图

```
apps/web-antd/          ← 优丁主应用模板
packages/effects/access, layouts, request
packages/@core/preferences, ui-kit/*
packages/stores, utils, types
internal/vite-config
apps/backend-mock/      ← 菜单/登录契约参考
```

---

## 关键文件速查

| 关注点 | 路径 |
|--------|------|
| 启动 | `apps/web-antd/src/main.ts` → `bootstrap.ts` |
| 偏好/主题 | `apps/web-antd/src/preferences.ts` + `@core/preferences` |
| 权限生成 | `packages/effects/access/src/accessible.ts` |
| 路由守卫 | `apps/web-antd/src/router/guard.ts` |
| BFF 接入点 | `apps/web-antd/src/router/access.ts` |
| Auth | `apps/web-antd/src/store/auth.ts` |
| HTTP | `apps/web-antd/src/api/request.ts` |
| Ant Design 适配 | `apps/web-antd/src/adapter/component/index.ts` |
| 后端路由 helper | `packages/utils/src/helpers/generate-routes-backend.ts` |
| Mock 菜单样例 | `apps/backend-mock/utils/mock-data.ts` |

---

## UAC 对接映射

| Vben | Youding BFF |
|------|-------------|
| `POST /auth/login` | `POST /admin-bff/auth/login` |
| `GET /user/info` | `GET /admin-bff/user/info` |
| `GET /auth/codes` | `GET /admin-bff/menu/permissions` |
| `GET /menu/all` | `GET /admin-bff/menu/routes?shell=client` |
| `app.accessMode: frontend` | **必须改为 `backend`** |

---

## 可抽取性

| 模块 | Yes/Partial/No |
|------|----------------|
| access + guards + stores | **Yes**（整包） |
| layouts BasicLayout | **Yes**（整包，非 Ant Design） |
| adapter + web-antd views | **Partial**（按页迁移） |
| 单独拆 access 不带 utils/stores | **No** |

---

## 待本地运行验证

- [ ] `pnpm dev:antd` 验证  
- [ ] `adapter/vxe-table.ts` 与优丁 `a-table` 策略对比  

---

## 本地已验证（Wave 1 接线见 [99-synthesis](./99-synthesis-for-uac.md) §五）

| 文件 | 要点 |
|------|------|
| `bootstrap.ts` | adapter → initStores → registerAccessDirective → router |
| `router/guard.ts` | token → `generateAccess` → menus/routes |
| `router/access.ts` | `getAllMenusApi()` |
| `store/auth.ts` | login → userInfo + accessCodes |
| `api/request.ts` | `code:0` + Bearer + refresh |
| `packages/effects/access/src/accessible.ts` | 动态 inject Root.children |

---

*2026-06-01 · Phase 0 本地验证*
