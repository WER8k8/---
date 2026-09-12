# MOD-03 · 40 平台正式表 PM 签字清单（S2 批次 · 记录占位已就绪）

> **代码主数据**：`backend/app/services/platform_catalog.py`（国内 20 + 海外 20）  
> **签字记录**：`docs/compliance/mod-03-platform-signoff-record.json`  
> **验证**：`python scripts/validate-mod-03-platform-signoff.py`

| # | 项 | 说明 | PM |
|---|-----|------|-----|
| 1 | 平台总数 | catalog = **40**（CN 20 + Global 20） | ☐ |
| 2 | 与 SEO/发布链路一致 | `/api/v1/platforms/catalog` 可读 | ☐ |
| 3 | 试点 5+5 | `PILOT_NAMES` 与 PM blocker 名单一致 | ☐ |
| 4 | 正式表归档 | 签字后更新 `signed_by` / `signed_at` | ☐ |

**签字后**：`python scripts/sync-owner-blockers-from-records.py`（若关联 MOD-08）
