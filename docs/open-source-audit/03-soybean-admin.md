# 03 · Soybean Admin

> **本地**：`_ref/soybean-admin` @ `c45c437` · v2.2.0  
> **栈**：Vue 3.5 + **Naive UI** + UnoCSS（非 Ant Design Vue）  
> **状态**：✅ 本地深读完成 · Phase 0b

---

## 抽取结论（优丁）

| 抽取 | 禁止 |
|------|------|
| `@sa/axios` + 业务码拦截/refresh 队列（逻辑） | 所有 Naive 组件与 layouts |
| 路由 init：constant → auth → redirect | elegant-router 覆盖 234 路由 |
| 菜单/面包屑/排序纯函数（`route/shared.ts`） | `table-column-setting.vue` 原样 |
| `typings/api/*` 命名空间规范 | apifoxToken、双 axios demo |

**总评**：**Partial** — 抽 HTTP 状态机与路由初始化；UI 全禁。

---

## API 三层

```
src/service/api/*.ts     → fetchLogin, fetchGetUserRoutes
src/service/request/     → code 0000、登出码、refresh
packages/axios/          → createFlatRequest
```

- 分页：`current` / `size` / `records`（需 adapter 到优丁 `page/pageSize`）
- 动态路由：`GET /route/getUserRoutes` → `{ routes, home }`

---

## Router 要点

- **Elegant Router**：`build/plugins/router.ts` 扫描 `views/` → `router/elegant/routes.ts`（生成物）
- **Guard 两阶段**：`initConstantRoute` → `initAuthRoute` → `router.addRoute`
- **模式**：`VITE_AUTH_ROUTE_MODE=static|dynamic`

---

## 深读文件索引

| 文件 | 用途 |
|------|------|
| `src/service/request/index.ts` | 业务码生命周期 |
| `src/router/guard/route.ts` | 登录/动态路由 |
| `src/store/modules/route/shared.ts` | 菜单推导 |
| `packages/hooks/src/use-table.ts` | 轻量表格（~136 行，非 Art 734 行） |
| `src/components/advanced/table-column-setting.vue` | 列拖拽（Naive，仅参考逻辑） |

---

*详见 Phase 0 子任务全文 · 2026-06-01*
