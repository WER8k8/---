# Sprint L · 生产化与架构债

> **目标**：SMTP 真实发码、租户站 API 基址环境化、询盘 API 导航聚合。

## 交付

| ID | 内容 |
|----|------|
| L-01 | `EmailService.send_verification_code` + `send-email-code` 对接 SMTP |
| L-02 | Nuxt `useApiV1` composable；用户中心/物流页去除硬编码 localhost |
| L-03 | `GET /inquiries/portal` 询盘 API 导航与统计 |
| L-04 | 生产环境未配置 SMTP 时发码返回 503 |
| L-05 | 测试 + 路由门禁 |

## 环境变量

### 后端（`backend/.env`）

```env
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=***
FROM_EMAIL=noreply@example.com
```

### 租户站（`frontend/.env`）

```env
API_HOST=https://api.youding.com
API_BASE=/api/v1
```

部署时务必设置 `API_HOST`，勿依赖默认 `localhost:8000`。

## 询盘接入建议

管理端统一调用：

- `GET /api/v1/inquiries/portal` — 看统计与路径说明  
- `GET /api/v1/inquiries/unified` — 列表分页  

## 说明

- Host 解析：`GET /api/v1/domains/resolve` + Nuxt `server/api/tenant-resolve.get.ts` 已存在。  
- 独立域 SSL 生产化见 Sprint H/I 文档与 `SSL_PROVIDER` / `ACME_WEBHOOK_URL`。
