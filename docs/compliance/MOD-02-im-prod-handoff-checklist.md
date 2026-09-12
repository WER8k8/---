# MOD-02 · 询盘 IM 生产交接清单（七步⑤ · 含 5a/5b/5c）

> **代码**：`inquiry_channels.py` · `social_interactions.py` · `tenant_wecom_config_service.py`  
> **验证**：`scripts/validate-mod-02-im-keys.py`  
> **QA 彩排**：[`qa-step5-inquiry-im-acceptance.md`](../qa-step5-inquiry-im-acceptance.md)  
> **Owner 阻塞**：[`pm-owner-blockers-20260604.md`](../pm-owner-blockers-20260604.md)

---

## A · 平台运维（服务器 `.env`）

| # | 变量 / 动作 | 说明 | 状态 |
|---|-------------|------|------|
| A1 | `INQUIRY_WEBHOOK_SECRET` | 企微/抖音 **入站**验签 Header: `X-Inquiry-Webhook-Secret` | ☐ |
| A2 | `SOCIAL_INTERACTION_WEBHOOK_SECRET` | 抖音评论 Worker 验签（可与 A1 相同） | ☐ |
| A3 | `PUBLIC_API_BASE` | 对外 API 根，如 `https://api.xxx.com` | ☐ |
| A4 | `alembic upgrade head` | 含 044–046 迁移 | ☐ |
| A5 | Webhook URL 入站 | `POST {BASE}/api/v1/inquiries/channels/wecom` | ☐ 平台配置 |
| A6 | Webhook URL 入站 | `POST {BASE}/api/v1/inquiries/channels/douyin` | ☐ 平台配置 |
| A7 | Webhook URL 评论 | `POST {BASE}/api/v1/social-interactions/webhook/douyin` | ☐ Worker 配置 |

**模板**：`deploy/production/env.template`（勿在开发目录填真实值）

---

## B · 5a 客户能联系到你（租户 + 运维）

| # | 动作 | 通过标准 | 状态 |
|---|------|----------|------|
| B1 | 租户完成开通向导「留联系方式」或配置 IM 全渠道 | 开户清单 `inquiry_im` → done | ☐ |
| B2 | 1 条入站测试 → 询盘列表 | `source_channel` 含 wecom/douyin | ☐ |

---

## C · 5b 销售收得到通知（租户自配 · 非平台 UserID）

| # | 动作 | 通过标准 | 状态 |
|---|------|----------|------|
| C1 | 租户 `PUT /client/wecom-push-config` | `app_ready` 或 `webhook_ready` | ☐ |
| C2 | 新询盘/社媒互动触发推送 | `push_events.status=sent` | ☐ |
| C3 | 销售企微收到消息 | 截图归档 | ☐ |

**客户手册**：[`guides/customer-wecom-push-5min.md`](../guides/customer-wecom-push-5min.md)

**禁止验收项**：生产环境用 `WECOM_PUSH_TO_USERIDS` 代替租户配置

---

## D · 5c 抖音评论自动抓

| # | 动作 | 通过标准 | 状态 |
|---|------|----------|------|
| D1 | 租户绑定抖音 `logged_in` | 内容分发可见 | ☐ |
| D2 | Worker 投递 1 条评论 | `social_interactions` 有记录 | ☐ |
| D3 | 自动谈单页可见 | `/sales/auto-negotiator` 列表有项 | ☐ |

---

## E · 自动化

| 项 | 命令 |
|----|------|
| 入站 webhook 单测 | `pytest backend/tests/unit/test_inquiry_channel_webhooks.py` |
| 社媒/推送单测 | `pytest backend/tests/unit/test_social_interaction_service.py backend/tests/unit/test_sales_push_service.py` |
| MOD-02 validate | `python scripts/validate-mod-02-im-keys.py` |

---

## 签字

| 角色 | 日期 | ☐ |
|------|------|---|
| 后端 Lane I | | |
| QA | | |
| PM-07 | | |
