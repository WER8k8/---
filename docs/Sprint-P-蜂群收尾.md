# Sprint P — 蜂群并行收尾

**模式**：M3 蜂群（S05 前后端 + S03 租户端并行）

## 工作包

| 包 | 路径 | 交付 |
|----|------|------|
| P1 租户端 | `frontend/admin/src/views/client/egress.vue`, `referral.vue` | IP 槽位自助/加购、邀请链接 |
| P2 发布双链 | `content_master` link-preview、 `publish/unified.vue` | 枢纽开关 + 双链预览 |
| P3 询盘统一 | `inquiries/index.vue` | `/inquiries/unified` + 类型列 |
| P4 财务/枢纽 | `admin/finance/index.vue`, `admin/hub/index.vue` | 成本类目、GSC 清单 |

## 验收

```powershell
cd backend
$env:JWT_SECRET_KEY="test-"+("x"*32)
python -m pytest tests/unit/test_sprint_p_swarm.py -q
cd ..
python scripts/check_mounted_routes.py
python scripts/module_progress.py
```

## 仍须 PM

- 5+5 / 40 平台签字、HTTPS 演示域、套餐定价表
