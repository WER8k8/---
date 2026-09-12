# Admin BFF 菜单接口冻结说明（JD-04）

> **状态**：🔒 **FROZEN** · 2026-06-07  
> **Gate**：JD-04 签认后 **WP-NAV-03**（前端消费 BFF 动态菜单）方可改生产路径  
> **实现位置**：`backend/app/api/v1/admin_bff/menu_adapter.py`

---

## 1. 端点

| 项 | 值 |
|----|-----|
| Method | `GET` |
| Path | `/api/v1/admin-bff/menu/routes` |
| Auth | `Authorization: Bearer <JWT>` |
| Query | `shell`（可选，`platform` \| `client` \| `agent` \| `ops`） |

**生产行为**：以 JWT 用户角色解析 shell（`resolve_shell(user)`）；`shell` 查询参数仅在与 JWT 一致时用于调试，不得作为权限提升通道。

---

## 2. 成功响应（200）

```json
{
  "code": 0,
  "success": true,
  "data": [
    {
      "name": "Dashboard",
      "path": "/dashboard",
      "component": null,
      "redirect": null,
      "meta": {
        "title": "数据看板",
        "icon": "DashboardOutlined",
        "order": 0,
        "keepAlive": false,
        "hideInMenu": false,
        "hideInTab": false,
        "affixTab": false,
        "shell": "platform",
        "roles": [],
        "authList": []
      },
      "children": []
    }
  ]
}
```

**数据来源优先级**：

1. DB 菜单树（`build_menu_tree`）→ `db_tree_to_routes`
2. 无 DB 数据时 → `seeds_for_shell(shell)` 静态 seed

---

## 3. 失败路径

| HTTP | 场景 | error_code / 说明 |
|------|------|-------------------|
| **401** | 无 token / token 无效 | 标准 JWT 未授权 |
| **403** | 用户无菜单访问权限 | 权限码过滤后空树可返回 `[]`，不伪装有菜单 |
| **422** | `shell` 参数非法 | FastAPI validation |
| **503** | DB 不可用且 seed 未配置 | 须明确 `error_code`，禁止假成功空壳 |

**禁止假交付**：不得 `success: true` 且返回占位「敬请期待」路由作为终态菜单。

---

## 4. 与前端 SSOT 字段映射

前端 Nav Kernel 消费结构见 `frontend/admin/src/types/shellNav.ts` 与 `platformShellMenu.ts`。

| BFF `UacMenuRoute` | 前端 `ShellNavItem` / `ShellMenuGroup` | 说明 |
|--------------------|----------------------------------------|------|
| `name` | `name` | 路由 name，Worktab 回退键 |
| `path` | `path` | 必须与 `check-nav-routes.mjs` 已注册 |
| `meta.title` | `title` | Worktab 中文标签 |
| `meta.icon` | `icon` | Ant Design Vue 图标名 |
| `children[]` | `children[]` | 嵌套子菜单 |
| `meta.hideInMenu` | — | `true` 时不进侧栏 |
| `meta.order` | 组内排序 | 数字越小越靠前 |
| — | `ShellMenuGroup.title` | BFF 无分组标题时由前端 `groupBy` 或 seed 分组补全 |

**WP-NAV-03 适配层职责**（Out-of-Scope 本冻结文档）：

- `GET menu/routes` → 转换为 `ShellMenuGroup[]` 供 `useShellNavigation`
- 字段缺失时 **503 + MENU_SHAPE_INVALID**，不得静默降级为硬编码全量菜单

---

## 5. 与 OpenAPI

片段已存在于 `backend/openapi.json` → `/api/v1/admin-bff/menu/routes`。  
变更须同步 OpenAPI + 本文件 + `platformShellMenu.ts` 映射表三处。

---

## 6. 签认

| 角色 | 签字 | 日期 |
|------|------|------|
| ARCH-NAV-01 | | |
| BE-BFF-MENU-01 | | |
| PM-NAV-01 | | |
