# 租户开户一站式开通

## 业务目标

开户时完成：

1. **邮箱验证码**（与 `/auth/send-email-code` 共用）
2. **大模型场景**（文章 / 视频脚本 / 渲染等，按套餐）
3. **云存储路径**（酷播 + R2 + MinIO 前缀预留）
4. **各平台发布账号槽位**（SEO 矩阵里待绑定 OAuth）
5. **海外 Egress IP**（按套餐自动分配）
6. **多媒体工厂**（访客视频、官网引流）

客户不必事后再逐项「申请开通」。

## API

| 接口 | 说明 |
|------|------|
| `POST /auth/send-email-code` | 发验证码 `{ "email": "..." }` |
| `GET /tenants/register/catalog` | 注册页：平台列表 + 打包说明 |
| `POST /tenants/register` | 必填 `email_code`；可选 `platform_names`、`guest_token` |

## 注册请求示例

```json
{
  "company_name": "示例建材",
  "admin_name": "张三",
  "email": "admin@example.com",
  "password": "******",
  "email_code": "123456",
  "contact_phone": "13800000000",
  "plan_code": "pro",
  "platform_names": ["微信公众号", "抖音", "YouTube"],
  "guest_token": "可选-访客视频绑定"
}
```

## 响应

除 `access_token` 外含 `onboarding`：

- `checklist`：已完成 / 待办项
- `platforms`：预置平台与 `pending_connect` 状态
- `storage`：R2/酷播/MinIO 路径说明
- `ai`：已开通场景列表

## 客户后续只需

1. 在 **开通向导** 查看「云存储 & 第三方账号」清单（`/client/onboarding#external-accounts`）
2. **产品图**：直接用「产品图片空间」，无需自开七牛/R2（平台代注册）
3. **发长视频**：自行注册 [酷播云](https://www.cuplayer.com/cloud/) 实名 → 设置里填 API 密钥
4. 在 **SEO 矩阵 / 多平台分发** 绑定抖音、微信、YouTube 等（需先在对应官网注册）
5. 按引导发布视频 / 内容

## 第三方账号分工

| 类型 | 负责方 | 示例 |
|------|--------|------|
| 产品图片（国内） | **平台** | 七牛云 — 运维注册实名，填 `QINIU_*` |
| 产品图片（海外） | **平台** | Cloudflare R2 — 填 `MEDIA_R2_*` |
| 视频点播 | **客户** | 酷播云注册 + 实名 + writetoken |
| 社媒发布 | **客户** | 抖音 / 微信 / YouTube 等 |
| 销售通知 | **客户** | 企业微信 |

API：`GET /tenants/self/external-accounts` · 注册页：`GET /tenants/register/catalog` → `external_accounts_preview`
