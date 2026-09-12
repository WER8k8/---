# SQLite → PostgreSQL 迁移指南

## 环境策略

| 环境       | 数据库        | 说明                     |
|------------|---------------|--------------------------|
| 本地开发   | SQLite        | 零配置，开箱即用         |
| 生产环境   | PostgreSQL    | 高性能、多并发、ACID     |

## 技术架构

```
本地开发:  backend/.env  → DATABASE_URL=sqlite:///./youding_dev.db
生产环境:  .env.prod     → 通过 Docker env 变量注入
           DB_USER / DB_PASSWORD / DB_NAME → postgres 服务
```

- 本地开发时，`alembic/env.py` 从 `DATABASE_URL` 环境变量读取 URL，
  若未设置则回退到 `settings.DATABASE_URL`（默认 SQLite）。
- 生产 Docker 环境由 `docker-compose.prod.yml` 注入完整的 PostgreSQL
  连接字符串。

## 生产环境部署步骤

### 1. 启动 PostgreSQL 容器

```bash
docker compose -f docker-compose.prod.yml up -d postgres
```

### 2. 运行数据库迁移

```bash
# 进入 backend 目录
cd backend

# 运行 Alembic 迁移
DATABASE_URL=postgresql://user:password@localhost:5432/youding alembic upgrade head
```

### 3. 初始化种子数据（如有）

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/youding python seed.py
```

### 4. 启动完整服务栈

```bash
docker compose -f docker-compose.prod.yml up -d
```

## 从 SQLite 迁移历史数据到 PostgreSQL

如果存在 SQLite 中积累的现网数据需要迁移到 PostgreSQL，可使用以下方案：

### 方案 A：pgloader（推荐）

```bash
# 安装 pgloader
# macOS: brew install pgloader
# Ubuntu: apt install pgloader

# 编写迁移配置 loadfile.load
cat > /tmp/migrate.load << 'EOF'
LOAD DATABASE
  FROM sqlite:///path/to/app.db
  INTO postgresql://user:password@localhost:5432/youding

WITH include drop, create tables, create indexes, reset sequences,
     batch rows = 500, batch concurrency = 1

SET maintenance_work_mem to '128MB',
    work_mem to '16MB'
EOF

pgloader /tmp/migrate.load
```

### 方案 B：手动导出导入

```bash
# 1. 导出 SQLite 为 SQL dump
sqlite3 app.db .dump > data.sql

# 2. 手动处理 SQL 差异（重点是自增主键和布尔值）
#    - SQLite 的 AUTOINCREMENT → PostgreSQL 的 SERIAL / BIGSERIAL
#    - SQLite 的 INTEGER 0/1 → PostgreSQL 的 BOOLEAN false/true
#    - SQLite 的 DATETIME → PostgreSQL 的 TIMESTAMPTZ

# 3. 导入到 PostgreSQL
psql -h localhost -U user -d youding -f data_cleaned.sql
```

## Alembic 兼容性说明

`backend/alembic/env.py` 已配置为数据库无关：

- `target_metadata = Base.metadata`：自动包含所有 SQLAlchemy 模型
- `get_url()` 函数从环境变量 `DATABASE_URL` 读取，兼容 SQLite 和 PostgreSQL
- 无需修改 Alembic 配置文件即可在两种数据库间切换

## 验证迁移结果

```bash
# 检查 PostgreSQL 容器运行状态
docker compose -f docker-compose.prod.yml ps postgres

# 连接数据库验证表结构
psql -h localhost -U user -d youding -c "\dt"

# 查看 Alembic 迁移历史
DATABASE_URL=postgresql://user:password@localhost:5432/youding alembic current
```

## 注意事项

- **密码安全**：生产环境务必使用强随机密码，切勿使用示例 `user:password`
- **pg_hba.conf**：确保允许应用服务器 IP 段的连接
- **连接池**：PostgreSQL 建议使用 `pool_size=20` + `max_overflow=10`
- **定时备份**：docker-compose 已包含 `db-backup` 服务（profile: backup），
  启用方式：
  ```bash
  docker compose -f docker-compose.prod.yml --profile backup up -d db-backup
  ```
