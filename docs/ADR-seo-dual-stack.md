# ADR: SEO 双栈（FastAPI 主栈 + Node seo-backend）

## 状态

已采纳（Sprint N，2026-05）

## 背景

- **FastAPI**：`/api/v1/seo-matrix/*`（县域矩阵）、`/api/v1/seo/*`（高级 SEO）
- **Node seo-backend**：历史矩阵服务，经 `SEO_BACKEND_URL` 与 `super-admin/seo-proxy` 代理

## 决策

1. **新功能默认落在 FastAPI**，不新增 Node 发布路径。
2. **集成可见性**：`GET /api/v1/integrations/status` 汇总路由数与 Node 健康探测。
3. **Node 仅维护存量**；未配置或非生产 URL 时标记 `not_configured` / `unreachable`。

## 后果

- 降低双写与数据不一致风险
- 运维需同时监控 FastAPI 与可选 Node 进程
