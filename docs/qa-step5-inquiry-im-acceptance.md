# QA 验收 · 七步⑤ 询盘 IM（含 5a / 5b / 5c）

> **任务 ID**：MOD-02 · MOD-04 · QA-04 彩排附件  
> **签发**：PM-07 · **日期**：2026-06-04  
> **环境**：staging 或 Owner 已配 HTTPS 演示域 + 生产密钥

---

## 总原则

- **5a**：客户留言能进系统  
- **5b**：销售在企业微信能收到（租户自配，不是平台代填）  
- **5c**：抖音评论能进自动谈单  
- 三张截图缺一不可，归档路径：`docs/mod-04-rehearsal/step5/`

---

## 5a · 客户能联系到你（入站）

| # | 步骤 | 通过标准 |
|---|------|----------|
| 1 | 登录租户后台 → **询盘管理 → IM 全渠道** | 页面打开，有「国内渠道 Webhook」卡片 |
| 2 | 复制企微或抖音 Webhook 地址 | `GET /api/v1/inquiries/channels/config` 有 `channels[].url` |
| 3 | 用 curl 或平台配置发 1 条测试私信 | `POST .../inquiries/channels/wecom` 或 `/douyin`，带 `X-Inquiry-Webhook-Secret` |
| 4 | 打开 **询盘管理** 列表 | 新增 1 条，`source_channel` 含 `wecom` 或 `douyin` |

**截图 A**：IM 全渠道 Webhook 卡片 + 测试询盘列表各 1 张

**自动化辅助**：

```powershell
backend\.venv\Scripts\python.exe scripts\validate-mod-02-im-keys.py
```

---

## 5b · 销售手机能收到通知（出站）

| # | 步骤 | 通过标准 |
|---|------|----------|
| 1 | 同一租户 → IM 全渠道 → **企微销售推送** | 填写测试企微 CorpID、AgentId、Secret、销售 UserID（测试号） |
| 2 | 保存 `PUT /api/v1/client/wecom-push-config` | 返回 `app_ready: true` 或 `webhook_ready: true` |
| 3 | 触发推送：新询盘或新社媒互动 | `push_events` 表 `status=sent` 且有 `upstream_msgid`（或 webhook 200） |
| 4 | 销售企微客户端 | 收到卡片/文本通知 |

**截图 B**：企微推送配置已保存 + 销售企微收到通知

**客户手册**：[`guides/customer-wecom-push-5min.md`](./guides/customer-wecom-push-5min.md)

**禁止**：用平台 `.env` 的 `WECOM_PUSH_TO_USERIDS` 作为生产验收依据

---

## 5c · 抖音评论自动抓

| # | 步骤 | 通过标准 |
|---|------|----------|
| 1 | 租户已绑定抖音平台账号（`login_status=logged_in`） | 内容分发中心可见已登录 |
| 2 | 查看 Worker 手册 `GET /api/v1/social-interactions/worker/config` | 返回 `webhook_url`、`secret_configured: true` |
| 3 | 投递 1 条测试评论（脚本或 ops） | `POST /api/v1/social-interactions/webhook/douyin` |
| 4 | 打开 **销售中心 → 自动谈单** | 列表可见该评论，`status` 为 `draft_ready` 或之后状态 |

**截图 C**：自动谈单列表 + Worker config 页（密钥打码）

**脚本参考**：

```powershell
backend\.venv\Scripts\python.exe scripts\run-douyin-comment-worker.py --batch-file path\to\comments.json
```

或 ops：`POST /api/v1/ops/jobs/douyin-comment-sync`

---

## 开户引导联动（ITER-03a）

| # | 检查 | 通过标准 |
|---|------|----------|
| 1 | `/client/onboarding` 完成页 | 显示「开户后完整路线」5 段 |
| 2 | `/client/dashboard` | 未完成时显示「开户还要做的事」 |
| 3 | `GET /tenants/self/onboarding-status` | 含 `sales_channel_steps`、`onboarding_roadmap` |
| 4 | 清单项 `wecom_push` | 保存企微配置后变 `done` |

---

## 签字

| 角色 | 日期 | 结果 |
|------|------|------|
| QA | | ☐ pass ☐ fail |
| PM-07 | | ☐ 归档 |

**fail 时**：开单指派 Lane I（后端）或 Lane B（前端），QA 不修功能。
