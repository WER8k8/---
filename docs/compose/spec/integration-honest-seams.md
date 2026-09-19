---
feature: integration-honest-seams
status: delivered
updated: 2026-09-20
branch: feat/integration-honest-seams
commits: 2361a079..046e6dea
---

# 外部能力诚实接线（Wave1 · 无外部 Key 可交付）

## Report

**What was built** — 对「OAuth / 静态 IP 采购 / 海关」等未接能力做 **Wave1 诚实收口**（不依赖外部账号）：① 运营真源 `docs/ops/external-integration-keys-checklist.md`（QQ/微信/飞书/钉钉、IPRoyal/ASocks、Customs Spider 等变量与验收命令）。② OAuth：`/auth/oauth/providers` 返回 `detail`（configured/missing_env/hint）；登录页四端可见、未配置如实「暂未开通+缺哪些变量」；QQ token **POST body** 不再把 client_secret 放 query；生产禁用 dev authorize（`_oauth_dev_mode_enabled`）；微信验签用 `WECHAT_VERIFICATION_TOKEN`。③ 呼朋唤友：`mark_invite_qualified` 首付费幂等；支付成功事件（含 **mock-pay**、**余额支付**、渠道 webhook）挂钩；stats 含 `qualification_rule=first_paid`；榜单标注 `metric=registration_invites` + `rewarded_count`。④ Egress：`/egress/suppliers` 每供应商 `has_token/ready/not_ready_reason`，顶层 `auto_purchase_ready`/`mode_hint`；非 manual 无 Token 不可 activate。

**Verification** — pytest `test_integration_honest_seams.py` **5 passed**（QQ POST、referral 幂等+qualification_rule、egress 字段、providers detail）；admin typecheck **PASS**；live：oauth detail 全 false+missing_env；egress `auto_purchase_ready=false` + 手工模式 mode_hint；LOGIN-LOCK 脚本 PASS。首轮 Review partial 的 critical（mock-pay/余额钩子、qualification_rule、弱测试）已修并复测。

**Journey log** — ① 「没接」多半是 **Key 未配**，代码/路由已挂；Wave1 做诚实态+闭环钩子，Wave2 填 Key 真联调。② 支付成功事件不是单一咽喉：必须在 mock-pay / 余额支付 / webhook 各路径挂齐，否则 referral 静默漏记。③ `total_referred` 是**注册邀请**，不能当付费有效；有效看 `rewarded`/`first_paid`。④ Egress `has_token` 须与 `_supplier_ready`（settings∪行内 config）同源。⑤ 树内 hermes/moss 脏文件勿混入本特性提交。

## [S1] Problem
主理人盘点出一批「记得没接」的外部能力：OAuth（QQ/微信/飞书/钉钉）、静态 IP 服务商采购、海关数据等。深挖后实况多为：**代码/路由已挂载，生产凭证未配**；同时存在 ① 登录页对未配置 Provider 不够诚实/图标不全 ② OAuth 实现安全债（QQ secret 走 GET 等） ③ referral 有效邀请未接支付闭环 ④ 海关/Egress 未配置时门禁与文案不够统一 ⑤ 没有一份「该申请哪些 Key、填到哪」的运营清单。

## [S2] Design

### Wave 边界
- **Wave1（本特性）**：无外部 Key 也能交付——诚实状态、安全修复、referral 支付钩子、凭证清单。
- **Wave2（后续）**：主理人提供 QQ/微信 AppId、IPRoyal/ASocks Token、Customs Spider URL 后的真接入联调。

### A. 凭证清单（运营真源）
- 文档：`docs/ops/external-integration-keys-checklist.md`
- 每项：能力 → 环境变量名 → 申请入口说明 → 配置位置（backend/.env）→ 未配置时系统诚实行为 → 申请后验收命令。

### B. OAuth 诚实态 + 安全
- providers 响应含 `detail`（configured/missing_env/hint）。
- QQ token：POST body；生产 `_oauth_dev_mode_enabled` 禁用 dev authorize。
- 登录页：四端 muted+缺变量提示；唯一 `/login`。

### C. Referral 支付闭环
- `mark_invite_qualified`：pending→rewarded，幂等，不阻断支付。
- 挂钩：渠道 webhook、**mock-pay**、**余额支付** `_mark_paid_and_provision` 成功后。
- stats：`qualification_rule=first_paid`；榜单 `metric=registration_invites` + `rewarded_count`。

### D. 海关 / Egress 诚实展示
- sidecar `not_configured` 既有行为；checklist 文档化。
- suppliers：`has_token/ready` 与 `_supplier_ready` 同源；`mode_hint`/`auto_purchase_ready`；无 Token 禁止 activate 自动采购。

### E. 验证
- pytest：QQ POST、referral 幂等、egress 字段、providers detail。
- live：providers detail、egress mode_hint、sidecars status。

## [S3] Out of Scope
- 真实申请 QQ/微信/IPRoyal/海关账号与联调（Wave2）；
- 发布母版 content_master、财务中台大项；
- LinkedIn 真数据抓取；
- 远端 push/PR。

## Tasks
- [x] T1: 凭证申请清单文档 — acceptance: checklist 含 OAuth/IP/海关等变量与验收命令（covers: S2 A）
- [x] T2: OAuth 安全修复 + providers 明细 — acceptance: QQ secret POST；detail 字段；pytest 绿（covers: S2 B）
- [x] T3: 登录页四端诚实 UI — acceptance: 四 Provider 可见；无 Key muted；无第二登录页（covers: S2 B; depends: T2）
- [x] T4: Referral 首付费资格钩子 — acceptance: mock-pay/余额/webhook 可标记且幂等；qualification_rule 在 stats（covers: S2 C）
- [x] T5: 海关/Egress 诚实字段与文案 — acceptance: suppliers has_token/mode_hint；activate 无 Token 拒绝（covers: S2 D）
- [x] T6: Verify + Finalize — acceptance: pytest 5 passed + typecheck + live；critical 已修；spec delivered（covers: S2; depends: T1–T5）
