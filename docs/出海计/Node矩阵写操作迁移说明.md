# 矩阵写操作已迁 FastAPI（T-NODE-2）

## 规则

1. **所有新建/更新/删除**矩阵数据（关键词、内容、发布、平台账号）仅通过 `backend/app/api/v1/routes/seo_matrix.py` 与 `publish-tasks`。
2. `seo-backend` **不得**新增 POST/PUT/PATCH/DELETE 业务路由；仅允许只读 GET 兼容旧页。
3. 管理端 `frontend/admin` 与租户站 SEO 页优先调用 `/api/v1/seo-matrix/*`。

## 验证

- `pytest backend/tests/unit/test_sprint_routes.py -k seo`
- `python scripts/check_mounted_routes.py`
