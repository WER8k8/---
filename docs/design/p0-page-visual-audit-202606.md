# P0 标杆页视觉审计表（JD-03 · 研发走查版 · 待视觉确认）

> **走查日期**：2026-06-07 · **走查人**：前端 Lane（代填草案）  
> **视觉部**：请在此基础上改分、补 Must-fix，签字后开 WP-P0-UI-*

---

## 1. admin/dashboard.vue（运营看板）

| 维度 | 分 | 问题 |
|------|-----|------|
| Typography | **4** | 已用 `YdPage` hero + display 标题；KPI 数字可加强 `tabular-nums` |
| Color / token | **4** | 已套 YdStatsCard；部分 tone 仍偏紫/蓝与壳层薄荷略跳 |
| Density | **4** | 首屏 5 KPI + 双栏，符合 cockpit；待跟进卡片略长 |
| YdPage 契约 | **5** | `surface="brand-hero"` + YdDataTable，结构正确 |

**Must-fix（研发可做 · 视觉确认）**

| # | 问题 | 任务 ID |
|---|------|---------|
| 1 | 空值部分用 `-` 应统一 `--`（表格规范） | WP-P0-UI-01 |
| 2 | KPI 卡片 tone 与 `--uj-brand` 对齐，减少 purple 独立色 | WP-P0-UI-01 |
| 3 | 待跟进询盘区与上方 grid 间距统一 16px 网格 | WP-P0-UI-01 |

---

## 2. admin/tenants.vue（租户管理）

| 维度 | 分 | 问题 |
|------|-----|------|
| Typography | **4** | YdPage 标题区 OK；Drawer 内 descriptions 字号略小 |
| Color / token | **4** | 玻璃面板已生效；状态 tag 色为 Ant 默认绿/橙 |
| Density | **5** | 搜索条 + 列设置 + 表格，高密度符合 Art Pro |
| YdPage + 表格 | **5** | YdSearchBar / YdDataTable / Drawer 齐全 |

**Must-fix**

| # | 问题 | 任务 ID |
|---|------|---------|
| 1 | 空值已用 `--` ✓；Drawer 内 `-` 改 `--` | WP-P0-UI-02 |
| 2 | 操作列仅 1 按钮 ✓；「查看详情」可改主色 link 跟随 accent | WP-P0-UI-02 |
| 3 | 表格 loading 骨架与壳层背景对比度（视觉定稿后微调） | WP-P0-UI-02 |

---

## 3. inquiries/index.vue（询盘管理）

| 维度 | 分 | 问题 |
|------|-----|------|
| Typography | **4** | 标题区 OK；顶栏 actions 按钮多，小屏易挤 |
| Color / token | **4** | StatsRow + panel 统一；radio 筛选区略密 |
| Density | **4** | 4 KPI + 筛选 + 大表，偏密但符合询盘场景 |
| YdPage + Drawer | **4** | 有 Drawer/导出；actions 区可收进「更多」 |

**Must-fix**

| # | 问题 | 任务 ID |
|---|------|---------|
| 1 | `#actions` 超过 3 个主按钮 → 收「导出审计」进「更多」下拉 | WP-P0-UI-03 |
| 2 | 移动端 actions 换行与顶栏不打架（响应式） | WP-P0-UI-03 |
| 3 | 统计卡片 compact 与列表区间距 16px 统一 | WP-P0-UI-03 |

---

## 并行 Lane 分配（PM 确认）

| 任务 ID | 页面 | Lane | 状态 |
|---------|------|------|------|
| WP-P0-UI-01 | dashboard | BJ-PAGE-01 | 研发 Must-fix 已落地，待 VIS 签字 |
| WP-P0-UI-02 | tenants | BJ-PAGE-02 | 研发 Must-fix 已落地，待 VIS 签字 |
| WP-P0-UI-03 | inquiries | BJ-PAGE-03 | 研发 Must-fix 已落地，待 VIS 签字 |

**视觉签字**：VIS-NAV-01 ______ **日期** ______  
**Owner 确认优先级**：默认先做 dashboard ☐ 改选 ______
