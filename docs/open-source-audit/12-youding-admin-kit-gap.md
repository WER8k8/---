# 12 · youding-admin-kit 差距清单（对照 Art Edge 深读）

> **对照基准**：[02-art-design-pro-edge.md](./02-art-design-pro-edge.md)  
> **现网 kit**：`frontend/youding-admin-kit/`（9 文件）

---

## 一、总览

| 维度 | Art Edge 完整实现 | 现 kit | 差距 |
|------|-------------------|--------|------|
| 表格 Hook | `useTable` ~734 行 + 缓存 + 5 种刷新 | `useYoudingTable` ~108 行 | **大** |
| 列配置 | `useTableColumns` + 拖拽重排 | 无 | **缺失** |
| 表格 UI | `ArtTable` + `ArtTableHeader` | 无（依赖页面手写 `a-table`） | **缺失** |
| 搜索 UI | `ArtSearchBar` 展开/收起 | `YdSearchBar.vue` 简化版 | **中** |
| 统计卡 | dashboard modules | `YdStatsCard.vue` | **小** |
| 水印 | Edge 组件 | MANIFEST 有，**文件未建** | **缺失** |
| 登录分屏 | `LoginLeftView` + tenant | MANIFEST 有 `TenantLogin`，**未建** | **缺失** |
| 路由/权限 | 完整 guards + MenuProcessor | schema JSON 仅有 | **未接 Vben** |
| CRUD 生成器 | — | MANIFEST 有 script，**未建** | **缺失** |

**结论**：kit 目前是 **「名片级骨架」**，不是 Art Edge 级能力。深读完成前 **不应宣称已集百家所长**。

---

## 二、useYoudingTable vs Art useTable（逐项）

| 能力 | Art `useTable` | `useYoudingTable` |
|------|----------------|-------------------|
| AbortController 取消重复请求 | ✅ | ❌ |
| LRU 请求缓存 (`tableCache`) | ✅ | ❌ |
| 5 种刷新策略（增删改/软刷） | ✅ | 仅 `reload` |
| `responseAdapter` 多格式 | ✅ | 固定 `{items,total}` |
| `columnsFactory` + 列显隐 | ✅ | ❌ |
| 分页字段可配置 | ✅ `tableConfig` | 固定 page/pageSize |
| 移动端分页 small | ✅ | ❌ |
| 错误处理 `TableError` | ✅ | try/finally  only |
| 空值 `cellText` | 在 ArtTable | ✅ 有 |

**深读后抽取顺序**：
1. 移植 `utils/table/*` + `useTableColumns`（逻辑层，Ant Design 无关）
2. 扩展 `useYoudingTable` 或 rename 为完整 `useTable` 并保留 Youding fetcher 签名
3. 新建 `YdTableHeader.vue`（列拖拽，抄 Edge 行为，换 Ant Design Popover/Checkbox）

---

## 三、MANIFEST 承诺但未落地的文件

| MANIFEST 条目 | 预期路径 | 状态 |
|---------------|----------|------|
| `YdWatermark.vue` | `components/` | ❌ |
| `layouts/TenantLogin.vue` | `layouts/` | ❌ 目录不存在 |
| `AssistantFab` | `components/` | ❌（现网在 admin UBrain） |
| `YdEmpty` | `components/` | ❌ |
| `gen-crud-from-openapi.mjs` | `scripts/` | ❌ |

---

## 四、深读阶段任务（本文件随审计更新）

- [ ] 读完 Art Edge `useTable.ts` 全文并标注优丁可删/必留分支  
- [ ] 读完 Vben `packages/effects/access` 与 web-antd 布局入口  
- [ ] 对照 `frontend/admin/src/views/client/layout.vue` 记录 emoji 菜单替换点  
- [ ] 输出 `99-synthesis-for-uac.md` 文件级抽取任务  

---

*2026-05-31 · Phase 0*
