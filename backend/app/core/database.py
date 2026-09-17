# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import sqlalchemy
from sqlalchemy import String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import logging

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"),
    pool_timeout=30,
    connect_args=connect_args)

# 读写分离支持 (改造 7)
if getattr(settings, "DATABASE_READ_URL", None):
    read_connect_args = {}
    if settings.DATABASE_READ_URL.startswith("sqlite"):
        read_connect_args["check_same_thread"] = False
    read_engine = create_engine(
        settings.DATABASE_READ_URL,
        pool_size=40,  # 读库连接池可稍大
        max_overflow=20,
        pool_recycle=1800,
        pool_pre_ping=not settings.DATABASE_READ_URL.startswith("sqlite"),
        pool_timeout=30,
        connect_args=read_connect_args
    )
else:
    read_engine = engine

class RoutingSession(sqlalchemy.orm.Session):
    def get_bind(self, mapper=None, clause=None, **kwargs):
        # 如果正在 flush（写操作），或在查询对象中标明需要写库，则路由到主库
        if self._flushing or getattr(self, "info", {}).get("write", False):
            return engine
        return read_engine

SessionLocal = sessionmaker(class_=RoutingSession, autocommit=False, autoflush=False, bind=engine)

# ============================================================
# 慢查询日志监控
# ============================================================
import time

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_time = conn.info["query_start_time"].pop(-1)
    total_time = time.time() - start_time
    if total_time >= 0.2:  # 超过 200ms
        logger = logging.getLogger("uj-admin.slow_query")
        logger.warning("慢查询 (%.2f ms): %s", total_time * 1000, statement[:500])

if getattr(settings, "DATABASE_READ_URL", None):
    @event.listens_for(read_engine, "before_cursor_execute")
    def before_cursor_execute_read(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(read_engine, "after_cursor_execute")
    def after_cursor_execute_read(conn, cursor, statement, parameters, context, executemany):
        start_time = conn.info["query_start_time"].pop(-1)
        total_time = time.time() - start_time
        if total_time >= 0.2:
            logger = logging.getLogger("uj-admin.slow_query")
            logger.warning("[只读库] 慢查询 (%.2f ms): %s", total_time * 1000, statement[:500])


# ============================================================
# RLS 集成 — 数据库事务级租户上下文注入
# ============================================================
def _setup_rls_event_listener():
    """注册事务 begin 事件，在每次事务开始时按当前请求租户注入 RLS 上下文。

    为什么用 begin 事件而不是 connect/checkout：
    - 连接是池化复用的，connect/checkout 时点没有所属请求、也常无事务；
      且事件回调拿到的是裸 DBAPI 连接，无法直接用 SQLAlchemy 参数绑定。
    - begin 事件在 SQLAlchemy 开始事务时触发，回调拿到的是该事务的
      Connection（可参数绑定），而 TenantMiddleware 已在请求入口把
      tenant_id 写入 OpenTelemetry context，此时读取即可得到"当前请求"的租户。
    - SET LOCAL 是事务级作用域：事务结束自动失效，连接池复用不会串租户。

    若 context 中取不到租户（主站/后台任务/迁移），则不注入。此时试点表 RLS
    默认 force=False，PG 表属主按语义天然旁路 RLS，因此不会误锁后台读写；
    若显式开了 FORCE，必须保证所有路径都注入租户，否则会读不到任何行。

    注意: SQLite 不支持 RLS / SET LOCAL，仅 PostgreSQL 生效。
    """
    from app.core.opentelemetry_config import get_tenant_from_context

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        """事务开始时，把当前请求租户写入该事务的连接上下文。"""
        if engine.dialect.name != "postgresql":
            return
        try:
            tenant_id = get_tenant_from_context()
            if tenant_id:
                from app.core.security.rls import set_tenant_context
                set_tenant_context(conn, tenant_id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("RLS 租户注入失败（不应阻塞事务）: %s", e)


try:
    _setup_rls_event_listener()
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning("RLS事件监听器初始化失败，继续启动: %s", e)
    pass  # RLS事件监听器初始化失败不应阻塞数据库引擎创建


def rebind_engine(database_url: str | None = None) -> None:
    """按新 URL 重建 engine/SessionLocal（预检、脚本切换 SQLite/Postgres 用）。"""
    global engine, SessionLocal, UUID_TYPE
    url = database_url or settings.DATABASE_URL
    if url.startswith("sqlite"):
        from app.core.sqlite_paths import resolve_sqlite_database_url
        url = resolve_sqlite_database_url(url)
    args = {}
    if url.startswith("sqlite"):
        args["check_same_thread"] = False
    engine = create_engine(
        url,
        pool_size=20,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=not url.startswith("sqlite"),
        pool_timeout=30,
        connect_args=args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    UUID_TYPE = get_uuid_column()
    # 重新注册RLS事件监听器
    _setup_rls_event_listener()


class Base(DeclarativeBase):
    pass


def get_db():
    """get_db。
    :return: 返回处理结果。
    """
    # TODO [P2] 逐步迁移所有 SessionLocal() 直接调用到 get_db() 依赖注入（待全量Review后实施）
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_uuid_column():
    """get_uuid_column。
    :return: 返回处理结果。
    """
    if engine.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        # as_uuid=False：PG 仍存原生 UUID（索引/FK 不变），但读取返回 str，
        # 与全部模型 `Mapped[str]` 及 Pydantic schema 的 str 字段自洽；
        # SQLite 下同为 String(36)→str。此前 as_uuid=True 会让 PG 返回 UUID 对象，
        # 导致 str 类型 schema 校验失败（products 等端点在真 PG 上 500，SQLite 掩盖）。
        return UUID(as_uuid=False)
    return String(36)


UUID_TYPE = get_uuid_column()


def mount_rls_pilot_if_enabled() -> None:
    """按配置门控挂载 RLS 试点表（默认关，生产零回归）。

    仅当 `RLS_PILOT_ENABLED=true` 且数据库为 PostgreSQL 时，对
    `RLS_PILOT_TABLES`（逗号分隔）指定的表创建租户隔离策略。
    策略默认 `force=False`：PG 表属主按语义旁路 RLS，避免在租户注入
    未覆盖所有路径前误锁后台/迁移读写。待全链路租户注入就绪后再开 FORCE。

    前置依赖（真正启用前必须满足）：
      1. 事务 begin 注入已生效（本文件 _setup_rls_event_listener）；
      2. 会话连接角色是目标表的属主（或对属主/服务角色执行 FORCE 的方案已评审）。
    """
    try:
        from app.core.config import settings
        if not settings.RLS_PILOT_ENABLED:
            return
        if engine.dialect.name != "postgresql":
            logger = logging.getLogger(__name__)
            logger.warning(
                "[RLS] RLS_PILOT_ENABLED=true 但非 PostgreSQL 方言 %s，跳过挂载",
                engine.dialect.name,
            )
            return
        pilot = [
            t.strip()
            for t in (settings.RLS_PILOT_TABLES or "").split(",")
            if t.strip()
        ]
        if not pilot:
            logger = logging.getLogger(__name__)
            logger.warning(
                "[RLS] RLS_PILOT_ENABLED=true 但未配置 RLS_PILOT_TABLES，跳过挂载"
            )
            return
        from app.core.security.rls import setup_rls_policies
        result = setup_rls_policies(engine, pilot_tables=pilot, force=False)
        logger = logging.getLogger(__name__)
        logger.info(
            "[RLS] 试点表挂载完成: enabled=%s skipped=%s",
            result["enabled"], result["skipped"],
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("[RLS] 试点表挂载失败（应显式排查，不应静默吞掉）: %s", e)


def get_pool_status() -> dict:
    """返回连接池状态（用于健康检查）"""
    try:
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow(),
            "total": pool.checkedin() + pool.checkedout(),
        }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("获取连接池状态失败: %s", e)
        return {"error": "pool status unavailable"}


# 兼容多大模型跨模块导入契约：get_redis 真身转发到 app.core.cache（唯一 Redis 客户端来源）。
# 注意：本模块不提供 async_session——项目未引入 asyncpg/aiosqlite，不存在异步引擎；
# 任何 async DB 访问需求应改走同步 SessionLocal（参见 acme_service.auto_renew_certificates 修法）。
def get_redis():
    """兼容导出 Redis 依赖（转发 app.core.cache.get_redis）。"""
    from app.core.cache import get_redis as _gr
    return _gr()
