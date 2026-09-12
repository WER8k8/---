# QA-04 · Locust 72h 长跑排期（CERT 前置）

> **冒烟**：`scripts/qa-locust-smoke-with-backend.ps1` → `docs/qa-locust/locust-smoke-latest.json`  
> **正式 72h 脚本**（Owner 提供 HTTPS 域后）：

```powershell
$env:LOCUST_HOST = "https://demo.youding.com"
powershell -File scripts/qa-locust-72h-production.ps1
```

> **2min 干跑**（本机 CI）：`scripts/qa-locust-72h-dryrun.ps1`

| 项 | 值 |
|----|-----|
| 计划窗口 | CERT 前置 6/10 – 6/16 |
| 前置 | ARCH-01 PASS · HTTPS 域（ARCH-04/MOD-01） |
| 归档 | `docs/qa-locust/run-72h_*.csv` + `locust-72h-latest.json` |

**说明**：72h 不在本机默认执行；Owner 提供 HTTPS 演示域后排期。
