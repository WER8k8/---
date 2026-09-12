# 13 · Formily + antdv-x3

> **本地**：`_ref/formily` (1332) + `_ref/formily-antdv-x3` (324)  
> **状态**：✅ 包结构深读 · Phase 0b

---

## 角色（优丁）

**局部 W3** — 复杂 Schema 表单、字段联动、未来拖拽设计器；**不**全站替换 `a-form`。

---

## antdv-x3 包结构

| 包 | 用途 |
|----|------|
| `packages/components` | Form/FormItem/FormGrid/FormStep/FormTab/FormDialog/**ArrayTable**/ArrayCards… |
| `packages/renderer` | Schema → 组件渲染 |
| `packages/setters` | 设计器属性面板 |
| `packages/settings-form` | 设计器表单 |
| `packages/prototypes` | 组件原型元数据 |

**与 Ant Design Vue 一致** — 优丁栈可对接（维护：最后 commit 2023，alpha.7）。

---

## 典型复杂场景组件

- `FormStep` / `FormTab` — 分步/分 Tab 大表单  
- `ArrayTable` — 动态行表格  
- `FormDialog` / `FormDrawer` — 弹窗表单  
- `Editable` — 行内编辑  

---

## 试点页建议

1. `tenants/site-editor` — 站点模块配置  
2. `seo/schema-markup` — Schema 驱动  

**依赖**：BFF 存 JSON Schema 版本 API（W3）。

---

## 抽取 vs 禁止

| Partial | No |
|---------|-----|
| Schema 渲染层 + 1 试点页 | 全站 Formily 化 |
| Designable 协议研究（在线） | 未评估前上生产设计器 |

---

*Phase 0b*
