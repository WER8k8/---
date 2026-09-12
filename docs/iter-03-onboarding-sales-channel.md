# ITER-03 · 开户路线图 + 销售通知链

> **签发**：PM-07 · **日期**：2026-06-04  
> **泳道**：产品 + 后端 Lane I + QA + 文档  
> **边界**：不新建支付 API · 租户企微由客户自配

---

## 目标

新户进站后 **不漏环节**：从一键开业到销售收得到企微/抖音消息，系统与文档一致。

---

## 任务分解

| ID | 任务 | 主责 | In-Scope | Out-of-Scope | 验收 |
|----|------|------|----------|--------------|------|
| **ITER-03a** | 开户路线图 UI + 进度刷新 | 前端+后端 | 向导/工作台路线图、`refresh_onboarding_checklist` | 不改支付 | 单测绿 + 向导可见五段 |
| **ITER-03b** | 抖音评论真实拉评 | 后端 Lane I | SAU/AiToEarn → Worker | 个人微信推送 | 1 条真实评论入库 |
| **ITER-03c** | 七步⑤ 5a/5b/5c 彩排 | QA | 截图 3 张 + 签字表 | 不修功能 | `qa-step5-inquiry-im-acceptance.md` |
| **ITER-03d** | 客户/代理手册 | PM+DOC | 5min 企微说明 + 代理一页纸 | 不进 S2 律师链 | 文档路径可访问 |

---

## 接口契约（冻结）

| 能力 | API / 页面 |
|------|------------|
| 开户状态 | `GET /tenants/self/onboarding-status` → `sales_channel_steps`, `onboarding_roadmap`, `checklist` |
| 租户企微 | `GET/PUT /api/v1/client/wecom-push-config` |
| 入站 Webhook | `POST /api/v1/inquiries/channels/{wecom\|douyin}` |
| 评论 Worker | `POST /api/v1/social-interactions/webhook/douyin` |
| 自动谈单 | `/sales/auto-negotiator` |

---

## 依赖

- **Owner O-2/O-3**（`pm-owner-blockers-20260604.md`）未做 → ITER-03c 仅能 staging  
- **MOD-02** 生产联调 = ITER-03b/c 硬依赖  

---

## 进度

| ID | pct | next |
|----|-----|------|
| ITER-03a | 100 | E2E 录屏 |
| ITER-03b | 55 | AiToEarn 生产 Key 实拉 1 条（pull API 已就绪） |
| ITER-03c | 40 | staging 路由探针 PASS；待 QA 3 张截图 |
| ITER-03d | 100 | 代理培训一次 |

---

## 索引

- Owner：[`pm-owner-blockers-20260604.md`](./pm-owner-blockers-20260604.md)  
- QA：[`qa-step5-inquiry-im-acceptance.md`](./qa-step5-inquiry-im-acceptance.md)  
- 客户：[`guides/customer-wecom-push-5min.md`](./guides/customer-wecom-push-5min.md)  
- 代理：[`guides/agent-onboarding-roadmap-onepage.md`](./guides/agent-onboarding-roadmap-onepage.md)  
- R1 关账：[`pm-r1-closeout-checklist.md`](./pm-r1-closeout-checklist.md)  

---

*PM 蜂群 · Lane H 编排 · 不越界写 Lane I 实现*
