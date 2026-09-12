# SEO 独立矩阵库部署（SEO-09）

Hermes 司令部与统一登录通过 `SEO_MATRIX_*` 连接 Node SEO 矩阵库的 `admin_users` 表。

## 方式一：连接串（推荐生产）

```env
SEO_MATRIX_DATABASE_URL=mysql+pymysql://user:pass@host:3306/seo_matrix_db?charset=utf8mb4
```

## 方式二：分项

```env
SEO_MATRIX_DB_HOST=127.0.0.1
SEO_MATRIX_DB_PORT=3306
SEO_MATRIX_DB_USER=seo_admin
SEO_MATRIX_DB_PASSWORD=***
SEO_MATRIX_DB_NAME=seo_matrix_db
```

## 本地 SQLite（开发）

```env
SEO_MATRIX_SQLITE_PATH=./data/seo_matrix.sqlite
```

需存在 `admin_users` 表，结构与 Node 矩阵项目一致。

## 健康探针

- API：`GET /hermes/ops/seo-matrix-db/health`（超管）
- 司令部快照：`seo.seo_matrix_db`

返回字段：`configured`、`reachable`、`mode`（mysql/sqlite/none）、`admin_users_count`。

## Rank Scheduler（SEO-04）

生产开启每日排名线程：

```env
RANK_SCHEDULER_ENABLED=true
```

启动时自动从主库 `keywords` 表同步追踪词；也可在 Admin **Rank Scheduler** 页或 `POST /hermes/ops/rank-scheduler/sync` 手动同步。

## Tavily 外网雷达（RADAR-09）

```env
TAVILY_API_KEY=tvly-***
```

未配置时技术雷达仅使用 RSS/GitHub 公开源，不影响启动。

## 验证

```powershell
powershell -File scripts/brand-guard-audit.ps1
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8001/api/v1/hermes/ops/seo-matrix-db/health
```
