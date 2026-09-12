"""数据库性能优化迁移脚本 — FIX-23: 索引优化

在各表上添加缺失索引，预计可将高频查询的扫描行数从全表扫描降低到索引扫描。

使用方法:
  python scripts/db_performance_optimize.py          # 仅查看（dry-run）
  python scripts/db_performance_optimize.py --apply  # 执行迁移

支持:
  - PostgreSQL（生产）
  - SQLite（开发）
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── P0 索引（必须立即添加）──
P0_INDEXES = [
    # inquiries — 最严重的缺失（几乎所有 Dashboard/Analytics 查询都依赖）
    ("inquiries", "status", "ix_inquiries_status", "status"),
    ("inquiries", "created_at", "ix_inquiries_created_at", "created_at"),
    ("inquiries", "email", "ix_inquiries_email", "email"),
    ("inquiries", "tenant_id, status", "ix_inquiries_tenant_status", "tenant_id, status"),
    ("inquiries", "tenant_id, created_at", "ix_inquiries_tenant_created", "tenant_id, created_at"),

    # products — 高频 is_active 过滤 + 热门排序
    ("products", "is_active", "ix_products_is_active", "is_active"),
    ("products", "view_count", "ix_products_view_count", "view_count"),

    # categories — 树形递归查询
    ("categories", "parent_id", "ix_categories_parent_id", "parent_id"),

    # tenants — 租户列表筛选
    ("tenants", "is_active", "ix_tenants_is_active", "is_active"),
    ("tenants", "created_at", "ix_tenants_created_at", "created_at"),

    # content_pages — 内容管理高频筛选
    ("content_pages", "is_active", "ix_content_pages_is_active", "is_active"),

    # case_studies — 案例筛选
    ("case_studies", "is_active", "ix_case_studies_is_active", "is_active"),

    # user_tenants — 用户-租户关联查询（20+ 处）
    ("user_tenants", "user_id, is_active", "ix_user_tenants_user_active", "user_id, is_active"),
]

# ── P1 索引（高优先级）──
P1_INDEXES = [
    # inquiries 补充
    ("inquiries", "source_channel", "ix_inquiries_source_channel", "source_channel"),
    ("inquiries", "attribution_channel", "ix_inquiries_attribution_channel", "attribution_channel"),
    ("inquiries", "merchant_id", "ix_inquiries_merchant_id", "merchant_id"),
    ("inquiries", "tenant_id, is_active, status", "ix_inquiries_tenant_active_status", "tenant_id, is_active, status"),

    # products 补充
    ("products", "sort_order", "ix_products_sort_order", "sort_order"),
    ("products", "updated_at", "ix_products_updated_at", "updated_at"),
    ("products", "category_id, is_active", "ix_products_category_active", "category_id, is_active"),
    ("products", "is_active, view_count", "ix_products_active_views", "is_active, view_count"),

    # categories 补充
    ("categories", "sort_order", "ix_categories_sort_order", "sort_order"),
    ("categories", "is_active", "ix_categories_is_active", "is_active"),

    # tenants 补充
    ("tenants", "expires_at", "ix_tenants_expires_at", "expires_at"),

    # content_pages 补充
    ("content_pages", "status", "ix_content_pages_status", "status"),
    ("content_pages", "author_id", "ix_content_pages_author_id", "author_id"),

    # content_masters
    ("content_masters", "status", "ix_content_masters_status", "status"),
    ("content_masters", "updated_at", "ix_content_masters_updated_at", "updated_at"),

    # publish_tasks
    ("publish_tasks", "status", "ix_publish_tasks_status", "status"),
    ("publish_tasks", "created_at", "ix_publish_tasks_created_at", "created_at"),

    # tenant_plans
    ("tenant_plans", "is_active", "ix_tenant_plans_is_active", "is_active"),

    # tenant_subscriptions
    ("tenant_subscriptions", "tenant_id, status", "ix_tenant_subscriptions_tenant_status", "tenant_id, status"),

    # payment_orders
    ("payment_orders", "paid_at", "ix_payment_orders_paid_at", "paid_at"),
    ("payment_orders", "status, paid_at", "ix_payment_orders_status_paid", "status, paid_at"),

    # prospect_leads
    ("prospect_leads", "assigned_to", "ix_prospect_leads_assigned_to", "assigned_to"),
    ("prospect_leads", "source", "ix_prospect_leads_source", "source"),

    # ssl_certificates
    ("ssl_certificates", "expires_at", "ix_ssl_certificates_expires_at", "expires_at"),
]


def _table_exists(db, table_name: str) -> bool:
    """检查表是否存在。"""
    db_type = _db_type()
    if db_type == "postgresql":
        result = db.execute(text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :tbl)"
        ), {"tbl": table_name})
        return result.scalar()
    else:
        result = db.execute(text(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name=:tbl"
        ), {"tbl": table_name})
        return result.fetchone() is not None


def _index_exists(db, table_name: str, index_name: str) -> bool:
    """检查索引是否存在。"""
    db_type = _db_type()
    if db_type == "postgresql":
        result = db.execute(text(
            "SELECT EXISTS(SELECT 1 FROM pg_indexes "
            "WHERE tablename = :tbl AND indexname = :idx)"
        ), {"tbl": table_name, "idx": index_name})
        return result.scalar()
    else:
        result = db.execute(text(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name=:idx AND tbl_name=:tbl"
        ), {"idx": index_name, "tbl": table_name})
        return result.fetchone() is not None


def _db_type() -> str:
    """获取数据库类型。"""
    url = str(engine.url)
    if "postgresql" in url:
        return "postgresql"
    return "sqlite"


def apply_indexes(indexes: list[tuple], dry_run: bool = True) -> int:
    """执行索引创建。

    Returns:
        成功创建的索引数
    """
    created = 0
    skipped = 0
    failed = 0

    with SessionLocal() as db:
        for table_name, columns, index_name, _desc in indexes:
            # 检查表
            if not _table_exists(db, table_name):
                log.info("⏭  跳过 %s.%s（表不存在）", table_name, index_name)
                skipped += 1
                continue

            # 检查索引
            if _index_exists(db, table_name, index_name):
                log.info("✅ %s.%s（已存在）", table_name, index_name)
                skipped += 1
                continue

            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"
            if dry_run:
                log.info("📋 [DRY-RUN] %s", sql)
                created += 1
            else:
                try:
                    db.execute(text(sql))
                    db.commit()
                    log.info("✅ 已创建: %s.%s ON (%s)", table_name, index_name, columns)
                    created += 1
                except Exception as e:
                    db.rollback()
                    log.error("❌ 创建失败 %s.%s: %s", table_name, index_name, e)
                    failed += 1

    log.info("---")
    log.info("总计: %d 创建, %d 跳过, %d 失败", created, skipped, failed)
    return created


def main():
    parser = argparse.ArgumentParser(description="数据库性能优化迁移")
    parser.add_argument("--apply", action="store_true", help="执行迁移（默认 dry-run）")
    parser.add_argument("--p0-only", action="store_true", help="仅执行 P0 索引")
    args = parser.parse_args()

    db_type = _db_type()
    log.info("数据库类型: %s", db_type)
    log.info("模式: %s", "执行" if args.apply else "DRY-RUN（预览）")

    if args.p0_only:
        log.info("仅 P0 索引（%d 个）", len(P0_INDEXES))
        apply_indexes(P0_INDEXES, dry_run=not args.apply)
    else:
        log.info("P0 索引（%d 个）", len(P0_INDEXES))
        apply_indexes(P0_INDEXES, dry_run=not args.apply)
        log.info("P1 索引（%d 个）", len(P1_INDEXES))
        apply_indexes(P1_INDEXES, dry_run=not args.apply)

    if not args.apply:
        log.info("\n⚠️  DRY-RUN 模式 — 未实际修改数据库。")
        log.info("   执行迁移: python scripts/db_performance_optimize.py --apply")
        log.info("   仅 P0:    python scripts/db_performance_optimize.py --apply --p0-only")


if __name__ == "__main__":
    main()