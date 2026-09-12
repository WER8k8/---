# PM 总结 · 四层贯通与租户支付链路（L1–L4 × 超管）

> **签发**：产品经理（PM-07）  
> **日期**：2026-06-02  
> **前置**：[`pm-executive-report-summary-20260601.md`](./pm-executive-report-summary-20260601.md) · [`pm-four-pillars-top12-route-map.md`](./pm-four-pillars-top12-route-map.md)  
> **研发任务**：**MOD-09** 四层贯通（本批交付）  
> **适用读者**：Owner · 研发 · QA · 送检彩排

---

## 一、Executive Summary（6/2 增量）

**问题**：Owner 问「L2/L3/L4 与超管是否贯通？」——工程主链路 **已部分贯通**，组织视图与超管财务 **未一体化**。

**PM 判断**：

| 维度 | 贯通度 | 一句话 |
|------|--------|--------|
| **角色与壳** | ✅ 90% | L1 `/admin` · L2 `/partner` · L3 `/agent` · L4 `/client`，代理不可进超管 |
| **开户归属** | ✅ 85% | 代理开户写入 `agent_node_id` / `agent_chain` / `opened_by_agent_user_id` |
| **付费→分润** | ✅ 80% | Mock/真支付 →  provisioning → `accrue_commission_for_payment` |
| **超管纵览** | ⚠️ 60% | 租户全量可见；层级树 L4≠租户；缺租户支付订单 Admin 页 |
| **组织一张图** | ❌ 40% | `AgentAggregationService` Mock 树与 `Tenant` 表双轨；子树范围偏 Mock |

**North Star（本批）**：超管在 **层级管理 cert-03** 能看到 L4 租户挂在其上级代理下；财务板块能串 **租户 → 支付单 → 分润**。

---

## 二、四层模型（产品口径 = 送检口径）

| 层级 | 含义 | 前端壳 | 角色 | 数据主表 |
|------|------|--------|------|----------|
| **L1** | 平台超管 | `/admin/*` | `super_admin` / `admin` | 全量 |
| **L2** | 省级代理 | `/partner/*` | `l2` | `agent_nodes` + 下级租户 |
| **L3** | 市级代理 | `/agent/*` | `l3` / `agent` / `sales` | 同上 |
| **L4** | 官网租户 | `/client/*` | `tenant_admin` | `tenants` |

> **注意**：代码 Mock 树曾用 l4/l5 表示「区/街道代理」，与产品 L4=租户 **语义冲突**。MOD-09 以 **产品口径为准**：UI 仅 L1–L4；API `l4` 层返回 **租户节点**。

---

## 三、贯通矩阵（调研结论 · 6/2）

### 3.1 已贯通（可演示 / 可测）

```text
L2/L3 开户 ──► Tenant(settings.agent_*)
      │
      ▼
L4 付费 ──► PaymentService ──► Provisioning（套餐/Token）
      │
      ├──► FinanceLedgerEntry（超管财务概览）
      └──► AgentCommissionSettlement（代理佣金 + 超管分润结算）

超管：/admin/tenants 全量 · /admin/finance 汇总 · /agent-tree/* CRUD
代理：/agent/dashboard · /agent/clients · /agent/account-opening（L2 同 API、/partner 壳）
```

| 链路 | 证据路径 | 送检脚本 |
|------|----------|----------|
| 超管看租户 | `tenants.py` · `/admin/tenants` | 1.2 cert-02 |
| 超管看层级 | `agent_tree.py` · `/admin/hierarchy` | 1.3 cert-03 |
| 代理开户 | `agent_portal_service.create_account_opening` | 3.4 |
| 租户付费 | `payment.py` · `/client/billing` | 口述 + Mock |
| 分润计提 | `agent_commission_service.accrue_commission_for_payment` | 1.6 财务 |

### 3.2 未贯通 / 半贯通（MOD-09 范围）

| # | 缺口 | 现网表现 | MOD-09 交付 |
|---|------|----------|-------------|
| G1 | L4 不在组织树 | 层级页 L4 列来自 Mock `l4/l5` 代理节点，非 `Tenant` | `l4` 层合并租户节点，`parent_id=agent_node_id` |
| G2 | 子树范围偏 Mock | `_subtree_node_ids` 先 walk `MOCK_TREE` | 优先 DB `agent_nodes` 递归子树 |
| G3 | 层级统计为 0 | DB 节点 `total_clients/revenue` 写死 0 | 按子树内租户 + 支付/台账聚合 |
| G4 | 超管无支付订单列表 | `GET /payment/orders` 无 Admin UI | `/admin/finance/payment-orders` |
| G5 | 代理看板 Mock 回退 | 无绑定租户时 `data_source: mock` | 保留 Mock 作空库演示；有租户必为 `db` |

### 3.3 明确 Out-of-Scope（本批不做）

- 重写 `get_full_tree` 全量 DB 化（仍保留 Mock 作 seed 演示）
- L2/L3 菜单能力差异（BFF seed，属 S1）
- 生产微信/支付宝密钥与 HTTPS 回调（MOD-01 / Owner）
- S2 人类链：手册 PDF · PM L3 六项签字

---

## 四、租户 ↔ 平台支付链路（PM 口径）

| 环节 | 状态 | 说明 |
|------|------|------|
| 租户发起 | ✅ | `/client/billing` → `POST /payment/create-native` 等 |
| 平台收款配置 | ⚠️ | 超管「支付码与接口」；生产密钥在服务器 `.env` |
| 回调 / Mock | ✅ 本地 | 未配置渠道时 Mock 支付 E2E |
| 入账与开通 | ✅ | `provision_after_payment` |
| 分润 | ✅ | 沿 `agent_chain` 计提 |
| 超管订单透视 | 🔄 MOD-09 | 新增财务子页 |

**生产真钱**：需 `WECHAT_PAY_*` / `ALIPAY_*` + 公网 HTTPS notify；与四层贯通 **正交**，不阻塞送检 Mock 演示。

---

## 五、MOD-09 任务卡（蜂群）

| 字段 | 内容 |
|------|------|
| **ID** | MOD-09 |
| **名称** | L1–L4 四层贯通 + 超管租户支付订单 |
| **Lane** | E 后端 + B 前端（边界：不改 Formily / 不新建支付 API） |
| **In-Scope** | `AgentAggregationService` DB 子树；`l4` 租户节点；`AgentPortalService` 范围；Admin 支付订单页；层级页 L4 只读 |
| **Out-of-Scope** | 新支付渠道；L2/L3 菜单 diff；全树去 Mock |
| **验收** | ① 代理开户后超管 hierarchy L4 可见 ② 代理 dashboard `data_source:db` ③ 超管 finance 支付订单列表可筛状态 ④ unit test 绿 |

---

## 六、送检彩排话术（四层段 · 30s）

1. **超管**：「租户在 L4，上级是 L3 市代；开户时自动绑定代理链。」  
2. **付费**：「租户在 Client 账户页付费，平台财务与代理佣金同源台账。」  
3. **声明**：「空库演示数字可能来自 seed；有真实开户后看板切 DB。」

---

## 七、与总表关系

| 文档 | 更新 |
|------|------|
| [`pm-dev-task-progress.json`](./pm-dev-task-progress.json) | 新增 MOD-09 |
| [`ecc-delivery-tracker.md`](./ecc-delivery-tracker.md) | Sprint 追加 MOD-09 |
| [`pm-executive-report-summary-20260601.md`](./pm-executive-report-summary-20260601.md) | §十四 增量索引 |

---

## 八、PM 结论

1. **不是「完全没通」** — 钱、户、角色壳已通；**缺的是超管「一张组织+订单图」**。  
2. **MOD-09 是送检 cert-03 / cert-06 的 P0 补洞**，不与 Vben 迁移绑定。  
3. **验收权**：SaaS 专家 — L4 租户必须在 hierarchy 可见，否则 cert-03 叙事不成立。

---

## 九、MOD-09 交付记录（2026-06-02）

| 项 | 状态 | 路径 |
|----|------|------|
| L4 租户挂树 | ✅ | `AgentAggregationService.get_l4_tenant_nodes` |
| DB 子树范围 | ✅ | `collect_subtree_node_ids` · `AgentPortalService._subtree_node_ids` |
| L2/L3 真实统计 | ✅ | `_enrich_node_stats` |
| 超管支付订单页 | ✅ | `/admin/finance/payment-orders` |
| 层级页 L4 只读 | ✅ | `hierarchy/index.vue` |
| 单测 | ✅ | `test_agent_hierarchy_bridge.py` 4/4 |

**仍保留 Mock**：空库演示 L1–L3 seed；有真实租户后看板/统计优先 DB。

---

*PM 四层贯通总结 v1 · 2026-06-02 · MOD-09 已交付*
