# Youding Omni Pro · 设计锁定规格（LOCKED）

> **状态**：🔒 **LOCKED** — 未经产品负责人书面确认，不得变更本文档中的定案项。  
> **版本**：v1.0 · 2026-06-02  
> **适用范围**：`frontend/admin`、`frontend/youding-admin-kit`、Admin BFF 消费侧、送检/融资演示路径。  
> **优先级**：本文档 **高于** `youding-admin-overhaul-prd.md` 中与之冲突的 **壳/底座** 描述（旧 PRD 写「Vben 唯一底座」→ **以本文绞杀现网为准**；Vben 仅作能力参考与后续可选迁移）。

---

## 0. 一句话目标

**出海营销 SaaS 的「高颜值、高规范、上下连通」运营 cockpit** —— 集 Art Design Pro X 壳与表格体验、Taste / frontend-design / UI-UX-Pro-Max / SuperDesign 方法论于一体，**超越 Art Pro X**，达到送检与融资演示标准。

**差异化 Slogan（锁定）**：「出海营销最顺手的运营 cockpit」

---

## 1. 战略定案（不可漂移）

| 项 | 🔒 定案 | 禁止 |
|----|---------|------|
| 工程路线 | **SuperDesign 定标杆 → 绞杀升级现网 `frontend/admin`**（方案 **C→A**） | 另起第二套生产壳并行维护 |
| UI 库 | **Ant Design Vue 唯一** + `youding-admin-kit` | Element / Naive 整库并进 |
| 布局 | **YoudingProLayout** 统一 Platform / Client / Agent（一壳三 accent） | client/agent 各写一套独立 layout 长期并存 |
| 页面结构 | **YdPage 契约** 全站唯一内脏布局 | 裸 `a-table` + 随意标题区 |
| 表格 | **`useYoudingTable` + `YdDataTable` + `YdTableColumnSettings`** | 页内手写 `columns` 且无列设置 |
| 后端 | FastAPI 不动；Admin **BFF** `/api/v1/admin-bff/*` | 前端直连散落权限逻辑 |
| Vben | **只抽取**：Worktab、preferences 数据结构、`v-access` 思路 | 送检前全量迁 `admin-vben` |
| 测试节奏 | **P0–P2 UI/功能完成后** 再跑全量门禁 | 未达标壳层前优先写报告 |

---

## 2. 四层架构（Omni Pro 栈）

```
L4 体验层   — 90 秒融资/送检路径、暗色同等完成度、微动效
L3 业务层   — 出海 SLA、询盘队列、AI Copilot 槽、三角色 BFF
L2 Pro 壳层 — Worktab、主题抽屉、Ctrl+K、通知、租户上下文条
L1 设计引擎 — frontend-design → Taste 旋钮 → UI-UX-Pro-Max 检索 → SuperDesign 拍板
```

**依赖方向**：L1 → L2 → L3 → L4（不允许跳过 L2 在单页堆功能）。

---

## 3. 设计引擎流水线（每次 UI 任务必走）

| 步骤 | 工具/Skill | 产出 |
|------|------------|------|
| 0 | **frontend-design** | 确认 Purpose / Tone / Constraints / Differentiation |
| 1 | **Taste Skill** | 应用全局 + 分区域三旋钮（§4） |
| 2 | **UI-UX-Pro-Max** | 按页面类型检索：Style / Palette / Font / UX Rules |
| 3 | **SuperDesign** | 仅 **Dashboard、租户、询盘** 三标杆页：baseline → branch 5 版 → **Master UI** |
| 4 | **Taste redesign-skill** | 老页 audit → 套 YdPage，禁止单页「自由发挥」 |

---

## 4. Taste 三旋钮（🔒 锁定值）

### 4.1 全局默认

| 旋钮 | 值 | 含义 |
|------|-----|------|
| **DESIGN_VARIANCE** | **5** | 壳与 Dashboard 略现代；列表页稳 |
| **MOTION_INTENSITY** | **3** | 页面切换、抽屉、数字滚动；无 scroll 炫技 |
| **VISUAL_DENSITY** | **7** | 运营 cockpit 偏密 |

### 4.2 分区域 Override（全都要，分区生效）

| 区域 | Variance | Motion | Density | 气质 |
|------|----------|--------|---------|------|
| Dashboard / 登录 | **6** | **4** | **5** | 出海 brand-hero + 轻动效 |
| 列表 / 财务 / 询盘 | **4** | **2** | **8** | Art Pro 高密度表格 |
| 设置 / Drawer / 表单 | **3** | **2** | **6** | soft-skill 克制精致 |

### 4.3 Master UI 气质权重（🔒 合成公式）

- **列表与壳**：**B — Stripe / Art Pro**（数据感、表格专业）权重 **70%**
- **Dashboard 首屏**：**C — 出海 DTC SaaS**（KPI 冲击、brand-hero）权重 **20%**
- **表单与 Drawer**：**A — Linear / 飞书**（克制、干净）权重 **10%**

---

## 5. frontend-design 五维约束（🔒 锁定）

| 维度 | 要求 | 禁止（AI slop） |
|------|------|-----------------|
| **Typography** | Display/数字：`Plus Jakarta Sans`；中文：`PingFang SC` / `Source Han Sans SC`；表格 `tabular-nums` | Inter / Arial / 纯 system-ui 作为唯一字体 |
| **Color** | `--uj-*` token 树；主色 `#2563eb` 可配置；**单一 accent** 用于待办/状态 | 全站紫渐变、 evenly-distributed  timid palette |
| **Motion** | CSS/Ant 过渡；Dashboard 可选 stagger；Motion 强度 ≤ 区域上限 | 满屏 scroll-trigger / magnetic |
| **Layout** | YdPage 契约；侧栏+顶栏+Worktab | 每页自创 hero 三栏模板 |
| **Detail** | surface 分层阴影；空值 `--`；圆角来自 token | 每页不同圆角/阴影 |

---

## 6. 视觉 Token（🔒 v3 目标结构）

在 `design-tokens.scss` / `design-tokens-v2.scss` 上演进为 **v3**，新增：

```css
/* 主题模式 */
--uj-theme: light | dark;           /* 同一组件树，禁止维护两套页面 */
--uj-accent-role: platform | client | agent;

/* Surface 模式（全都要） */
--uj-mode-surface: default | elevated | brand-hero;
/* default   → 列表、表格（Art Pro 白底细线） */
/* elevated  → 卡片、Drawer、通知 */
/* brand-hero→ Dashboard 顶区、登录品牌屏 */

/* 布局 */
--uj-sidebar-width: 240px;
--uj-worktab-height: 40px;
--uj-page-max-width: 1440px;       /* 超宽屏居中 */

/* 阴影（kit 已有扩展） */
--yd-shadow-card: 0 4px 24px rgba(15, 23, 42, 0.06);
```

**Ant Design Vue ConfigProvider** 必须与 `--uj-*` 同步（主色、圆角、字体）。

---

## 7. YoudingProLayout（L2 壳 — 🔒 能力清单）

### 7.1 必须有

- [ ] 侧栏：折叠、分组、flyout 子菜单（延续现网 `layout/index.vue` 能力并统一）
- [ ] 顶栏：面包屑 / 页标题、**Ctrl+K**、通知、用户、**租户/角色上下文条**
- [ ] **Worktab 多标签**（Vben 抽取，默认开启，可用户关闭）
- [ ] **主题配置抽屉**：亮/暗、主色、圆角 scale、紧凑度、侧栏宽
- [ ] **今日队列 FAB 或顶栏入口**：询盘 / 发布 / 履约未读
- [ ] **AI Copilot 槽**（壳层右侧可折叠，非业务页硬编码）
- [ ] **送检模式**：隐藏 stub 菜单，仅暴露 P0 polished 路径

### 7.2 超越 Art Pro X（必须有叙事）

1. 上下连通：壳 ↔ kit ↔ 页面 ↔ BFF 权限  
2. 三角色一设计语言（accent 区分）  
3. 出海场景内置（SLA、队列、AI 入口）  
4. 列/密度/主题用户可配 + localStorage  
5. 任意菜单点进均为 Pro 页，无「生成页简陋感」

---

## 8. YdPage 契约（🔒 全站唯一页面布局）

```
┌─ YdPageHeader ─────────────────────────────────────────┐
│ 标题 + 副标题 + 主操作（≤3 直出 + 「更多」）              │
├─ YdStatsRow（可选）─────────────────────────────────────┤
│ 2–4 × YdStatsCard                                       │
├─ YdSearchBar ────────────────────────────────────────────┤
│ 筛选项 | 查询 重置 | [列设置] [刷新] [导出] [密度]        │
├─ YdDataTable ────────────────────────────────────────────┤
│ visibleColumns · 居中 · 无序号列 · 空值 -- · 分页         │
└─ YdDetailDrawer（详情统一右侧，禁止 Modal 堆叠）──────────┘
```

### 8.1 表格工具栏（Art Pro 全家桶）

| 能力 | 实现 |
|------|------|
| 列显隐 / 顺序 | `YdTableColumnSettings` + `useYoudingColumnLayout` |
| 列顺序持久化 | `columnOrderKey` → localStorage |
| 密度 | compact / default / comfortable（Ant table size + token） |
| 刷新 | `reload()` |
| 全屏 | 表格容器 fullscreen |
| 导出 | CSV，与询盘等已有 export 对齐 |

### 8.2 表格约定（延续 `conventions/table.md`）

- 单元格、表头 **居中**
- **禁止**序号列
- 空值 **`--`**（保留 `0` / `false`）
- 操作列 **≤3** 按钮，超出 **「更多」** 下拉
- 权限按钮对接 `authList.code` / `v-access`

---

## 9. 标杆页与铺量顺序（🔒 P0–P2）

### P0（送检/融资 blocker，必须先 polished）

1. **运营 Dashboard** — `views/admin/dashboard.vue`  
2. **租户管理** — `views/admin/tenants.vue`  
3. **询盘管理** — `views/inquiries/index.vue`  
4. **YoudingProLayout** — `layout/index.vue` 演进  
5. **主题抽屉 + 暗色**  
6. **`_generated/*` 12 页** — 全部套 YdPage（`gen-crud-from-openapi.mjs` 模板锁定）

### P1

- 队列三页：`client/queues/{inquiries,publish,fulfillment}.vue`  
- 财务中台：`admin/finance/index.vue` + 子页顶栏一致  
- 表格工具栏：全屏、密度、导出统一  

### P2

- Client / Agent 迁入 **同一 Pro Shell**（仅 accent + 菜单不同）  
- 剩余 admin 子模块按菜单优先级批量 YdPage  
- 水印、Worktab 与 keep-alive 策略  

---

## 10. 90 秒融资 / 送检路径（🔒 不可改顺序）

| 时间 | 画面 | 验收 |
|------|------|------|
| 0–15s | 分屏登录 + brand-hero | 无 placeholder |
| 15–30s | Dashboard KPI + 待办询盘 **可点击** | 进 `/inquiries` |
| 30–50s | 租户 / 询盘：列设置 + Drawer + 操作 | 无裸 `a-table` |
| 50–70s | 主题抽屉：暗色 + 换主色 | 同页不闪崩 |
| 70–90s | Client 壳 **同布局** 不同 accent | 一壳三角色叙事 |

**零容忍**：「敬请期待」、演示 `message.info`、无 handler 按钮、生成页简陋壳。

---

## 11. 工程文件锚点（🔒 实现必须落在此）

| 用途 | 路径 |
|------|------|
| Pro 壳 | `frontend/admin/src/layout/index.vue` → `YoudingProLayout` |
| 设计 token | `frontend/admin/src/styles/design-tokens*.scss` |
| Kit 组件 | `frontend/admin/src/components/youding/` |
| Kit 源码 | `frontend/youding-admin-kit/` |
| 表格 composable | `useYoudingTable.ts` / `useYoudingColumnLayout.ts` |
| CRUD 模板 | `frontend/admin/scripts/gen-crud-from-openapi.mjs` |
| 表格约定 | `frontend/youding-admin-kit/conventions/table.md` |
| 抽取清单 | `frontend/youding-admin-kit/MANIFEST.md` |
| BFF 契约 | `docs/youding-admin-composite-blueprint.md` |

---

## 12. 禁止清单（🔒 HARD-GATE）

以下出现即视为 **偏离锁定规格**，PR 应拒绝或返工：

1. 新页面裸写 `a-table` 且不套 YdPage / `YdDataTable`  
2. 新 layout 分叉（client/agent 再写第三套壳）  
3. 页内硬编码 `#2563eb` 而不走 token  
4. 列不可配置的管理列表（无 `YdTableColumnSettings`）  
5. 占位文案：「对接中」「敬请期待」「演示，可对接…」  
6. 按钮无 `@click` / 仅 `message.info` 敷衍  
7. 引入第二 UI 组件库  
8. 送检演示路径上出现 stub 菜单或未 YdPage 的 `_generated` 页  
9. 未经验收修改本文 **🔒 定案** 表中的数值与路线  

---

## 13. 六周节奏（🔒 里程碑）

| 周 | 交付 |
|----|------|
| W1 | SuperDesign 三标杆 5 选 1 → Master UI + Token v3 定稿 |
| W2 | YoudingProLayout + Worktab + 主题抽屉（亮/暗） |
| W3 | P0 三页标杆 + `_generated` 模板统一 |
| W4 | P1 队列 + 财务 + 表格工具栏全家桶 |
| W5 | Client/Agent 同壳 + AI 槽 + 队列入口 |
| W6 | 90 秒路径演练 + 送检截图 + 门禁（测试放此周） |

---

## 14. 与旧文档关系

| 文档 | 关系 |
|------|------|
| `youding-admin-overhaul-prd.md` | 产品 OKR 仍有效；**壳底座以本文为准** |
| `youding-admin-composite-blueprint.md` | BFF/UAC 仍有效 |
| `youding-admin-kit/MANIFEST.md` | 抽取来源；落地状态以本文 P0–P2 为准 |
| `open-source-audit/02-art-design-pro-edge.md` | 对标参考，目标 **超越** |

---

## 15. 变更控制

- 变更本文档须：说明原因 + 对 90 秒路径的影响 + 产品负责人确认  
- AI / 开发任务 **必须先读本文** + `.cursor/rules/00-youding-omni-pro-lock.mdc`  
- `docs/pm-dev-task-progress.json` 中 BJ-02 等 UI 任务 **不得标记 100%** 除非满足 §8 与 §12  

---

*本文档由 2026-06-02 Omni Pro 设计对话锁定生成。*
