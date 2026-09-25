"""120 — W1 获客主链收敛：email_outreachs.prospect_id + buyer_prospect_leads 候选三值 + opportunities.stage 归一

背景（团队任务 #2 · W1；契约 ``docs/获客闭环唯一数据契约-2026-09-25.md``）：
- N-2：``email_tracking_service.py:117/164/194`` 读写 ``EmailOutreach.prospect_id``，
  但模型/物理库均无该列 → 必然 AttributeError/SQL 错误。
- P0-5：``BuyerProspectLead`` 缺 ``candidate_kind`` / ``verified`` / ``evidence_status``，
  画像模板候选与真实抓取候选无法区分，可能被误送入外发队列。
- P0-8 / N-3：存量 ``opportunities.stage`` 存在 ``prospecting`` / ``Quotation`` 等
  非法自由串，须回填到唯一词表 ``app.constants.crm_stages.STAGE_ORDER``。

设计：
- 全部操作**幂等**（先 inspect 列/索引是否存在），与 119 同风格，兼容历史 bootstrap 建表。
- 新增列一律带 ``server_default``（存量行非空）。
- ``opportunities.stage`` 归一为**单向数据规范化**，downgrade 不反向还原（避免把
  合法数据误改回脏值）。

依赖：down_revision = 119_align_provenance_metadata_domestic_inquiries
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "120_w1_acquisition_backpoints"
down_revision: Union[str, None] = "119_align_provenance_metadata_domestic_inquiries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 唯一合法 CRM 阶段（与 app.constants.crm_stages.STAGE_ORDER 保持一致）
_LEGAL_STAGES = (
    "Lead", "Qualified", "Contacted", "Engaged",
    "RFQ", "Quote", "Negotiation", "Won", "Lost",
)

# 遗留 / 别名 → 合法阶段
_STAGE_BACKFILL: dict[str, str] = {
    "new": "Lead",
    "prospecting": "Lead",
    "lead": "Lead",
    "qualification": "Qualified",
    "qualified": "Qualified",
    "needs_analysis": "Engaged",
    "engaged": "Engaged",
    "quotation": "Quote",
    "proposal": "Quote",
    "quoted": "Quote",
    "negotiated": "Negotiation",
    "won": "Won",
    "lost": "Lost",
}


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _index_names(table: str) -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    tables = _table_names()

    # ── 1) email_outreachs.prospect_id（N-2）──────────────────────────────
    if "email_outreachs" in tables:
        cols = _columns("email_outreachs")
        if "prospect_id" not in cols:
            op.add_column(
                "email_outreachs",
                sa.Column("prospect_id", postgresql.UUID(as_uuid=False), nullable=True),
            )
        if "ix_email_outreachs_prospect_id" not in _index_names("email_outreachs"):
            op.create_index(
                "ix_email_outreachs_prospect_id", "email_outreachs", ["prospect_id"]
            )

    # ── 2) buyer_prospect_leads 候选三值（P0-5）──────────────────────────
    if "buyer_prospect_leads" in tables:
        cols = _columns("buyer_prospect_leads")
        added = False
        if "candidate_kind" not in cols:
            op.add_column(
                "buyer_prospect_leads",
                sa.Column(
                    "candidate_kind", sa.String(20), nullable=False,
                    server_default="archetype",
                ),
            )
            added = True
        if "verified" not in cols:
            op.add_column(
                "buyer_prospect_leads",
                sa.Column(
                    "verified", sa.Boolean(), nullable=False,
                    server_default=sa.text("false"),
                ),
            )
            added = True
        if "evidence_status" not in cols:
            op.add_column(
                "buyer_prospect_leads",
                sa.Column(
                    "evidence_status", sa.String(20), nullable=False,
                    server_default="missing",
                ),
            )
            added = True
        if "candidate_kind" not in _index_names("buyer_prospect_leads"):
            try:
                op.create_index(
                    "ix_buyer_prospect_leads_candidate_kind",
                    "buyer_prospect_leads", ["candidate_kind"],
                )
            except Exception:  # noqa: BLE001
                pass
        if added:
            # 存量回填（尽力）：find_buyers/NULL → archetype；其余（sidecar 抓取）→ scraped。
            # evidence_status：notes 含 "evidence=" 的抓取候选 → present，否则 missing。
            op.execute(
                sa.text(
                    """
                    UPDATE buyer_prospect_leads
                    SET candidate_kind = CASE
                            WHEN source_tool IS NULL OR source_tool = 'find_buyers'
                            THEN 'archetype' ELSE 'scraped' END,
                        evidence_status = CASE
                            WHEN source_tool IS NOT NULL
                                 AND source_tool <> 'find_buyers'
                                 AND notes LIKE '%evidence=%'
                            THEN 'present' ELSE 'missing' END
                    """
                )
            )

    # ── 3) opportunities.stage 归一（P0-8 / N-3）─────────────────────────
    if "opportunities" in tables:
        for legacy, canonical in _STAGE_BACKFILL.items():
            op.execute(
                sa.text(
                    "UPDATE opportunities SET stage = :canonical "
                    "WHERE lower(stage) = :legacy"
                ).bindparams(canonical=canonical, legacy=legacy)
            )
        # 兜底：任何不在合法集内的值（含 NULL）→ 'Lead'
        legal_list = ", ".join(f"'{s}'" for s in _LEGAL_STAGES)
        op.execute(
            f"UPDATE opportunities SET stage = 'Lead' "
            f"WHERE stage IS NULL OR stage NOT IN ({legal_list})"
        )


def downgrade() -> None:
    """回滚结构性变更。

    注意：``opportunities.stage`` 的归一为**单向数据规范化**（把 ``prospecting`` 等
    脏值改成合法值），downgrade **不**反向还原——反向会把合法数据改回脏值，造成更大破坏。
    """
    tables = _table_names()

    if "email_outreachs" in tables:
        if "ix_email_outreachs_prospect_id" in _index_names("email_outreachs"):
            op.drop_index("ix_email_outreachs_prospect_id", table_name="email_outreachs")
        if "prospect_id" in _columns("email_outreachs"):
            op.drop_column("email_outreachs", "prospect_id")

    if "buyer_prospect_leads" in tables:
        idx = _index_names("buyer_prospect_leads")
        if "ix_buyer_prospect_leads_candidate_kind" in idx:
            op.drop_index(
                "ix_buyer_prospect_leads_candidate_kind",
                table_name="buyer_prospect_leads",
            )
        cols = _columns("buyer_prospect_leads")
        for col in ("evidence_status", "verified", "candidate_kind"):
            if col in cols:
                op.drop_column("buyer_prospect_leads", col)
