# ADR: seo-backend vs FastAPI 主从决策

**状态**: 已接受  
**日期**: 2026-05-24  
**任务**: B-06

## 背景

仓库同时存在 `backend/`（FastAPI + PostgreSQL）与 `seo-backend/`（Node/Express + MySQL 矩阵）。发布、SEO 矩阵等能力存在重复实现，易导致双写与部署分裂。

## 决策

1. **主 API**：`backend/` FastAPI 为唯一写入与业务真相源（租户、母版、发布任务、计费、物流等）。
2. **seo-backend**：**只读遗留** — 保留现有矩阵读接口与历史 MySQL 数据，**禁止新增写路径**；新功能一律在 FastAPI 实现。
3. **迁移**：矩阵能力按 Sprint 逐步迁 PG 或经 API 网关聚合；未迁完前，管理端优先调 FastAPI，seo-backend 仅作兼容只读回退。

## 后果

- 新 PR 不得在两个后端各改一套发布/母版逻辑。
- `seo-backend` 可继续运行供旧矩阵页读取，但不扩展 schema。
- CI 以 `scripts/check_mounted_routes.py` 与 FastAPI 路由为准验收。
