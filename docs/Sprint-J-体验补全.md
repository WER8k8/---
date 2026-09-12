# Sprint J · 体验补全与运维告警

> **目标**：补齐登录体验（邮箱验证码）、OAuth 账号绑定、生产就绪飞书告警。

## 交付

| ID | 内容 |
|----|------|
| J-01 | 登录页「密码 / 邮箱验证码」切换 + `emailAuth.ts` |
| J-02 | `GET/POST/DELETE /auth/oauth/bindings` + 系统管理 → 账号绑定 |
| J-03 | `POST /ops/alerts/readiness-notify` → 飞书 Webhook |
| J-04 | 开发环境 `send-email-code` 返回 `dev_code` |
| J-05 | 单元测试 + 路由门禁 |

## 使用说明

### 邮箱验证码登录

1. 登录页选择 **邮箱验证码**
2. 输入邮箱 → 获取验证码（开发环境界面会显示 `dev_code`）
3. 完成滑块验证 → 登录

### OAuth 绑定

路径：**超级管理员 → 系统管理 → 账号绑定**（`/admin/system/account-bindings`）

1. 已登录状态下点击「绑定」
2. 完成第三方授权后回调自动写入绑定
3. 之后可在登录页用该第三方方式登录

### 就绪告警 Cron

```bash
# 需超管 Token；未就绪时推送到 FEISHU_WEBHOOK_URL 或 OPS_READINESS_WEBHOOK_URL
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/ops/alerts/readiness-notify
```

## 环境变量

```env
OPS_READINESS_WEBHOOK_URL=   # 可选，默认 FEISHU_WEBHOOK_URL
```

## 说明

- **呼朋唤友首单奖励**：已在 `ProvisioningService._apply_referral_rewards` 于支付成功时发放 Token，本 Sprint 未重复实现。
