# 表格与列表约定（Art Design Edge + RuoYi + 优丁）

> **🔒 锁定**：`docs/youding-omni-pro-design-LOCKED.md` §8 — 全站 YdPage + `YdTableColumnSettings`

## 表格

- 单元格、表头默认 **居中**（`align="center"`）
- **不展示**序号列（`type: 'index'`）
- 空值显示 **`--`**，保留 `0` / `false`
- 操作列：**≤3** 个直出按钮，超出收起到「更多」下拉

## 搜索区（YdSearchBar）

- 主按钮：查询 / 重置
- GET 参数自动剔除 `undefined`、空字符串，保留 `0` / `false`

## 分页

- 默认 `page` + `pageSize`，与后端列表 API 对齐

## 权限

- 按钮使用 `authMark` 或 `code`，与 `GET /admin-bff/menu/permissions` 一致
