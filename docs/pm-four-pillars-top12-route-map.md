# PM-02 · 四支柱 ↔ Top12 送检路由映射

> **签发**：产品经理 · **截止**：S0 / 6/8  
> **对齐**：思维导图「三壳 IA」· [`送检演示脚本-v2-鉴定面.md`](./送检演示脚本-v2-鉴定面.md) · BFF seed

---

## 1. 租户 Client · 四支柱

| 支柱 | 用户问题 | 菜单标签 | 路由 | BFF seed | Top12 |
|------|----------|----------|------|----------|-------|
| **工作台** | 今天干什么？ | 工作台 | `/client/dashboard` | `ClientDashboard` | 演示步 3.1 |
| **获客** | 有新询盘吗？ | 获客 · 询盘 | `/client/inquiries` | `ClientInquiries` | 演示步 3.2 |
| **发品** | 店正常吗？ | 发品 · 产品 / 内容 | `/client/products` · `/client/content` | `ClientProducts` · `ClientContent` | —（送检走超管业务链） |
| **账户** | 套餐够吗？ | 账户 · 套餐 | `/client/billing` | `ClientBilling` | — |

**Hide/Lab**（不进四支柱菜单）：见 [`pm-stub-visibility-matrix-v1.md`](./pm-stub-visibility-matrix-v1.md)

---

## 2. 代理 Agent · 五栏

| 栏位 | 路由 | BFF seed | 送检 |
|------|------|----------|------|
| 首页 | `/agent/performance` | `AgentPerformance` | 3.3 KPI 白底 |
| 客户 | `/agent/traffic` | `AgentTraffic` | — |
| 开户 | `/agent/account-opening` | `AgentAccountOpening` | 3.4 |
| 佣金 | `/agent/commission` | `AgentCommission` | — |
| 预警 | `/agent/churn-warning` | `AgentChurnWarning` | — |

**禁止**：任何 `/admin/*` 或「查看全平台」（FE-03 ✅）

---

## 3. 超管 Platform · Top12 鉴定面

| # | 脚本步 | 路由 | BFF 节点 | 截图 |
|---|--------|------|----------|------|
| 1 | 1.1 | `/login` | — | cert-01 |
| 2 | 1.2 | `/admin/tenants` | `PlatformTenants` | cert-02 |
| 3 | 1.3 | `/admin/hierarchy` | `PlatformHierarchy` | cert-03 |
| 4 | 1.4 | `/admin/aggregation` | `PlatformAggregation` | cert-04 |
| 5 | 1.5 | `/system-health/dashboard` | `PlatformSystemHealth` | cert-05 |
| 6 | 1.6 | `/admin/finance` | `PlatformFinance` | cert-06 |
| 6b | 1.6+ | `/admin/finance/payment-orders` | `PlatformPaymentOrders` | MOD-09 租户订单 |
| 7 | 2.1 | `/products` | `PlatformProducts` | cert-07 |
| 8 | 2.2 | `/products/categories` | `PlatformCategories` | cert-08 |
| 9 | 2.3 | `/international/inquiries` | `PlatformIntlInquiries` | cert-09 |
| 10 | 2.4 | `/seo-matrix/publish` | `PlatformSeoPublish` | cert-10 |
| 11 | 2.5 | `/admin/ai-center/content` | `PlatformAiContent` | cert-11 |
| 12 | 2.6 | `/admin/ai-engine/trade-intel` | `PlatformTradeIntel` | cert-12 |

**多角色演示**（同脚本 §3）：`/client/dashboard` · `/client/inquiries` · `/agent/performance` · `/agent/account-opening`

**菜单源**：`frontend/admin/src/constants/stubVisibility.ts` → `CERT_INSPECTION_MENU`

---

## 4. 验收签字

- [x] PM：四支柱与 Top12 无孤儿路由  
- [x] SaaS：30s 三问均可从四支柱首屏回答  
- [ ] 前端：BFF fallback seed 与现网 router 路径一致  
- [ ] QA：脚本 v2 全流程 30min 彩排

---

*PM-02 v1 · 2026-06-02*
