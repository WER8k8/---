# 数据库切换指南 (SQLite ↔ PostgreSQL)

> P3-015: 防止 `DB_TYPE=postgresql` 但 `DATABASE_URL` 仍指向 SQLite 的生产事故。

## 一、配置项

`backend/config/{ENV}/.env` 中:

| 变量 | 取值 | 说明 |
| --- | --- | --- |
| `DB_TYPE` | `sqlite` \| `postgresql` | 显式声明数据库类型 |
| `DATABASE_URL` | 见下 | 实际连接串 |

### SQLite (dev)

```env
DB_TYPE=sqlite
DATABASE_URL=sqlite:///./data/dev.db
```

### PostgreSQL (prod / staging)

```env
DB_TYPE=postgresql
DATABASE_URL=postgresql+asyncpg://youding:STRONG_PASSWORD@postgres:5432/youding_prod
```

> 强烈建议显式声明 `+asyncpg` 驱动,SQLAlchemy 2.0 异步模式需要它。

## 二、切库流程

### 2.1 从 SQLite → PostgreSQL (上线)

1. **创建库/用户** (一次性):
   ```sql
   CREATE USER youding_admin WITH PASSWORD '...';
   CREATE DATABASE youding_prod OWNER youding_admin;
   GRANT ALL PRIVILEGES ON DATABASE youding_prod TO youding_admin;
   ```

2. **更新 `.env`** (生产由 Secrets Manager 注入):
   ```env
   DB_TYPE=postgresql
   DATABASE_URL=postgresql+asyncpg://youding_admin:STRONG_PASSWORD@postgres:5432/youding_prod
   ```

3. **导出旧数据** (SQLite):
   ```bash
   sqlite3 data/dev.db ".dump" > backup_$(date +%Y%m%d).sql
   ```

4. **迁移 + 导入** (使用 Alembic):
   ```bash
   cd backend
   ENV_FILE=config/prod/.env alembic upgrade head
   psql -h postgres -U youding_admin -d youding_prod -f backup_*.sql
   ```

5. **冒烟测试**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/health/ready   # 应返回 db 状态 ok
   ```

6. **回归关键 API**:登录、列表、创建订单、上传文件。

### 2.2 从 PostgreSQL → SQLite (回滚到 dev)

仅用于本地调试,生产**禁止**。

```env
DB_TYPE=sqlite
DATABASE_URL=sqlite:///./data/dev.db
```

## 三、配置一致性校验

`app.core.config.Settings.__init__` 会在加载时强制校验:

- `DB_TYPE=postgresql` 但 URL 不含 `postgresql` → **启动失败**
- `DB_TYPE=sqlite` 但 URL 不含 `sqlite` → **启动失败**
- `DB_TYPE` 为其他值 → 仅警告
- `postgresql://` 缺 `+asyncpg` → 警告(不阻断)

## 四、健康检查

`GET /health/ready` 会同时检查 DB 连通性,返回 JSON:

```json
{
  "status": "ok",
  "checks": {
    "db": "ok",
    "redis": "skipped",
    "minio": "ok"
  }
}
```

## 五、Docker Compose

`docker-compose.yml` 已默认配置:

- `postgres:15-alpine` 容器,数据卷持久化
- 后端环境变量注入 `${DB_PASSWORD}` (从 `.env` 读)
- 健康检查 `pg_isready`

启动命令:

```bash
docker compose up -d postgres
docker compose up -d backend
```

## 六、相关单元测试

```bash
cd backend
ENV_FILE=config/dev/.env pytest tests/unit/test_db_type_p3_015.py -v
```

覆盖 10 个场景,包括:

- 类型不匹配 → 抛错
- 驱动缺失 → 警告
- 传统 `postgres://` 协议 → 兼容
- 默认 dev 配置 → 正常加载

## 七、故障排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ValueError: [配置错误] DB_TYPE=postgresql 但 DATABASE_URL 不含 postgresql 协议` | `.env` 改 `DB_TYPE` 但忘改 `DATABASE_URL` | 同步修改 `DATABASE_URL` |
| `[配置建议] 缺 +asyncpg 驱动声明` | URL 是 `postgresql://` 而非 `postgresql+asyncpg://` | URL 改为 `postgresql+asyncpg://...` |
| `/health/ready` 返回 `db: error` | Postgres 容器未起 / 密码错 / 网络不通 | `docker compose ps postgres`;`psql` 测试连通 |
| `asyncpg.exceptions.InvalidPasswordError` | 密码含特殊字符未 URL 编码 | 用 `urllib.parse.quote_plus()` 编码 |
