# Sprint Q — 蜂群并行收尾（第二轮）

| 包 | 交付 |
|----|------|
| Q1 运维 | `POST /ops/jobs/run-all`、`/ops/publish-worker/run`、管理端运维批处理页 |
| Q2 支付 | `PAYMENT_STRICT_VERIFY` + `PAYMENT_WEBHOOK_SECRET` HMAC 验签 |
| Q3 财务 | `GET /finance/reconciliation-template.csv`、财务页「对账模板」 |
| Q4 枢纽 | Nuxt `useApiRoot` 统一 SSR/浏览器 API 基址 |
| Q5 文档 | `docs/运维-cron.md` |

验收：

```powershell
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -m pytest tests/unit/test_sprint_q_swarm.py tests/unit/test_order_tracking_patch.py -q
cd ..
python scripts/check_mounted_routes.py
```
