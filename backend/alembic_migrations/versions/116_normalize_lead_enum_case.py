"""线索枚举词表对齐（prospect_leads）

背景：LeadStatus/LeadSource 与订单枚举同病——Python value 为小写，
PG 原生 enum 标签曾为大写 Name，ORM 以 value 读回时 LookupError。
本迁移将 lead_status_enum / lead_source_enum 重建为小写 value 词表。

依赖：down_revision = 115_normalize_order_status_case
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "116_normalize_lead_enum_case"
down_revision: Union[str, None] = "115_normalize_order_status_case"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LEAD_STATUS = [
    "discovered", "enriched", "verified", "qualified",
    "contacted", "engaged", "converted", "archived", "invalid",
]
_LEAD_SOURCE = [
    "google_cse", "website_scrape", "hunter_io", "apollo_io",
    "linkedin", "whatsapp", "reddit", "tiktok", "quora",
    "manual_import", "referral",
]


def _rebuild(conn, type_name: str, values: list[str], table: str, col: str) -> None:
    exists = conn.execute(
        sa.text("SELECT 1 FROM pg_type t WHERE t.typname = :n"), {"n": type_name}
    ).scalar()
    conn.execute(sa.text(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" TYPE text USING ("{col}"::text)'))
    conn.execute(sa.text(f'UPDATE "{table}" SET "{col}" = lower("{col}") WHERE "{col}" IS NOT NULL'))
    if not exists:
        return
    tmp = f"{type_name}_new"
    conn.execute(sa.text(f'DROP TYPE IF EXISTS "{tmp}" CASCADE'))
    labels = ", ".join(f"'{v}'" for v in values)
    conn.execute(sa.text(f'CREATE TYPE "{tmp}" AS ENUM ({labels})'))
    conn.execute(sa.text(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" TYPE "{tmp}" USING ("{col}")::"{tmp}"'))
    conn.execute(sa.text(f'DROP TYPE IF EXISTS "{type_name}" CASCADE'))
    conn.execute(sa.text(f'ALTER TYPE "{tmp}" RENAME TO "{type_name}"'))


def upgrade() -> None:
    conn = op.get_bind()
    _rebuild(conn, "lead_status_enum", _LEAD_STATUS, "prospect_leads", "status")
    _rebuild(conn, "lead_source_enum", _LEAD_SOURCE, "prospect_leads", "source")


def downgrade() -> None:
    pass
