# 视觉 / 美工部 · 本周任务单

> **下发**：PM-NAV-01 · **截止**：2026-06-09  
> **您交图后**：前端按图做第 4 步，不再盲改  
> **规格依据**：`docs/youding-omni-pro-design-LOCKED.md` · Taste 5/3/7

---

## 任务 A · 三张外壳效果图（必交）

每张 **1440 × 900 px**，PNG，存到：

`docs/design/screenshots/shell-{platform|client|agent}-202606.png`

### 必须画进图里的区域

| 区域 | 要求 |
|------|------|
| 侧栏 | 含 1 个分组标题、1 个带子菜单的项、1 个叶子项；**仅 1 项高亮** |
| 顶栏 | 左：页面标题 + 副标题；右：搜索、通知、头像 |
| 标签区 | 上：角色胶囊 + 用户名；下：2～3 个打开的标签，当前标签有左色条 |
| 内容区 | 可放灰色占位块，**不用画业务细节** |

### 三张图的区别（只改 accent，布局完全相同）

| 文件名 | 角色 | 主色 | 侧栏品牌字 |
|--------|------|------|------------|
| `shell-platform-202606.png` | 超管 | 薄荷 `#4a9b8c` | 优丁建材 |
| `shell-client-202606.png` | 租户 | 蓝 `#2563eb` | 出海工作台 |
| `shell-agent-202606.png` | 代理 | 青 `#0d9488` | 代理中心 |

### 气质参考（禁止）

- 禁止全站紫渐变、Inter 独占、每块不同圆角  
- 背景：淡色 mesh（平台薄荷 / 租户淡蓝 / 代理淡青）  
- 卡片：白玻璃感 + 轻阴影，**不要**强磨砂导致字重影  

---

## 任务 B · 壳层签认表（交图时一并填）

文件：`docs/design/shell-master-ui-signoff-202606.md` 第五节签字栏

---

## 任务 C · P0 三页审计（6/10 前）

文件：`docs/design/p0-page-visual-audit-202606.md`

只审这三页，每页 Must-fix **≤5 条**：

1. 运营看板 `/admin/dashboard`  
2. 租户管理 `/admin/tenants`  
3. 询盘管理 `/inquiries`  

打分 1–5：Typography / Color / Density / YdPage 契约

---

## 研发已先做的（供对照，不是最终稿）

本地 `http://127.0.0.1:5173/login` 登录后可看：

- 超管：点「运营看板」→ 看壳层薄荷底  
- 租户：进 `/client/dashboard` → 应变为淡蓝 accent  
- 代理：进 `/agent/performance` → 应变为淡青 accent  

**视觉部职责**：指出与定稿不符处，写进 Must-fix，不要求自己写代码。

---

## 交付 checklist

- [ ] A1 platform 效果图 PNG  
- [ ] A2 client 效果图 PNG  
- [ ] A3 agent 效果图 PNG  
- [ ] B 签认表签字  
- [ ] C 三页审计表填完  

交齐后 @ PM → 开第 4 步全面实现 + 第 5 步三页抛光。
