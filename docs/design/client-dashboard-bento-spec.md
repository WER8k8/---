# Client Dashboard · Bento 规范（视觉交付 v1）

> **主责**：陈列视觉设计师 · **指导**：SaaS 产品策略专家  
> **工程落地**：`youding-admin-kit` + `admin-vben` Client 首页  
> **版本**：v1 · 2026-06-01  

---

## 1. 画布与栅格

- 内容区 max-width：**1280px**，居中  
- 栅格：**12 col**，gap **16px**，page padding **24px**（`--uj-space-page`）  
- 卡片：圆角 **12px**，边框 **无**，阴影 `0 1px 3px rgba(0,0,0,.06)`  
- 背景页：`#f8fafc`（tokens v2）

---

## 2. Header 工作区（固定 56px）

```
[租户 Logo 32px | 公司名 15px semibold]  ···  [套餐徽章] [用量条 120px] [通知] [头像]
```

- 用量条：高 6px，圆角 full；`<80%` brand / `80–99%` warning / `100%` danger  
- 套餐徽章：见 `plan-copy-deck.md` 色值  

---

## 3. Bento 首屏（优先级序）

| 格子 | 栅格 | 内容 | 空状态 CTA |
|------|------|------|------------|
| **Onboarding** | col 4 | 6 步进度条，当前步高亮 | 「完成第 2 步：绑定独立域 →」 |
| **未读询盘** | col 4 | 数字 + 最近 1 条摘要 | 「去配置询盘入口 →」 |
| **发布进行中** | col 4 | 数字 + 最近 1 条任务 | 「创建第一条发布 →」 |
| **今日待办** | col 8 | Art 精简 5 行 | — |
| **套餐/续费** | col 4 | 套餐名 + 到期日 + 按钮 | Trial 显示「升级专业版」 |

**次要区（可 W2+）**：7 日询盘 sparkline 单条，高度 ≤120px，**禁止** 3D 图表。

---

## 4. 侧栏（四支柱）

- 宽 **220px**；icon **Lucide** 20px；active **左侧 3px brand 条**  
- 项：获客 / 发品 / 履约 / 账户 — **禁 emoji**  
- 底部：折叠 + 「查看我的网站」链 Nuxt  

---

## 5. 财旺 FAB

- 64px，`--uj-glass`，右下 24px  
- 抽屉宽 420px，glass 头图 + 对话区  

---

## 6. 动效

- 卡片 hover：`translateY(-1px)` + 阴影略增，**150ms**  
- 骨架屏：Bento 6 格占位，**禁止** 全屏 spin  

---

## 7. 移动（W3）

- 仅 3 卡：Onboarding 摘要 / 未读询盘 / 用量  
- 链「桌面查看完整工作台」  

---

## 8. 工程映射

| 视觉块 | kit 组件 |
|--------|----------|
| Onboarding | `YdOnboardingCard.vue` |
| 询盘/发布 KPI | `YdStatsCard.vue` 扩展 |
| 今日待办 | `YdTodayQueue.vue` |
| 用量 | `YdUsageMeter.vue` |
| Header | `YdWorkspaceHeader.vue`（待建） |

---

*视觉 v1 · 开发按此实现 · 变更需 SaaS+视觉双签*
