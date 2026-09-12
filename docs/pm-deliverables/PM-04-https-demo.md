# HTTPS 演示域（PM-04）

- 开发：`SSL_PROVIDER=dev_local` 自动签发 `.test.local`
- 生产：配置 `SSL_PROVIDER=http` + `ACME_WEBHOOK_URL` 或 Cloudflare
- 验收：`GET /api/v1/ssl-certificates`
