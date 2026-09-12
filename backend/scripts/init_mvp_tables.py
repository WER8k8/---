#!/usr/bin/env python3
"""创建 MVP 新增表（content_masters / egress / 列扩展）。"""

import os
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("JWT_SECRET_KEY", "init-mvp-" + "x" * 32)

from app.core.database import Base, engine
from app.models.content_master import ContentMaster
from app.models.egress import BrowserProfile, EgressEndpoint
from app.models.commission_settlement import AgentCommissionSettlement
from app.models.agent_commission_rule import AgentCommissionRule
from app.models.finance_ledger import FinanceLedgerEntry
from app.models.token_ledger import TokenLedgerEntry
from app.models.invoice_application import (
    InvoiceApplication,
    PlatformInvoiceConfig,
    TenantInvoiceProfile,
)


def main() -> None:
    tables = [
        ContentMaster.__table__,
        EgressEndpoint.__table__,
        BrowserProfile.__table__,
        FinanceLedgerEntry.__table__,
        TokenLedgerEntry.__table__,
        AgentCommissionSettlement.__table__,
        AgentCommissionRule.__table__,
        PlatformInvoiceConfig.__table__,
        TenantInvoiceProfile.__table__,
        InvoiceApplication.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    logger.info('OK: MVP tables created (content_masters, egress_endpoints, browser_profiles)')
    logger.info('NOTE: platforms/publish_tasks 新列若已有库需手动 ALTER 或 Alembic 迁移')


if __name__ == "__main__":
    main()
