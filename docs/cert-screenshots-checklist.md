# 送检 12 截图清单（S0-12）

> **脚本**：`npm run cert:screenshots`  
> **归档**：`docs/cert-screenshots/` · [`manifest.json`](./cert-screenshots/manifest.json)

| 文件 | 路由 | 状态 |
|------|------|------|
| cert-01-login.png | `/login` | ✅ |
| cert-02-tenants.png | `/admin/tenants` | ✅ |
| cert-03-hierarchy.png | `/admin/hierarchy` | ✅ |
| cert-04-aggregation.png | `/admin/aggregation` | ✅ |
| cert-05-health.png | `/system-health/dashboard` | ✅ |
| cert-06-finance.png | `/admin/finance` | ✅ |
| cert-07-products.png | `/products` | ✅ |
| cert-08-categories.png | `/products/categories` | ✅ |
| cert-09-inquiries.png | `/international/inquiries` | ✅ |
| cert-10-seo.png | `/seo-matrix/publish` | ✅ |
| cert-11-ai-content.png | `/admin/ai-center/content` | ✅ |
| cert-12-trade-intel.png | `/admin/ai-engine/trade-intel` | ✅ |

**UX-07 三壳**：`ux-07-client-dashboard.png` · `ux-07-agent-performance.png` · `ux-07-platform-dashboard.png` ✅

```powershell
cd backend; .\.venv\Scripts\python.exe scripts/seed_qa_passwords.py
cd ..\frontend\admin; npm run cert:screenshots
```

*采集完成 · 2026-06-01（15/15 OK · preview :4174 + API :8001）*
