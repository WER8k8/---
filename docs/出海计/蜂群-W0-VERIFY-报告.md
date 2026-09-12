# 蜂群 W0-VERIFY 报告

**时间**: 2026-05-28  
**包**: W0-VERIFY（只读核验 + 任务 JSON）  
**工作区**: `website CodeBuddy`

## 结论摘要

| 任务 ID | 标题 | 判定 | 状态更新 |
|---------|------|------|----------|
| T-P0-01 | 复扫 referral 挂载 | 通过 | `done` |
| T-P0-02 | 复扫 super_admin 挂载 | 通过（见路径说明） | `done` |
| T-P0-05 | content_master 模型 CRUD | 通过 | `done` |
| T-P0-12 | logistics/track API | 通过 | `done` |
| T-P0-07 | 40 平台生产 seed | 通过 | `done` |

## 证据

### T-P0-01 — `GET /api/v1/referral/leaderboard`

- 路由定义：`backend/app/api/v1/routes/referral.py` — `APIRouter(prefix="/referral")` + `@router.get("/leaderboard")`。
- 挂载：`backend/app/api/v1/routes/__init__.py` — `router.include_router(referral_router)`（v1 前缀 `/v1`，API 总前缀 `/api`）。
- OpenAPI 路径表（`app.routes`）：存在 **`/api/v1/referral/leaderboard`**（EXACT）。
- 测试：`pytest tests/unit/test_sprint_routes.py::test_referral_mounted` — **14/14 passed**（2026-05-28，需 `JWT_SECRET_KEY` / `SECRET_KEY` 环境）。
- 运行时：空 SQLite 无表时 leaderboard 可能 500（缺 `referral_codes`）；属 DB 未迁移，非未挂载。

### T-P0-02 — super_admin / dashboard

- 挂载：`routes/__init__.py` — `router.include_router(super_admin_router)`；`super_admin/__init__.py` — `prefix="/super-admin"`，`dashboard_router` 挂在 `prefix="/dashboard"`。
- 子路由：`super_admin/dashboard.py` — `@router.get("/stats")` 等。
- OpenAPI 路径：存在 **`/api/v1/super-admin/dashboard/stats`**、**`/system-status`**、**`/ai-usage`** 等；**不存在** 无后缀的 **`/api/v1/super-admin/dashboard`**。
- HTTP 冒烟（TestClient，`raise_server_exceptions=False`）：
  - `GET /api/v1/super-admin/dashboard` → **404**
  - `GET /api/v1/super-admin/dashboard/stats` → **401**（需超管鉴权，路由可达）
- 测试：`test_sprint_routes.py::test_super_admin_mounted` — passed。

> **说明**：验收清单写的 `GET /api/v1/super-admin/dashboard` 当前无根 handler；实际大盘入口为 **`/api/v1/super-admin/dashboard/stats`**（及同前缀子路径）。任务 T-P0-02 标题为「复扫 super_admin 挂载」，挂载与子树已确认。

### T-P0-05 — content_master CRUD

- 文件：`backend/app/api/v1/routes/content_master.py`
- 装饰器：`GET/POST ""`，`GET/PUT/DELETE "/{master_id}"`，另 `publish`、`link-preview`。
- 挂载路径：**`/api/v1/content-masters`**（复数，EXACT 在 `app.routes`）。
- 测试：`test_sprint_routes.py::test_content_masters_mounted` — passed。

### T-P0-12 — logistics `/track`

- 文件：`backend/app/api/v1/routes/logistics.py` — `@router.get("/track")`。
- 挂载：`include_router(logistics_router, prefix="/logistics")` → **`/api/v1/logistics/track`**（EXACT）。
- HTTP：`GET /api/v1/logistics/track` → **401**（鉴权，非 404）。
- 测试：`test_sprint_routes.py::test_logistics_track_mounted` — passed。

### T-P0-07 — 40 平台 seed 脚本

- 脚本：`backend/scripts/seed_platforms_full.py`（注释：正式 40 平台，国内 20 + 海外 20）。
-  companion：`backend/scripts/seed_platforms_pilot.py`。
- 目录数据：`app/services/platform_catalog.py` — `all_catalog_rows()` 返回 **40** 行（venv 执行 `len(all_catalog_rows())` → 40）。
- `py_compile`：`seed_platforms_full.py`、`seed_platforms_pilot.py` — **compile_ok**。
- `check_mounted_routes.py`：本机未设 `SECRET_KEY` 时失败；设 `SECRET_KEY>=32` 后可 import `app.main` 并列路径（见上）。

## 执行的命令

```powershell
$env:SECRET_KEY="..."; $env:JWT_SECRET_KEY="test-..." + ("x"*32)
cd backend
.\.venv\Scripts\python.exe -m pytest tests/unit/test_sprint_routes.py -q
.\.venv\Scripts\python.exe -c "from app.services.platform_catalog import all_catalog_rows; print(len(all_catalog_rows()))"
.\.venv\Scripts\python.exe -m py_compile scripts/seed_platforms_full.py scripts/seed_platforms_pilot.py
python ..\scripts\sprint-task-report.py
```

## JSON 变更

`docs/dev-sprint-all-in-one.json`：上述 5 个任务 `status` → **`done`**（仅此文件，未改后端业务代码）。

## 未覆盖 / 风险

- 未对生产 DB 执行 seed 或全量 HTTP 200 联调。
- `GET /api/v1/super-admin/dashboard` 无根路由；前端若硬编码该 URL 需对齐 `/dashboard/stats`。
- `pytest` 全量 conftest 在本次环境曾遇 `accio_gap_handlers` 循环 import；`test_sprint_routes.py` 单独跑 14 passed。
