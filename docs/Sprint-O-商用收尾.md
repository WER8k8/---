# Sprint O — 商用收尾与统一入口

## 交付

| 任务 | 说明 |
|------|------|
| O-01 | `SSL_PROVIDER=acme|certbot` + `ACME_WEBHOOK_URL` 签发与 `/status/{job_id}` 轮询 |
| O-02 | `InquiriesUnifiedService` — `/inquiries/unified` 与废弃的 `GET /inquiries/` |
| O-03 | `POST /api/v1/payment/addon/egress-ip` — 支付后 `[addon:egress_ip:N]` 增加配额 |
| O-04 | 管理端 `/admin/system/integrations-stack` |
| O-05 | 单元测试 |

## 环境变量（生产 SSL）

```env
SSL_PROVIDER=acme
ACME_WEBHOOK_URL=https://your-certbot-worker.example/issue
```

Webhook 契约：

- `POST {ACME_WEBHOOK_URL}` body: `{ "action":"issue", "domain", "tenant_id" }` → `{ "status","job_id" }`
- `GET {ACME_WEBHOOK_URL}/status/{job_id}` → `{ "status":"active|failed|pending", "expires_at", "error" }`

## IP 加购

```http
POST /api/v1/payment/addon/egress-ip
{ "tenant_id": "...", "slots": 2, "channel": "wechat" }
```

支付成功（含 `mock-pay`）后自动增加 `settings.egress_ip_quota` 并尝试分配槽位。

## 验证

```powershell
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -m pytest tests/unit/test_sprint_o_services.py -q
```
