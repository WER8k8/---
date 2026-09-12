# Sprint K · 商业闭环深化

> **目标**：财务中台看板、Token 耗尽停服、枢纽 GSC 检查清单。

## 交付

| ID | 内容 |
|----|------|
| K-01 | `TokenService` 余额为 0 自动 `suspended`（`suspend_reason=token_depleted`），充值恢复 |
| K-02 | `GET /finance/summary` 增强：分润、净利润、Top 租户营收 |
| K-03 | `GET /finance/export.csv` 超管导出 |
| K-04 | `GET/POST /hub/search-console/*` GSC 清单与 ping |
| K-05 | 管理端 **财务中台** 页 `/admin/finance` |

## 路径

- 财务看板：超级管理员 → **财务中台**
- 枢纽 sitemap：`GET /api/v1/hub/sitemap.xml`
- GSC 清单：`GET /api/v1/hub/search-console/checklist`

## 环境变量（可选）

```env
PUBLIC_API_BASE=https://api.youding.com   # sitemap 对外 URL
GSC_SERVICE_ACCOUNT_JSON=                # 未来接入 Google Indexing API
```

## 说明

- 呼朋唤友首单奖励已在 `ProvisioningService` 支付回调中发放。
- 总站前台页：`frontend/pages/industry/[tenantSlug]/[contentId].vue` 已存在，本 Sprint 补运营 API 与财务看板。
