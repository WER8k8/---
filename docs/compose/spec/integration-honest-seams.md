---
feature: integration-honest-seams
status: in-progress
updated: 2026-09-20
branch: feat/integration-honest-seams
commits: 
---

# 外部能力诚实接线（Wave1 · 无外部 Key 可交付）

## Report

## [S1] Problem
主理人盘点出一批「记得没接」的外部能力：OAuth（QQ/微信/飞书/钉钉）、静态 IP 服务商采购、海关数据等。深挖后实况多为：**代码/路由已挂载，生产凭证未配**；同时存在 ① 登录页对未配置 Provider 不够诚实/图标不全 ② OAuth 实现安全债（QQ secret 走 GET 等） ③ referral 有效邀请未接支付闭环 ④ 海关/Egress 未配置时门禁与文案不够统一 ⑤ 没有一份「该申请哪些 Key、填到哪」的运营清单。

## [S2] Design

### Wave 边界
- **Wave1（本特性）**：无外部 Key 也能交付——诚实状态、安全修复、referral 支付钩子、凭证清单。
- **Wave2（后续）**：主理人提供 QQ/微信 AppId、IPRoyal/ASocks Token、Customs Spider URL 后的真接入联调。

### A. 凭证清单（运营真源）
- 文档：`docs/ops/external-integration-keys-checklist.md`
- 每项：能力 → 环境变量名 → 申请入口说明 → 配置位置（backend/.env）→ 未配置时系统诚实行为 → 申请后验收命令。
- 覆盖：OAuth 四端、IPROYAL/ASOCKS、CUSTOMS_DATA_SPIDER、LinkedIn/sidecar、GoodJob/TradeAI 本地桥说明。

### B. OAuth 诚实态 + 安全
- `oauth_providers_status()` 继续返回 bool；**响应增加 `configured` 明细**（无 Key=false），前端文案「暂未开通（缺 QQ_APP_ID 等）」而非含糊。
- QQ token 交换：**client_secret 改为 POST body**，禁止 query 泄露。
- 微信验签：使用 `WECHAT_VERIFICATION_TOKEN`，不再误用飞书 token。
- 登录页：`LoginOAuthRow`/`LoginSocialButtons` 展示全部四端；未配置 muted + 可读原因；**禁止**生产 `OAUTH_DEV_BYPASS`。
- 硬锁：不新建第二登录页；仍唯一 `/login`。

### C. Referral 支付闭环（无 Key 可写）
- 模型/服务：在 `ReferralRecord` 上增加/使用 `status` + `rewarded_at`（若字段已存在则复用）。
- 钩子：支付成功路径（订单 paid / mock-pay / webhook 统一入口）调用 `referral_service.mark_invite_qualified(invited_tenant_id)`：
  - 仅当 invited 租户 **首次** 有效付费；
  - 幂等：已 rewarded 不重复；
  - inviter 累计 `total_referred` / 奖励字段按现有模型更新；
  - 失败写日志，**不阻断支付主流程**。
- API：referral stats 在 payload 标明 `qualification_rule: "first_paid"`；无支付记录的邀请 `pending`。
- 禁止：未付费就记有效、假 leaderboard 灌数。

### D. 海关 / Egress 未配置诚实展示
- Customs sidecar status 已有 `fallback=not_configured`：侧栏/面板文案固定「海关反查未配置（CUSTOMS_DATA_SPIDER_URL）」；禁止展示假买家。
- Trade-intel customs-stats 保留 disclaimer；UI 不把试点统计写成「已接海关实时数据」。
- Egress `/suppliers`：每供应商返回 `has_token` / `ready`（现有 iproyal_config.has_token 模式提升到每个 provider）；激活时若无 token → 明确 error，不静默假采购。
- Egress overview/pool：`upstream_pool=false` 时 UI 可读提示「当前手工录入模式，自动采购未开通」。

### E. 验证
- pytest：oauth QQ token 调用方式（mock httpx）；referral mark_qualified 幂等；egress supplier status 字段。
- live：oauth/providers 明细；referral leaderboard/stats；egress/suppliers has_token；customs sidecar status。
- typecheck：登录组件/egress 相关。

## [S3] Out of Scope
- 真实申请 QQ/微信/IPRoyal/海关账号与联调（Wave2）；
- 发布母版 content_master、财务中台大项；
- LinkedIn 真数据抓取；
- 远端 push/PR。

## Tasks
- [ ] T1: 凭证申请清单文档 — acceptance: docs/ops/external-integration-keys-checklist.md 含 OAuth/IP/海关等变量与验收命令（covers: S2 A）
- [ ] T2: OAuth 安全修复 + providers 明细 — acceptance: QQ secret POST；微信验签 token 正确；providers 响应含未配置原因字段；pytest 绿（covers: S2 B）
- [ ] T3: 登录页四端诚实 UI — acceptance: 四 Provider 可见；无 Key muted；无第二登录页（covers: S2 B; depends: T2）
- [ ] T4: Referral 首付费资格钩子 — acceptance: 支付成功路径可标记有效邀请且幂等；pending/rewarded 可区分（covers: S2 C）
- [ ] T5: 海关/Egress 诚实字段与文案 — acceptance: sidecar not_configured 文案；suppliers has_token/ready；live 探针（covers: S2 D）
- [ ] T6: Verify + Review + Finalize — acceptance: pytest/typecheck/live；review 无 critical；spec delivered（covers: S2; depends: T1–T5）
