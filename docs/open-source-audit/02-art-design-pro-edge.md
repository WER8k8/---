# 02 · Art Design Pro Edge

> **本地**：`_ref/art-design-pro-edge` @ `7df1d04` · **358 文件**  
> **栈**：Vue 3.5 + **Element Plus** + Tailwind 4  
> **状态**：✅ **本地代码级深读完成** · Phase 0a

---

## 优丁角色

**不整库采用** — 抽 **表格逻辑 + 登录多租户链 + 列拖拽 + BFF 契约对照**。

| 模块 | 路径 | 抽取 |
|------|------|------|
| useTable | `src/hooks/core/useTable.ts` (~734 行) | **Yes** 逻辑 |
| useTableColumns | `src/hooks/core/useTableColumns.ts` | **Yes** |
| tableCache/Utils/Config | `src/utils/table/*` | **Yes** |
| ArtTable / ArtTableHeader | `components/core/tables/*` | **Partial** → antd 重写 |
| 列拖拽 | `art-table-header` + `vue-draggable-plus` | **Yes** 逻辑 |
| 登录多租户 | `views/auth/login/index.vue` | **Partial** 流程 |
| Router guards | `router/guards/beforeEach.ts` | **Yes** 对照 |
| API | `api/auth.ts` → `/private/admin/system/*` | **Partial** → UAC BFF |

---

## useTable 能力清单（代码提取）

1. API 请求 + AbortController 取消重复  
2. 分页 `current/size`（与 API `page/pageSize` 双轨）  
3. LRU 缓存 + 5 种刷新（增删改/软刷）  
4. `responseAdapter` 多格式  
5. `columnsFactory` + `useTableColumns` 列显隐/重排  
6. 空值 `--` 在 ArtTable formatter  

**优丁 kit 差距**：`useYoudingTable` 仅 ~108 行 → 需移植 `utils/table/*` + columns。

---

## 多租户登录链

```
tenant_code → POST login → token → GET info → tenant → GET menu → 动态路由
```

与 UAC BFF 设计一致；Edge 路径 `/private/admin/system/user/*`。

---

## 拖拽（唯一生产 DnD）

`components/core/tables/art-table-header/index.vue`  
- `VueDraggable` v-model columns  
- fixed 列不可作为 drop 目标  

---

## 典型 CRUD 页模式

```
ArtSearchBar → ElCard.art-table-card → ArtTableHeader → ArtTable
```

使用页：`system/user`, `system/role`, `platform/tenant`, `platform/menu` 等。

---

## 深读索引

```
src/hooks/core/useTable.ts
src/hooks/core/useTableColumns.ts
src/utils/table/tableUtils.ts
src/components/core/tables/art-table-header/index.vue
src/views/auth/login/index.vue
src/router/guards/beforeEach.ts
src/api/auth.ts
src/store/modules/user.ts
```

---

*Phase 0a · 完整子任务审计 2026-05-31*
