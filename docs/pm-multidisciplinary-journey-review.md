# 八角色联合旅程审查 · 盲区补齐

> **任务**：PM-MKT-02（在 PM-MKT-01 矩阵之上）  
> **角色**：产品经理 · 营销 · 策略 · 市场调研 · 用户研究 · 数据分析 · UX 研究 · UI 设计  
> **配套**：[`pm-marketing-journey-review-matrix.md`](./pm-marketing-journey-review-matrix.md) · [`iter-03-onboarding-sales-channel.md`](./iter-03-onboarding-sales-channel.md)

---

## 1. 审查结论（2026-06-04）

| 维度 | 结论 | 证据 |
|------|------|------|
| 主链可跑通 | 开发环境 5a/5b/5c 可彩排 | `sales_channel_rehearsal_service` · IM 页一键测试 |
| 用户可读性 | 工作台/落地页去工程词 | `dashboard.vue` · `landing/index.vue` |
| 数据诚实 | 蓝海/漏斗有免责 | `journey_health_service` · 漏斗脚注 |
| 缺口可见 | 开户进度 + 八角色建议 API | `GET /client/journey-health` |
| 仍待 Owner | HTTPS 演示域 · 生产密钥 · 库迁移 | `pm-owner-blockers-20260604.md` |

---

## 2. 八角色盲区矩阵（发现 → 修复）

| 角色 | 容易想不到的盲区 | 系统应对 | 交付/文件 |
|------|------------------|----------|-----------|
| **产品经理** | BFF 返回 `onboarding_steps` 时工作台跳过路线图/漏斗/HTTPS | 去掉早退；并行拉 guides + journey-health | `dashboard.vue` |
| **产品经理** | 5a 做了但 5b/5c 未做仍显示「开户完成」 | 主链 6 项计分；销售子步单独 `sales_channel_gaps` | `journey_health_service.py` |
| **营销** | 对外承诺「自动接单」但销售手机未配企微 | `role_insights.marketing` 限制话术 | 旅程健康 API + 代理一页纸 |
| **策略** | 未首发就加大投放，蓝海当实时海关 | 策略 insight + `trade_intel_disclaimer` | `client_today_service` 蓝海后置 |
| **市场调研** | 蓝海数据被当成海关实时同源 | 矩阵脚注 + `data_notes` | 工作台漏斗免责 |
| **用户研究** | 老板以为「留电话=销售收到」 | 5b 在向导与 IM 页重复提示 | `im-routing.vue` · 开通向导 |
| **数据分析** | 只看访问量不看「询盘→带号→发布」 | 漏斗 5 段 + 完成度 `done/total` | `dashboard.vue` 卖货漏斗 |
| **UX 研究** | 30 秒内不知道「今天干什么」 | 询盘优先；无询盘则推销售缺口 | `client_today_service.py` |
| **UI 设计** | inbox / Webhook / plan-copy-deck 吓退客户 | 统一「询盘」「销售通知」「拉评论」 | `landing` · `im-routing` · `dashboard` |

---

## 3. 按旅程段 · 八角色打分项（会议用）

### A. 获客第一印象

| ID | 环节 | PM | 营销 | 策略 | 市调 | 用研 | 数据 | UX | UI |
|----|------|:--:|:----:|:----:|:----:|:----:|:----:|:--:|:--:|
| A-01 | `/landing` | 七步一致 | 3 秒懂卖点 | 不夸大 40 平台 | — | 注册动机清晰 | — | CTA 一条主路 | 无工程词 |
| A-02 | 注册 | 跳向导 | 表单项大白话 | — | — | 错误可恢复 | — | 步骤≤3 屏 | 字号/对比度 |

### B. 开户五段（ITER-03）

| ID | 环节 | PM | 营销 | 策略 | 市调 | 用研 | 数据 | UX | UI |
|----|------|:--:|:----:|:----:|:----:|:----:|:----:|:--:|:--:|
| B-06 | 5a 入站 | Webhook 可测 | ≠ 销售收到 | — | — | 认知对齐 | 入站可计数 | 一键测试 | 不叫 Webhook |
| B-07 | 5b 企微 | 租户自配 | 5 分钟手册对齐 | — | — | UserID 谁填 | 推送成功率 | 保存即反馈 | 表单分组清晰 |
| B-08 | 5c 抖音 | Worker 状态真 | 不夸大自动成交 | 评论=线索非订单 | — | 评论场景 | 拉取条数 | 链到列表 | 状态色一致 |
| B-09 | 工作台 | 路线图+健康度 | 店长日报语气 | 蓝海后置 | 免责可见 | 今日一件事 | 漏斗 5 段 | 30 秒可决策 | 主按钮 3 个 |

### C. 数据与合规（横切）

| 检查项 | 负责角色 | 通过标准 |
|--------|----------|----------|
| 蓝海免责 | 市调 + 数据 | 页面可见 `DISCLAIMER` 摘要 |
| 漏斗来源 | 数据 + UX | 标注「账户真实记录」 |
| 工程词扫描 | UI + 营销 | 租户可见页无 inbox/Webhook 作主标题 |
| 主链计分 | PM + 数据 | `critical_done/critical_total` 与清单一致 |

---

## 4. 代码/API 契约（审查冻结）

```
GET  /api/v1/client/journey-health
GET  /api/v1/client/onboarding-guides  → journey_health, role_insights
GET  /api/v1/client/dashboard          → today_* 含 journey_health 摘要
POST /api/v1/client/sales-channel-rehearsal/inbound|wecom-push
POST /api/v1/client/douyin-comments/pull
```

`role_insights[].role` 枚举：`pm` · `marketing` · `strategy` · `market_research` · `user_research` · `data_analytics` · `ux_research` · `ui_design`

---

## 5. 仍开放项（非本批代码范围）

| ID | 项 | Owner | 说明 |
|----|-----|-------|------|
| O-1 | HTTPS 演示域 | Owner | 工作台绿锁演示 |
| O-2 | 生产 Webhook 密钥 | Owner | 5a 验签 |
| O-3 | 迁移 044–046 | Owner/后端 | 生产库 |
| QA-5 | Step5 三张截图 | QA | staging 实机 |
| PM-MKT-01 | 会议 signoff | PM+营销 | 填 `pm-marketing-journey-review-signoff.json` |

---

## 6. 验收命令

```powershell
python scripts/validate-pm-multidisciplinary-review.py
python scripts/validate-iter-03-handoff.py
cd backend
python -m pytest tests/unit/test_journey_health.py tests/unit/test_onboarding_progress.py -q
```
