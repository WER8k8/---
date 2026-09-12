# 开发信可达性 — 研究员 × PM 短板补齐（2026-06-02）

## 背景

对标迈富时 Eva：开发信不能「糊写」、要降低进垃圾箱概率、按买家时区安排发送。

## 现状 vs 目标

| 维度 | 改造前 | 目标（本迭代） |
|------|--------|----------------|
| 正文 | 区域模板 + 列表堆砌 | 结构化钩子 + 规格点 + 低压力 CTA |
| 主题 | 【品类】促销感 | 专业主题 ≤72 字，无全大写 |
| 垃圾箱 | 无检测 | `scan_spam_risks` + 质量分 |
| 发送时间 | 无 | `suggest_send_window` 按国家时区 |
| 跟进 | 无 | 建议 D+3 / D+7 |
| 真发 | 人工复制 | 仍人工；清单约束 SPF/DKIM/预热 |

## 研究员负责（数据与规则）

1. 维护 `_COUNTRY_TZ` 与中东/欧美发送窗口惯例（Tue–Thu 上午优先）。
2. 扩充 `_SPAM_TRIGGERS`：从真实退信/进箱案例迭代（季度 review）。
3. 按品类维护「必提规格字段」（岩棉/玻璃棉/保温）— 已在 `accio_sales_service`。
4. 对外表述：仍为**草稿 + 人审**，不承诺送达率。

## PM 负责（产品与验收）

1. **验收 ID OUTREACH-D1**：`outreach_letter_pack` 返回 `deliverability` 每封信 + `pack_summary`。
2. **OUTREACH-D2**：质量分 &lt; 70 或 spam 风险 &gt; 1 → 前端标黄「需修改后再发」。
3. **OUTREACH-D3**（P1）：待发队列 + 到点提醒（不接 SMTP 也可日历导出）。
4. **OUTREACH-D4**（P2）：接 SendGrid/腾讯企业邮 + 打开/退信 webhook。

## Out of Scope（本迭代）

- 购买 RocketReach 等联系人库
- 全自动无人工外发
- HTML 多 part 邮件渲染（仅 plain 结构建议）

## 索引与变更

| 文件 | 用途 |
|------|------|
| 本文 | 开发信 P0 专项 |
| [`global-overseas-growth-agent-backlog.md`](./global-overseas-growth-agent-backlog.md) | **全量出海智能体头脑风暴与 GW 任务** |
| [`global-overseas-growth-task-register.json`](./global-overseas-growth-task-register.json) | 可机读 GW 任务登记 |
| `backend/app/data/b2b_trade_experts.json` | B2B 外贸 AI 专家角色库 |
| `backend/app/services/ubrain/outreach_deliverability_service.py` | 开发信门禁实现 |
