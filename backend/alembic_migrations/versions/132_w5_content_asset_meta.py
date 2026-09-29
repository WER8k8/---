# -*- coding: utf-8 -*-
"""132 — W5 ContentAsset asset_meta 列（修正设计稿 模块4 / 契约 §5.1 路线B · 裁-1）

裁定：**只加 1 列、不建表**。`content_masters.asset_meta JSON NULL` 承载 6 个
净新增溯源/上下文字段：`{product_id, market, language, source_refs,
prompt_version, model_version}`（纯 facade 会让 6 字段永久为 null，满足不了
设计稿 4.3/4.6「能反向定位到 product」）。

- 幂等：`ADD COLUMN IF NOT EXISTS` 语义（先 inspect 判存在）。
- 可空、无默认回填（存量行保持 NULL，诚实降级）。
- 保持单 head：`down_revision = "131_w5_industry_profiles"`。
- `downgrade`：`DROP COLUMN asset_meta`。

⚠ 只加列不建表 → public 表数维持 270。
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "132_w5_content_asset_meta"
down_revision: Union[str, None] = "131_w5_industry_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table: str) -> set[str]:
    try:
        return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
    except Exception:  # noqa: BLE001
        return set()


def upgrade() -> None:
    if "content_masters" not in _table_names():
        return
    if "asset_meta" in _column_names("content_masters"):
        return
    op.add_column("content_masters", sa.Column("asset_meta", sa.JSON(), nullable=True))


def downgrade() -> None:
    if "content_masters" not in _table_names():
        return
    if "asset_meta" in _column_names("content_masters"):
        op.drop_column("content_masters", "asset_meta")
