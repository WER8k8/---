# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""数据库会话 — 从 app.core.database 统一 get_db，避免双引擎问题"""
import logging

from sqlalchemy import inspect, text

from app.core.database import Base, SessionLocal, UUID_TYPE, engine, get_db

logger = logging.getLogger(__name__)

__all__ = ["Base", "SessionLocal", "UUID_TYPE", "engine", "get_db"]

_INQUIRY_ATTRIBUTION_COLS = (
    ("session_id", "VARCHAR(64)"),
    ("landing_path", "VARCHAR(500)"),
    ("last_click_label", "VARCHAR(300)"),
    ("tenant_id", "VARCHAR(36)"),
    ("assigned_to", "VARCHAR(36)"),
)


def _ensure_inquiry_attribution_columns() -> None:
    """开发/未跑 Alembic 033 时补齐 inquiries 归因列（生产请用 alembic upgrade）。"""
    import re
    try:
        insp = inspect(engine)
        if "inquiries" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("inquiries")}
        dialect = engine.dialect.name
        with engine.begin() as conn:
            for col, col_type in _INQUIRY_ATTRIBUTION_COLS:
                if col in existing:
                    continue
                # 严格白名单：仅允许字母、数字、下划线，且以字母/下划线开头
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                    logger.warning("Skipping unsafe column name: %s", col)
                    continue
                safe_col = conn.engine.dialect.identifier_preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(f"ALTER TABLE inquiries ADD COLUMN IF NOT EXISTS {safe_col} {col_type}")
                    )
                else:
                    conn.execute(text(f"ALTER TABLE inquiries ADD COLUMN {safe_col} {col_type}"))
                logger.info("Added inquiries.%s for traffic attribution", col)
    except Exception as exc:
        logger.warning("Could not ensure inquiry attribution columns: %s", exc)


_MEDIA_RENDER_COLS = (
    ("scenario", "VARCHAR(64)"),
    ("prompt_text", "TEXT"),
    ("image_url", "VARCHAR(500)"),
    ("result_url", "VARCHAR(500)"),
    ("result_path", "VARCHAR(500)"),
    ("started_at", "DATETIME"),
    ("finished_at", "DATETIME"),
    ("tenant_id", "VARCHAR(36)"),
    ("file_size_bytes", "INTEGER DEFAULT 0"),
    ("expires_at", "DATETIME"),
    ("purge_at", "DATETIME"),
    ("handoff_type", "VARCHAR(20)"),
    ("handoff_at", "DATETIME"),
    ("handoff_external_url", "VARCHAR(500)"),
    ("file_purged", "INTEGER DEFAULT 0"),
    ("edit_config", "TEXT"),
    ("edited_result_path", "VARCHAR(500)"),
    ("edited_result_url", "VARCHAR(500)"),
    ("guest_token", "VARCHAR(64)"),
    ("cloud_provider", "VARCHAR(20)"),
    ("cloud_vid", "VARCHAR(64)"),
    ("cloud_play_url", "VARCHAR(500)"),
    ("cloud_r2_key", "VARCHAR(500)"),
    ("cloud_r2_url", "VARCHAR(1000)"),
    ("cloud_backup_url", "VARCHAR(500)"),
    ("cloud_upload_status", "VARCHAR(20) DEFAULT 'pending'"),
)

_PLATFORM_ACCOUNT_COLS = (
    ("tenant_id", "VARCHAR(36)"),
)


def _ensure_platform_account_columns() -> None:
    """_ensure_platform_account_columns。
    :return: 返回处理结果。
    """
    try:
        insp = inspect(engine)
        if "platform_accounts" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("platform_accounts")}
        dialect = engine.dialect.name
        with engine.begin() as conn:
            preparer = conn.engine.dialect.identifier_preparer
            for col, col_type in _PLATFORM_ACCOUNT_COLS:
                if col in existing:
                    continue
                safe_col = preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(
                            f"ALTER TABLE platform_accounts ADD COLUMN IF NOT EXISTS {safe_col} {col_type}"
                        )
                    )
                else:
                    conn.execute(text(f"ALTER TABLE platform_accounts ADD COLUMN {safe_col} {col_type}"))
                logger.info("Added platform_accounts.%s", col)
    except Exception as exc:
        logger.warning("Could not ensure platform_accounts columns: %s", exc)


def _ensure_media_render_columns() -> None:
    """开发库未跑 Alembic 时补齐 media_render_tasks 列。"""
    try:
        insp = inspect(engine)
        if "media_render_tasks" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("media_render_tasks")}
        dialect = engine.dialect.name
        with engine.begin() as conn:
            preparer = conn.engine.dialect.identifier_preparer
            for col, col_type in _MEDIA_RENDER_COLS:
                if col in existing:
                    continue
                safe_col = preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(
                            f"ALTER TABLE media_render_tasks ADD COLUMN IF NOT EXISTS {safe_col} {col_type}"
                        )
                    )
                else:
                    conn.execute(text(f"ALTER TABLE media_render_tasks ADD COLUMN {safe_col} {col_type}"))
                logger.info("Added media_render_tasks.%s", col)
    except Exception as exc:
        logger.warning("Could not ensure media_render columns: %s", exc)


_SEO_METADATA_COLS = (
    ("entity_type", "VARCHAR(50)"),
    ("entity_id", "VARCHAR(36)"),
    ("resource_type", "VARCHAR(50)"),
    ("resource_id", "VARCHAR(50)"),
)


def _ensure_seo_metadata_columns() -> None:
    """_ensure_seo_metadata_columns。
    :return: 返回处理结果。
    """
    try:
        insp = inspect(engine)
        if "seo_metadata" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("seo_metadata")}
        dialect = engine.dialect.name
        with engine.begin() as conn:
            preparer = conn.engine.dialect.identifier_preparer
            for col, col_type in _SEO_METADATA_COLS:
                if col in existing:
                    continue
                safe_col = preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(f"ALTER TABLE seo_metadata ADD COLUMN IF NOT EXISTS {safe_col} {col_type}")
                    )
                else:
                    conn.execute(text(f"ALTER TABLE seo_metadata ADD COLUMN {safe_col} {col_type}"))
                logger.info("Added seo_metadata.%s", col)
    except Exception as exc:
        logger.warning("Could not ensure seo_metadata columns: %s", exc)


def _ensure_ai_model_sort_order_column() -> None:
    """开发 SQLite 未跑 041 迁移时补齐 ai_model_configs.sort_order。"""
    try:
        insp = inspect(engine)
        if "ai_model_configs" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("ai_model_configs")}
        if "sort_order" in existing:
            return
        dialect = engine.dialect.name
        with engine.begin() as conn:
            if dialect == "postgresql":
                conn.execute(
                    text(
                        "ALTER TABLE ai_model_configs ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0"
                    )
                )
            else:
                conn.execute(
                    text("ALTER TABLE ai_model_configs ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
                )
            rows = conn.execute(
                text(
                    """
                    SELECT id, provider_id FROM ai_model_configs
                    ORDER BY provider_id, is_default DESC, created_at ASC
                    """
                )
            ).fetchall()
            rank_by_provider: dict[str, int] = {}
            for row in rows:
                pid = str(row[1])
                rank_by_provider[pid] = rank_by_provider.get(pid, 0) + 1
                conn.execute(
                    text("UPDATE ai_model_configs SET sort_order = :n WHERE id = :id"),
                    {"n": rank_by_provider[pid], "id": str(row[0])},
                )
        logger.info("Added ai_model_configs.sort_order")
    except Exception as exc:
        logger.warning("Could not ensure ai_model_configs.sort_order: %s", exc)


def _ensure_egress_jit_columns() -> None:
    """SQLite/未跑 042 时补齐 egress JIT 字段与任务表。"""
    try:
        insp = inspect(engine)
        if "egress_endpoints" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("egress_endpoints")}
        dialect = engine.dialect.name
        patches = [
            ("upstream_ref", "VARCHAR(200)"),
            ("proxy_username", "VARCHAR(200)"),
            ("proxy_password", "VARCHAR(200)"),
            ("provision_error", "VARCHAR(500)"),
        ]
        with engine.begin() as conn:
            preparer = conn.engine.dialect.identifier_preparer
            for col, col_type in patches:
                if col in existing:
                    continue
                safe_col = preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(
                            f"ALTER TABLE egress_endpoints ADD COLUMN IF NOT EXISTS {safe_col} {col_type}"
                        )
                    )
                else:
                    conn.execute(
                        text(f"ALTER TABLE egress_endpoints ADD COLUMN {safe_col} {col_type}")
                    )
            if "qc_meta" not in existing:
                if dialect == "postgresql":
                    conn.execute(
                        text(
                            "ALTER TABLE egress_endpoints ADD COLUMN IF NOT EXISTS qc_meta JSONB"
                        )
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE egress_endpoints ADD COLUMN qc_meta JSON")
                    )
        if "egress_provision_jobs" not in insp.get_table_names():
            Base.metadata.create_all(
                bind=engine, tables=[Base.metadata.tables["egress_provision_jobs"]]
            )
        logger.info("Ensured egress JIT schema patches")
    except Exception as exc:
        logger.warning("Could not ensure egress JIT columns: %s", exc)


def _ensure_iproyal_egress_schema() -> None:
    """SQLite/未跑 043 时补齐 IPRoyal 字段与成本/补池表。"""
    try:
        insp = inspect(engine)
        if "egress_endpoints" in insp.get_table_names():
            existing = {c["name"] for c in insp.get_columns("egress_endpoints")}
            dialect = engine.dialect.name
            patches = [
                ("iproyal_order_id", "INTEGER"),
                ("expire_date", "DATETIME"),
                ("renew_count", "INTEGER DEFAULT 0"),
            ]
            with engine.begin() as conn:
                preparer = conn.engine.dialect.identifier_preparer
                for col, col_type in patches:
                    if col in existing:
                        continue
                    safe_col = preparer.quote(col)
                    if dialect == "postgresql":
                        conn.execute(
                            text(
                                f"ALTER TABLE egress_endpoints ADD COLUMN IF NOT EXISTS {safe_col} {col_type}"
                            )
                        )
                    else:
                        conn.execute(
                            text(f"ALTER TABLE egress_endpoints ADD COLUMN {safe_col} {col_type}")
                        )
        missing_tables = [
            t
            for t in ("egress_cost_records", "egress_pool_replenish_jobs")
            if t not in insp.get_table_names()
        ]
        if missing_tables:
            import app.models  # noqa: F401
            Base.metadata.create_all(
                bind=engine,
                tables=[Base.metadata.tables[name] for name in missing_tables],
            )
        if "egress_suppliers" not in insp.get_table_names():
            import app.models  # noqa: F401
            Base.metadata.create_all(
                bind=engine, tables=[Base.metadata.tables["egress_suppliers"]]
            )
        logger.info("Ensured IPRoyal egress schema patches")
    except Exception as exc:
        logger.warning("Could not ensure IPRoyal egress schema: %s", exc)


_ORDER_TRADE_COLS = (
    ("incoterms", "VARCHAR(10)"),
    ("payment_terms", "VARCHAR(50)"),
    ("deposit_ratio", "NUMERIC(5, 2)"),
    ("deposit_amount", "NUMERIC(10, 2)"),
    ("port_of_loading", "VARCHAR(100)"),
    ("port_of_discharge", "VARCHAR(100)"),
    ("gross_weight", "NUMERIC(12, 3)"),
    ("net_weight", "NUMERIC(12, 3)"),
    ("volume", "NUMERIC(12, 3)"),
    ("shipping_marks", "TEXT"),
    ("container_no", "VARCHAR(50)"),
    ("bl_number", "VARCHAR(50)"),
)


def _ensure_order_trade_columns() -> None:
    """未跑 111 迁移时补齐 orders 外贸履约字段（P/I 定金 + CI/箱单数据）。"""
    try:
        insp = inspect(engine)
        if "orders" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("orders")}
        dialect = engine.dialect.name
        with engine.begin() as conn:
            preparer = conn.engine.dialect.identifier_preparer
            for col, col_type in _ORDER_TRADE_COLS:
                if col in existing:
                    continue
                safe_col = preparer.quote(col)
                if dialect == "postgresql":
                    conn.execute(
                        text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {safe_col} {col_type}")
                    )
                else:
                    conn.execute(text(f"ALTER TABLE orders ADD COLUMN {safe_col} {col_type}"))
                logger.info("Added orders.%s for foreign-trade fulfillment", col)
    except Exception as exc:
        logger.warning("Could not ensure order trade columns: %s", exc)


def init_db():
    """初始化数据库表结构（保留 in session 层以维持向后兼容）"""
    import app.models  # noqa: F401 — 注册全部 ORM（含 SiteAnalyticsEvent）
    if engine.dialect.name == "postgresql":
        # Postgres 由 alembic 管理；create_all 会与既有 VARCHAR/UUID 漂移冲突导致启动失败
        logger.info("init_db: PostgreSQL — skip create_all, run column patches only")
    else:
        Base.metadata.create_all(bind=engine)
    _ensure_egress_jit_columns()
    _ensure_iproyal_egress_schema()
    _ensure_inquiry_attribution_columns()
    _ensure_media_render_columns()
    _ensure_platform_account_columns()
    _ensure_seo_metadata_columns()
    _ensure_ai_model_sort_order_column()
    _ensure_order_trade_columns()
