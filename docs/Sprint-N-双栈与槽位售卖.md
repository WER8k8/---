# Sprint N — 双栈集成与 IP 槽位售卖

## 目标

- 运维/超管可查看 **FastAPI 主栈** 与可选 **seo-backend (Node)** 的集成健康
- 套餐绑定 **IP 出口槽位配额**，支付成功后自动从池分配
- 租户管理员可查看已分配槽位并 **自助申领**（在配额内）

## 交付

| 任务 | 说明 |
|------|------|
| N-01 | `GET /api/v1/integrations/status` |
| N-02 | `egress_quota_service` — `PLAN_EGRESS_QUOTA` + `settings.egress_ip_quota` |
| N-03 | `GET /api/v1/egress/my`、`POST /api/v1/egress/request-slot` |
| N-04 | `ProvisioningService.provision_after_payment` → `egress_slots_assigned` |
| N-05 | 单元测试 + `docs/ADR-seo-dual-stack.md` |

## 套餐默认配额

| plan.code | 槽位数 |
|-----------|--------|
| free | 0 |
| basic / pilot | 1 |
| pro | 2 |
| enterprise | 5 |
| flagship | 10 |

可在租户 `settings` JSON 中设置 `egress_ip_quota` 覆盖。

## 验证

```powershell
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -m pytest tests/unit/test_sprint_n_services.py -q
cd ..
python scripts/check_mounted_routes.py
python scripts/dev_progress.py
```

## 后续（Sprint O 建议）

- 管理端「集成栈」只读页
- 租户侧购买加购 IP 包（支付 SKU → 增加 `egress_ip_quota`）
- 生产 ACME SSL（`ssl_certificate_service`）
