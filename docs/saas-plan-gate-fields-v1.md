# SAAS-03 · Plan Gate 字段定义

> **唯一文案源**：[`marketing/plan-copy-deck.md`](./marketing/plan-copy-deck.md)  
> **BFF**：`GET /api/v1/admin-bff/dict/plan_features`（BE-05 stub）

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `feature_key` | string | 如 `seo_matrix` · `im` · `white_label` |
| `min_plan` | enum | `trial` \| `starter` \| `pro` \| `enterprise` |
| `cta_copy` | string | 「该能力属于 **{plan}**，升级后立即可用」 |
| `route` | string | 被 gate 的路由，如 `/client/egress` |

## 与 Stub 矩阵关系

| 路径 | 策略 | min_plan |
|------|------|----------|
| `/client/egress` | planGate | enterprise |
| `/client/media-factory` | lab | pro（W3） |

## 服务端（BE-04 待做）

- 中间件读取 JWT tenant → plan_code → 拒绝 403 + `{ upgrade_plan, cta }`

*SAAS-03 v1 · W2*
