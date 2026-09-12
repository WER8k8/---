# youding-admin-kit — 百家抽取清单

从各开源仓库抽取的**模块清单**，供 `admin-vben` 与现网 `admin` 绞杀者迁移时引用。  
**禁止**在此 kit 内引入第二套 UI 库（仅 Ant Design Vue + SCSS 令牌）。

> **🔒 设计锁定**：`docs/youding-omni-pro-design-LOCKED.md` · 页面契约 **YdPage** · 表格必须 **YdDataTable + 列设置**

---

## 抽取对照表

### Vben Admin → 壳与权限引擎

| 模块 | 源路径（参考） | kit 对应 |
|------|----------------|----------|
| 动态路由注册 | `packages/effects/access` | 消费 `GET /admin-bff/menu/routes` |
| 多标签 worktab | `packages/effects/layouts` | Platform / Ops 默认开 |
| 按钮权限指令 | `v-access` | 对接 `authList[].code` |
| 主题配置 | `@vben/preferences` | 同步 `--uj-*` tokens |

### Art Design Pro / Edge → 表格与视觉

| 模块 | 抽取内容 | kit 文件 |
|------|----------|----------|
| useTable | 分页/搜索/刷新/列缓存 | `composables/useYoudingTable.ts` |
| ArtSearchBar | 查询区布局 | `components/YdSearchBar.vue` |
| ArtStatsCard | 指标卡 | `components/YdStatsCard.vue` |
| 表格约定 | 居中、无序号、空值 `--` | `conventions/table.md` |
| 水印 | 租户\|账号 | `components/YdWatermark.vue` |
| 多租户登录 | tenant_code URL | BFF `auth/tenant/search` |

### Soybean Admin → 工程规范

| 模块 | 抽取内容 | 落地 |
|------|----------|------|
| API 分层 | `service/api/*` | `admin-vben/.../api/{auth,menu,client}.ts` |
| 路由模块 | `routes/modules/*` | 按 shell 分文件 |
| 类型 | `Api.Namespace` | `types/uac.d.ts` |

### Pure Admin → 开发与主题

| 模块 | 抽取内容 | 落地 |
|------|----------|------|
| mock 结构 | `mock/*` | W2 租户 Dashboard 开发 |
| 侧栏折叠 | 移动端 | ClientShell |
| 色弱/布局宽 | 设置项 | Vben preferences 扩展 |

### Vue-Admin-Better → 生成器

| 模块 | 抽取内容 | 落地 |
|------|----------|------|
| CRUD 模板 | list/form/api 三文件 | `scripts/gen-crud-from-openapi.mjs` |
| 操作列规范 | ≤3 直出 | `conventions/table.md` |

### Naive UI Admin → 租户颜值

| 模块 | 抽取内容 | 落地 |
|------|----------|------|
| 登录分屏 | 左品牌右表单 | `layouts/TenantLogin.vue` |
| 统计卡留白 | 大圆角轻阴影 | `YdStatsCard` |
| 鉴权模式 | 路由/前端/后端 | 映射为 UAC 五层权限 |

### Vue Element Admin → 守卫经典

| 模块 | 抽取内容 | 落地 |
|------|----------|------|
| permission 流程 | 白名单→拉菜单→addRoute | Vben beforeEach 对照 |
| meta 字段 | title/icon/roles | `schemas/menu-route.schema.json` |

### RuoYi-Plus-Soybean → 后端能力

| 能力 | FastAPI 状态 | 波次 |
|------|--------------|------|
| 用户/角色/菜单 | 已有 AdminMenu/RBAC | W4 |
| 租户套餐 | 已有 tenants | W2 |
| 操作日志 | 部分 audit | W5 |
| 字典 | settings 分散 | W5 |
| 文件上传 | file-manager | W5 |
| 代码生成 | 无 | W6 script |

---

## kit 目录

```
youding-admin-kit/
├── MANIFEST.md                 # 本文件
├── conventions/
│   └── table.md                # Art Edge 表格约定
├── composables/
│   └── useYoudingTable.ts
├── components/
│   ├── YdStatsCard.vue
│   ├── YdSearchBar.vue
│   └── YdWatermark.vue
├── design-tokens/
│   └── tokens.scss             # 扩展 admin design-tokens
├── schemas/
│   ├── menu-route.schema.json
│   └── permission.schema.json
└── types/
    └── uac.d.ts                # Admin Unified Contract 类型
```

---

## 使用方式

1. **W1**：在 `admin-vben` 中 `pnpm add` 或通过 workspace 引用本 kit  
2. **现网 admin**：绞杀者期可复制 `composables` + `components` 到 `frontend/admin/src/youding/`  
3. **BFF**：前端只调 `/api/v1/admin-bff/*`，见 `docs/youding-admin-composite-blueprint.md`
