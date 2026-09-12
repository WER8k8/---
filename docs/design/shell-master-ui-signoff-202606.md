# 壳层 Master UI 签认包（JD-01 草案）

> **状态**：草案 · 待 VIS-NAV-01 / PM-NAV-01 / ARCH-NAV-01 联合签字  
> **依据**：`docs/youding-omni-pro-design-LOCKED.md` §4–§7  
> **代码基线**：`YdProSidebar` · `YdProTopbar` · `YdProWorktabs`（WP-NAV-02 ✅）

---

## 1. 设计读数（Design Read）

**B2B 出海运营 cockpit**，受众为租户管理员与超管；视觉语言为 **薄荷玻璃 + Stripe 式数据壳**，Taste **5 / 3 / 7**（略现代、动效克制、偏密）。

---

## 2. 壳层三区对照（已实现 vs 待签）

| 区域 | 组件 | Token / 气质 | 签认项 |
|------|------|--------------|--------|
| 侧栏 | `YdProSidebar.vue` | `--uj-brand-muted` 激活、flyout 子菜单 | ☐ 折叠仅 1 项高亮 ☐ flyout 不挡内容 |
| 顶栏 | `YdProTopbar.vue` | display 字体标题、玻璃底 + 轻 inset 阴影 | ☐ Ctrl+K ☐ 通知面板 ☐ 移动端汉堡 |
| 标签+上下文 | `YdProWorktabs.vue` | 角色胶囊 + 左条激活 tab | ☐ 中文名来自菜单 ☐ 关闭其他 |

---

## 3. 一壳三 accent（WP-NAV-04 视觉稿要求）

| Shell | 路由前缀 | 主 accent | 角色胶囊色 |
|-------|----------|-----------|------------|
| Platform | `/admin` `/dashboard` | `#4a9b8c` 薄荷 | `--uj-brand-deep` |
| Client | `/client` | `#5a9fd4` 蓝 | `#1d4ed8` 浅底 |
| Agent / Partner | `/agent` `/partner` | `#4db6a0` 青 | `#0f766e` 浅底 |

**视觉部交付**：各 accent 1 张 1440×900 静态截图（含侧栏+顶栏+标签），文件名约定 `screenshots/shell-{platform|client|agent}-202606.png`。

---

## 4. 禁止项（AI slop · LOCKED §5）

- 全站紫渐变、Inter 独占、每页不同圆角
- 侧栏/顶栏双重重影渐变（已修：动效只在图标内层）
- 假数据充 Dashboard KPI（送检须真实或显式 `mode: mock`）

---

## 5. 签字栏

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 视觉 VIS-NAV-01 | | | ☐ 通过 ☐ 修改后通过 |
| UX UX-NAV-01 | | | ☐ 通过 ☐ 修改后通过 |
| PM PM-NAV-01 | | | ☐ 通过 |
| 架构 ARCH-NAV-01 | | | ☐ 通过 |
| SaaS 专家 | | | ☐ 否决 Stub |
