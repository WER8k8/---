"""PostgreSQL Row Level Security (RLS) — 数据库层租户隔离

通过 PostgreSQL 的 Row Level Security 机制，在数据库层面强制执行租户数据隔离：
- 为所有带 tenant_id 的表创建 RLS 策略
- 使用 SET LOCAL app.current_tenant 设置当前会话的租户上下文
- 策略确保每个会话只能访问属于当前租户的数据

工作流程:
  1. 应用连接数据库后调用 set_tenant_context(conn, tenant_id)
  2. PostgreSQL 自动过滤不匹配 tenant_id 的行
  3. 请求结束后调用 clear_tenant_context(conn) 清除上下文

依赖:
  - 目标表必须有 tenant_id 列 (String(36) 或 UUID)
  - PostgreSQL 9.5+
  - 需要超级用户或表所有者权限创建策略
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

log = logging.getLogger(__name__)

# 会话变量名 —— 存储当前 tenant_id
_TENANT_SETTING = "app.current_tenant"


def _exec(conn, sql: str, params: Optional[dict] = None) -> None:
    """统一执行：兼容 SQLAlchemy Connection 与裸 DBAPI 连接（psycopg2 用 %s 占位）。"""
    if isinstance(conn, Connection):
        conn.execute(text(sql), params or {})
    else:
        cur = conn.cursor()
        try:
            cur.execute(sql.replace(":tid", "%s"), list((params or {}).values()))
        finally:
            cur.close()


def set_tenant_context(conn, tenant_id: str) -> None:
    """设置当前数据库会话的租户上下文。

    通过 SET LOCAL 设置会话级变量，RLS 策略中的 CURRENT_SETTING 读取此值。
    SET LOCAL 仅在当前事务内有效，事务结束后自动清除（本包注入点已置于事务 begin 之后）。

    Args:
        conn: SQLAlchemy Connection 或裸 DBAPI 连接
        tenant_id: 当前租户的 UUID 字符串

    Example:
        set_tenant_context(db.connection(), "tenant-uuid-123")
    """
    if not tenant_id:
        log.warning("set_tenant_context: empty tenant_id, skipping")
        return
    _exec(conn, f"SET LOCAL {_TENANT_SETTING} = :tid", {"tid": tenant_id})


def clear_tenant_context(conn) -> None:
    """清除当前数据库会话的租户上下文。

    将 app.current_tenant 重置为空字符串，阻止后续查询访问任何租户数据。

    Args:
        conn: SQLAlchemy Connection 或裸 DBAPI 连接
    """
    _exec(conn, f"SET LOCAL {_TENANT_SETTING} = ''")


def _policy_exists(conn, full_name: str, policy: str) -> bool:
    """PG 没有 CREATE POLICY IF NOT EXISTS；先查 pg_policies 判断是否已存在。"""
    sql = text(
        "SELECT 1 FROM pg_policies "
        "WHERE schemaname = :schema AND tablename = :table AND policyname = :policy"
    )
    schema, _, table = full_name.partition(".")
    if isinstance(conn, Connection):
        return conn.execute(sql, {"schema": schema, "table": table, "policy": policy}).scalar() is not None
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM pg_policies "
            "WHERE schemaname = %s AND tablename = %s AND policyname = %s",
            (schema, table, policy),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()


def setup_rls_policies(
    engine: Engine,
    pilot_tables: Optional[Iterable[str]] = None,
    force: bool = False,
) -> dict[str, list[str]]:
    """为所有带 tenant_id 的表创建 RLS 策略。

    试点挂载：pilot_tables 传入表名（如 ["mcp_servers"]）时仅处理这些表；
    默认（None）处理全部带 tenant_id 的表。生产环境建议先小范围试点验证。

    Args:
        engine: SQLAlchemy 数据库引擎
        pilot_tables: 仅处理的表名集合（不区分 schema）
        force: 是否对所有其他用户强制（FORCE ROW LEVEL SECURITY）。
               默认为 False，仅对表属主生效，避免因当前会话 current_setting
               为空而锁死其它角色的后台读写（如迁移/调度）。

    Returns:
        {"enabled": [已处理的表名列表], "skipped": [无 tenant_id 的表名列表]}

    Example:
        result = setup_rls_policies(engine, pilot_tables=["mcp_servers"])
        log.info("已为 %d 个表启用 RLS", len(result['enabled']))
    """
    enabled_tables: list[str] = []
    skipped_tables: list[str] = []
    if engine.dialect.name != "postgresql":
        log.warning("[RLS] 非 PostgreSQL 方言 %s，跳过 RLS 部署（仅 PG 支持）", engine.dialect.name)
        return {"enabled": [], "skipped": []}
    # 查询所有带 tenant_id 列的表
    discovery_sql = """
        SELECT table_schema, table_name
        FROM information_schema.columns
        WHERE column_name = 'tenant_id'
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
    """
    pilot = {t.lower() for t in (pilot_tables or [])}
    with engine.connect() as conn:
        result = conn.execute(text(discovery_sql))
        tables = [(row[0], row[1]) for row in result]
        for schema, table in tables:
            if pilot and table.lower() not in pilot:
                continue
            full_name = f"{schema}.{table}"
            try:
                _create_table_rls_policies(conn, full_name, table, force=force)
                enabled_tables.append(full_name)
                log.info("[RLS] 已为表 %s 启用租户隔离策略", full_name)
            except Exception as e:
                skipped_tables.append(full_name)
                log.warning("[RLS] 处理表 %s 失败: %s", full_name, e)

        conn.commit()

    log.info(
        "[RLS] 策略部署完成: 已启用 %d 个表, 跳过 %d 个表",
        len(enabled_tables),
        len(skipped_tables),
    )
    return {"enabled": enabled_tables, "skipped": skipped_tables}


def _create_table_rls_policies(
    conn: Connection,
    full_name: str,
    table: str,
    force: bool = False,
) -> None:
    """为单个表创建 RLS 策略：启用 RLS + SELECT/INSERT/UPDATE/DELETE 隔离策略。"""
    # 1. 启用 RLS（幂等）
    conn.execute(
        text(f'ALTER TABLE {full_name} ENABLE ROW LEVEL SECURITY')
    )
    if force:
        conn.execute(
            text(f'ALTER TABLE {full_name} FORCE ROW LEVEL SECURITY')
        )
    # 2. SELECT USING 策略（幂等：已存在则跳过）
    using_policy = f"tenant_isolation_{table}_using"
    if not _policy_exists(conn, full_name, using_policy):
        conn.execute(
            text(
                f"CREATE POLICY {using_policy} "
                f"ON {full_name} "
                f"FOR SELECT "
                f"USING (tenant_id = current_setting('{_TENANT_SETTING}', true))"
            )
        )
    # 3. INSERT WITH CHECK 策略
    check_policy = f"tenant_isolation_{table}_check"
    if not _policy_exists(conn, full_name, check_policy):
        conn.execute(
            text(
                f"CREATE POLICY {check_policy} "
                f"ON {full_name} "
                f"FOR INSERT "
                f"WITH CHECK (tenant_id = current_setting('{_TENANT_SETTING}', true))"
            )
        )
    # 4. UPDATE WITH CHECK 策略
    update_policy = f"tenant_isolation_{table}_update"
    if not _policy_exists(conn, full_name, update_policy):
        conn.execute(
            text(
                f"CREATE POLICY {update_policy} "
                f"ON {full_name} "
                f"FOR UPDATE "
                f"WITH CHECK (tenant_id = current_setting('{_TENANT_SETTING}', true))"
            )
        )
    # 5. DELETE USING 策略
    delete_policy = f"tenant_isolation_{table}_delete"
    if not _policy_exists(conn, full_name, delete_policy):
        conn.execute(
            text(
                f"CREATE POLICY {delete_policy} "
                f"ON {full_name} "
                f"FOR DELETE "
                f"USING (tenant_id = current_setting('{_TENANT_SETTING}', true))"
            )
        )


def disable_rls_policies(engine: Engine) -> list[str]:
    """禁用所有由 setup_rls_policies 创建的 RLS 策略。

    用于维护模式、数据迁移或调试场景。

    Args:
        engine: SQLAlchemy 数据库引擎

    Returns:
        已处理的表名列表
    """
    processed: list[str] = []
    discovery_sql = """
        SELECT table_schema, table_name
        FROM information_schema.columns
        WHERE column_name = 'tenant_id'
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
    """
    with engine.connect() as conn:
        result = conn.execute(text(discovery_sql))
        tables = [(row[0], row[1]) for row in result]
        for schema, table in tables:
            full_name = f"{schema}.{table}"
            try:
                conn.execute(
                    text(f"ALTER TABLE {full_name} DISABLE ROW LEVEL SECURITY")
                )
                processed.append(full_name)
                log.info("[RLS] 已禁用表 %s 的 RLS", full_name)
            except Exception as e:
                log.warning("[RLS] 禁用表 %s RLS 失败: %s", full_name, e)

        conn.commit()

    return processed


def get_rls_status(engine: Engine) -> list[dict]:
    """查询所有表的 RLS 启用状态。

    Returns:
        每个带 tenant_id 的表的 RLS 状态字典列表
    """
    status_sql = """
        SELECT
            c.table_schema,
            c.table_name,
            t.rowsecurity AS rls_enabled
        FROM information_schema.columns c
        JOIN pg_tables t ON t.schemaname = c.table_schema AND t.tablename = c.table_name
        WHERE c.column_name = 'tenant_id'
          AND c.table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY c.table_schema, c.table_name
    """
    with engine.connect() as conn:
        result = conn.execute(text(status_sql))
        return [
            {
                "schema": row[0],
                "table": row[1],
                "rls_enabled": row[2],
            }
            for row in result
        ]
