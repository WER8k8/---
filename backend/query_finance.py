import logging
import os
os.environ["SECRET_KEY"] = "dev_secret_key_12345678901234567890123456789012"
os.environ["JWT_SECRET_KEY"] = "dev_jwt_key_12345678901234567890123456789012"
os.environ["REDIS_ENABLED"] = "false"
os.environ["ENV"] = "development"

from app.db.session import SessionLocal
from app.models.finance_ledger import FinanceLedgerEntry

logger = logging.getLogger(__name__)

db = SessionLocal()
logger.info('FinanceLedgerEntry count: %s', db.query(FinanceLedgerEntry).count())
entries = db.query(FinanceLedgerEntry).all()
logger.info('Entries:')
for e in entries:
    logger.info('  %s: %s cents, tenant=%s, category=%s', e.entry_type, e.amount_cents, e.tenant_id, e.category)
