# 产品经理 × SaaS 专家 · 三壳产品改造方案（送检级）

> **联合主笔**：产品经理 + SaaS 产品策略专家  
> **触发**：超管 / 各级代理 / 租户页面「太糙」— 对照抖音 B 端审美（琢磨先生等切片所代表的 **Linear/Notion 克制风**），**不具备省级评测中心现场观感**  
> **原则**：工程门禁已绿 ≠ 产品可送检；**评测员 30 秒第一印象** 由 PM+SaaS+视觉 负责  
> **版本**：v1 · 2026-06-01  

---

## 〇、联合结论（先看）

| 壳 | 现网评级 | 送检风险 | 改造优先级 |
|----|----------|----------|------------|
| **租户 Client** | D+ | 中 — 菜单像个人笔记，Dashboard 像模板 | **P0** |
| **代理 Agent** | D | 高 — 彩虹渐变 KPI + 链超管 + emoji | **P0** |
| **超管 Platform** | F | **极高** — 菜单爆炸、玻璃 hero 内页、实验室外露 | **P0** |

**一句话方案**：三壳 **信息架构重写 + 视觉降噪 + 送检路径专用「鉴定面」** — 不是 234 页搬家，是 **每壳只 polished 送检必看 + 主链**。

**琢磨先生 / 抖音热切片在批评什么（ECC 统一理解）**：

```text
❌ emoji 当图标、彩虹渐变 KPI 卡、管理页里塞 landing hero
❌ 侧栏 20+ 项、实验室和生产线混一排
❌ 空状态「暂无数据」、英文假字段、点进去 toast 演示
❌ 代理页出现「查看全平台」、租户页像 2019 Bootstrap 后台

✅ 3 秒读懂主任务、5 项内导航、灰阶+一处品牌色
✅ 首屏 Bento：待办 > 图表、真实 API、骨架屏
✅ 角色零泄漏、像 Linear/飞书/Stripe 克制
```

---

## 一、现网深度诊断（代码级证据）

### 1.1 租户 Client — `views/client/layout.vue`

| 问题 | 证据 | 送检/商业伤害 |
|------|------|---------------|
| **15 项 emoji 硬编码菜单** | `menuItems` 含 🏠📦🎬🎞️🌐🤖 等 | 不像 SaaS，像个人工具箱 |
| **无 BFF 动态菜单** | 本地数组，0 BFF | 套餐无法门控 |
| **Header 无套餐/用量** | 仅公司名 + 退出 | 付费感为零 |
| **实验室进租户菜单** | 文章转视频、视频工厂、出口 IP、AI 场景 | 评测员认为功能堆砌/未完成 |
| Dashboard | 全宽渐变 welcome + emoji 快捷操作 | 抖音反面教材「渐变大海报」 |

```66:82:frontend/admin/src/views/client/layout.vue
const menuItems = [
  { label: '工作台', path: '/client/dashboard', icon: '🏠' },
  // ... 共 15 项，含 🎬 🎞️ 🌐 🤖
]
```

### 1.2 代理 Agent — `views/agent/layout.vue` + `performance.vue`

| 问题 | 证据 | 伤害 |
|------|------|------|
| emoji 侧栏 6 项 | 同 Client 模式 | 不专业 |
| **彩虹渐变 KPI 四卡** | `from-blue-500 via-blue-600 to-purple-700` | 2019 模板风，琢磨类视频必批 |
| **代理页链超管** | `router.push('/admin/aggregation')` 「查看全平台」 | **角色泄漏**，送检现场致命 |
| 无 L2/L3 差异 | 同一套 6 菜单 | 省代/市代叙事不清 |
| 无开户/待办队列 | 只有看板 | 代理「我今天该干什么」答不出 |

### 1.3 超管 Platform — `layout/index.vue` + `admin/hierarchy`

| 问题 | 证据 | 伤害 |
|------|------|------|
| **巨型侧栏** | 单文件 1200+ 行，多组菜单 | 评测员认为「研发中系统」 |
| **admin/layout 空壳** | 仅 `<router-view/>` | 无 Platform 统一壳 |
| **层级页 hero-glass** | 全屏玻璃营销块 + 四级树 UI 过重 | 像官网不像治理后台 |
| 实验室与生产混排 | capability-hub、demo-rehearsal、v2ray… | 送检清单外仍可见即扣分 |
| 品牌文案 | 侧栏「优丁建材」 | 与「AI-SaaS 平台」申报名需一致策略 |
| 送检 12 模块路径分散 | `/admin/*` `/dashboard` `/products` 混用 | 演示脚本 30min 像打迷宫 |

---

## 二、三壳目标信息架构（PM+SaaS 定稿）

### 2.1 租户 Client（L4）— 「今日经营」

**首页问题**：我今天该干什么？店还正常吗？

| 一级（≤4） | 二级（送检+主链） | 隐藏/PlanGate |
|------------|-------------------|---------------|
| **工作台** | Dashboard Bento | — |
| **获客** | 询盘 inbox、IM 配置 | 国际询盘 Pro+ |
| **发品** | 产品、内容、发布枢纽 | 视频工厂 Lab |
| **账户** | 套餐/用量、域名、设置、发票 | 出口 IP Enterprise |

**+1 财旺 FAB**，**不是菜单**。

**Dashboard Bento（送检必看）** — 见 `docs/design/client-dashboard-bento-spec.md`。

**删除出租户侧栏**：文章转视频、视频工厂、出口 IP、AI 场景模型 → Lab 或 Plan Gate。

---

### 2.2 代理 Agent（L2/L3）— 「业绩与开户」

**首页问题**：我能赚多少？下一个该开谁？

| 一级（≤5） | L2 省代 | L3 市代 |
|------------|---------|---------|
| **首页** | 业绩 + 下级汇总 | 业绩（无下级汇总） |
| **客户** | 我的客户 inbox | 同左 |
| **开户** | 开户申请队列 | 同左 |
| **佣金** | 明细 + 待结算 | 同左 |
| **预警** | 流失预警 | 同左 |

**禁止**：任何 `/admin/*` 链接、彩虹渐变 KPI、emoji。

**KPI 视觉改为**：白底卡片 + 左色条 3px（单品牌色）+ 数字 + 环比小字 — **一张图一个主色**。

**送检演示**：只演示 **业绩首页 + 客户列表 + 开户提交**（3 页）。

---

### 2.3 超管 Platform（L1）— 「平台稳不稳、钱对不对」

**三区 Tab，主路径 ≤12，不是 200 路由侧栏**

| Tab | 送检必演 | 日常 | 进实验室 |
|-----|----------|------|----------|
| **A 运营** | 租户总览、发布队列、询盘大盘 | 告警 | — |
| **B 商业** | 营收/分润、发票 | 对账 | — |
| **C 治理** | 层级管理、权限、审计、系统健康 | AI 配置单页 Tab | GEO/RAG/v2ray… |

**层级管理页改造**：

- **删** 全屏 hero-glass 营销块  
- **改** 标准 Platform 顶栏 + 左树右详情（Ant Design Tree + Descriptions）  
- **送检叙事**：「四级组织架构管理」— 专业、克制、可截图  

**送检专用「鉴定面」**（30 分钟脚本只走此线）：

```text
/login（超管）
  → /admin/operations/tenants      租户总览
  → /admin/commercial/revenue        商业
  → /admin/hierarchy                 层级（改造后）
  → /admin/governance/audit          审计
  → /admin/governance/system-health  系统健康
  → /products + /international/inquiries  （业务链 2 步）
  → /client/dashboard                切租户视角 1 屏
```

**实验室**：Settings → 「实验室」抽屉 + 二次确认 + 水印 **「非送检范围」**。

---

## 三、视觉与营销标准（对标抖音「高级感」）

### 3.1 三壳共用 Design Constitution

| 规则 | Client | Agent | Platform |
|------|--------|-------|----------|
| 图标 | Lucide 线图标 | 同 | 同 |
| 主色 | `#2563eb` 一点 | 同 | 同 |
| KPI 卡 | 白底+shadow | **禁渐变** | 白底或浅灰 |
| 圆角 | 12px | 12px | 8px（略密） |
| 边框 | 默认无，间距分组 | 同 | 表格区可有 1px |
| 字体 | 15/14/12 三级 | 同 | 同 |
| 空状态 | 一句人话 + CTA | 同 | 同 |

### 3.2 营销 × 送检口径一致

- 申报名：**优丁建材 AI-SaaS 智能营销平台 V2.0**  
- 侧栏品牌：**优丁** + 副标 **SaaS 工作台**（Tenant）/ **平台治理**（Platform）/ **代理中心**（Agent）  
- 对外不说「234 模块」— 说 **四支柱 + 四级架构 + 12 项送检能力**  
- 手册截图 **只截鉴定面**，不截实验室  

---

## 四、具体改造清单（可执行）

### Phase S0 · 送检阻断清零（1 周，与 W1 并行）

| ID | 动作 | 壳 | 负责 |
|----|------|-----|------|
| S0-1 | Client 菜单 **15→4 支柱** mapping + Hide 5 实验室项 | Client | PM+BFF |
| S0-2 | Agent **删除** 「查看全平台」链 `/admin/aggregation` | Agent | 前端+安全 |
| S0-3 | Agent KPI **去渐变** → 白底色条卡 | Agent | 视觉+前端 |
| S0-4 | hierarchy **删 hero-glass** → 树+详情标准页 | Platform | 视觉+前端 |
| S0-5 | Platform 侧栏 **送检模式**：仅展示鉴定面 12+2 项 | Platform | PM+BFF |
| S0-6 | 三壳 **emoji→Lucide** | 全 | 视觉+前端 |
| S0-7 | `docs/送检截图/` **按鉴定面重拍 12 张** | 全 | PM+营销 |

### Phase S1 · SaaS 商品化（2–3 周，W2）

| ID | 动作 | 交付 |
|----|------|------|
| S1-1 | Client Bento Dashboard + Header 用量 | kit 组件 |
| S1-2 | TenantLogin 分屏 | kit |
| S1-3 | Agent 客户/开户 **inbox 队列** | Art table |
| S1-4 | Platform 三区 Tab Layout（Vben fork 或现 layout 重构） | admin-vben |
| S1-5 | L2/L3 菜单差异（BFF seed） | 后端 |

### Phase S2 · 送检材料（1 周）

| ID | 交付 |
|----|------|
| S2-1 | 《用户操作手册-送检版》只写鉴定面 |
| S2-2 | 30min 演示脚本 v2（按 §2.3 路径） |
| S2-3 | PM L3 六项签字 + 12 截图 |
| S2-4 | 现场口头声明「实验室非送检范围」稿 |

---

## 五、页面级 Before / After（PM 验收表）

### Client Dashboard

| Before | After |
|--------|-------|
| 渐变大海报 + 4 数字 | Bento：Onboarding / 询盘 / 发布 / 待办 |
| emoji 快捷操作 | 3 个文字按钮 + 图标 Lucide |
| 套餐在右侧小卡 | Header 用量条 + 账户支柱 |

### Agent Performance

| Before | After |
|--------|-------|
| 4 张彩虹 gradient 卡 | 4 张白底 KPI，左色条 |
| 查看全平台 → admin | **删除**；L2 仅「我的下级」折叠区 |
| 仅看板 | 顶部「待开户 3 · 待跟进 5」队列条 |

### Platform Hierarchy

| Before | After |
|--------|-------|
| hero-glass 全屏 + 玻璃树 | 标准页：标题 + 树表 + 右侧详情抽屉 |
| 「层级管理中心」营销文案 | 「组织架构」+ 四级说明一行 |
| 添加节点大按钮裸露 | Toolbar：添加 / 导入 / 导出 |

---

## 六、SaaS 专家 · 送检现场话术（30 秒）

> 本平台是 **多租户 AI 营销 SaaS**：租户侧按 **获客、发品、履约、账户** 四类工作组织；代理侧管 **业绩、客户、开户、佣金**；平台侧 **运营、商业、治理** 三区管理四级架构。  
> 演示路径为 **送检功能清单 12 项**，实验室能力默认关闭，**不在本次检测范围**。  
> 界面遵循 **简洁、任务导向、数据来自真实 API** — 与 GB/T 25000.51 易用性要求一致。

---

## 七、产品经理 · 送检演示脚本修正（v2 要点）

**原脚本问题**：路径跨 `/dashboard` `/admin` `/products`，超管与租户混，易穿帮。

**v2 结构**：

| 段 | 时长 | 角色 | 路径 |
|----|------|------|------|
| 1 | 5min | super_admin | 鉴定面 6 页（§2.3） |
| 2 | 10min | super_admin | 送检清单 产品→询盘→SEO→AI→健康 |
| 3 | 5min | tenant | Client Dashboard → 询盘 inbox |
| 4 | 5min | agent | 业绩 → 开户申请 |
| 5 | 5min | 口述 | 实验室关闭声明 + Q&A |

**截图命名**：`cert-01-platform-tenants.png` … `cert-12-client-dashboard.png`

---

## 八、视觉 / 营销 · 本周强制交付（接上 masterplan）

| 交付 | 内容 | 截止 |
|------|------|------|
| **V-S0** | Agent KPI 白底色条组件稿 + hierarchy 标准页线框 | 3 天 |
| **V-S1** | 三壳 Lucide icon-map + 禁渐变规范页 | 5 天 |
| **M-S0** | 送检手册目录（只含鉴定面 12 模块） | 3 天 |
| **M-S1** | 30s 口播稿（SaaS 专家 §六 扩展版） | 5 天 |
| **M-S2** | 对比图：现网 vs 目标（Client/Agent/Platform 各 1） | 5 天 |

---

## 九、决议

| # | 决议 |
|---|------|
| R1 | **本方案为三壳改造唯一 PM+SaaS 权威**，优先于「234 路由迁移」 |
| R2 | **S0 送检阻断 7 项** 与 Wave 1 并行，**D+7 必须完成** |
| R3 | Agent **永久禁止** 链 `/admin/*` |
| R4 | Platform **送检模式菜单** 仅鉴定面；实验室 Feature Flag 默认关 |
| R5 | 视觉/营销 **5 天内** 交付 §八，未完成 ECC 红灯 |
| R6 | 重拍 12 张送检截图前，**S0 视觉改造必须 merge** |

---

## 十、相关文档

- [ecc-optimal-saas-masterplan-20260601.md](./ecc-optimal-saas-masterplan-20260601.md)  
- [client-dashboard-bento-spec.md](./design/client-dashboard-bento-spec.md)  
- [送检功能清单-v1.md](./送检功能清单-v1.md)  
- [四壳信息架构与菜单治理.md](./四壳信息架构与菜单治理.md)  

---

*产品经理 × SaaS 专家联合 · 送检级三壳改造 v1*
