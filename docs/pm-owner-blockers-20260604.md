# Owner 待办表 · MOD-08 阻塞项

> **签发**：PM-07 · **日期**：2026-06-04  
> **用途**：Owner 逐项签字后，ARCH-04 / QA-04 / MOD-02 / MOD-04 可关账  
> **原则**：真实密钥与域名 **只放生产服务器 `.env`**，禁止写入 git

---

## 汇总

| # | 事项 | 阻塞谁 | 目标日 | 状态 |
|---|------|--------|--------|------|
| O-1 | HTTPS 演示独立域 + 真证书 | ARCH-04、QA-04 72h、MOD-04 录屏 | 6/10 | ☐ |
| O-2 | 生产 Webhook 密钥 | MOD-02 七步⑤ 实机联调 | 6/12 | ☐ |
| O-3 | 生产库迁移 044–046 | 社媒谈单 + 租户企微推送 | 6/12 | ☐ |

---

## O-1 · HTTPS 演示域

| 项 | 说明 | 验收 |
|----|------|------|
| 域名 | 1 个可公网访问的演示独立域（如 `demo.xxx.com`） | 浏览器打开显示绿锁 |
| DNS | A/AAAA 指到 staging 或生产入口 | `dig` 解析正确 |
| 证书 | Certbot 或云厂商 SSL | `GET /api/v1/domains/pilot/demo-https` → `ready_for_pilot: true` |
| 记录 | 运维在工单备注域名与到期日 | PM 截图归档 `docs/mod-04-rehearsal/` |

**谁验**：架构 ARCH-04 收尾 · QA 据此跑 Locust 72h

---

## O-2 · 生产 Webhook 密钥

| 变量 | 用途 | 填在哪 |
|------|------|--------|
| `INQUIRY_WEBHOOK_SECRET` | 企微/抖音 **入站**私信验签 | 生产 `backend/.env` |
| `SOCIAL_INTERACTION_WEBHOOK_SECRET` | 抖音评论 Worker 入库验签 | 同上（可与上行共用或单独） |
| `PUBLIC_API_BASE` | Worker 回调完整 URL | 如 `https://api.xxx.com` |

**不填平台 `.env` 的项（客户自配）**：

- 租户企微 CorpID / Agent / 销售 UserID → 客户在 **IM 全渠道 → 企微销售推送** 填写  
- `WECOM_PUSH_TO_USERIDS` 仅开发兜底，**生产不作为验收依据**

**验收**：各 1 条测试数据入库（询盘 1 条 + `social_interactions` 1 条）

详见：[`compliance/MOD-02-im-prod-handoff-checklist.md`](./compliance/MOD-02-im-prod-handoff-checklist.md)

---

## O-3 · 生产库迁移

```bash
cd backend
alembic upgrade head
```

| 迁移 | 内容 |
|------|------|
| 044 | `social_interactions` 社媒互动 |
| 045 | `push_events` 推送记录 |
| 046 | `tenant_wecom_push_configs` 租户企微配置 |

**验收**：生产库存在上表 · 租户保存企微配置不 500

---

## Owner 签字

| 角色 | 姓名 | 日期 | 签字 |
|------|------|------|------|
| Owner | | | ☐ |
| 运维 | | | ☐ |
| PM 确认归档 | PM-07 | | ☐ |

---

*关账后更新 `module-progress.json` · `loop-inquiry` → 10/10*
