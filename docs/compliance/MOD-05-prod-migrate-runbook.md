# MOD-05 · 生产库 alembic 025/026 执行 Runbook

> **staging 已验证**：`run-mod-05-staging-migrate.ps1` PASS  
> **生产**：运维在维护窗口执行

## 前置

- [ ] 生产 `DATABASE_URL` 已备份（快照/ pg_dump）
- [ ] staging 与生产 revision 差异已核对：`alembic current` / `alembic history`
- [ ] 025/026 文件：`025_ubrain_accio_sales.py` · `026_ubrain_commercial_os.py`

## 命令

```bash
cd backend
export DATABASE_URL='postgresql://...production...'
python -m alembic upgrade 026_ubrain_commercial_os
python -m alembic current
```

## 验收表

| 表 | 存在 |
|----|------|
| ubrain_tenant_memory | ☐ |
| buyer_prospect_leads | ☐ |
| ubrain_research_insights | ☐ |
| ubrain_pipeline_runs | ☐ |
| ubrain_feedback_snapshots | ☐ |

**校验脚本（staging）**：`validate-mod-05-staging-tables.py`  
**归档**：执行后更新 `docs/mod-05-prod-migrate-latest.json`
