"""Create GEO tables script

import logging

logger = logging.getLogger(__name__)

This script creates the GEO-related tables in the UJ database.
Run this script to initialize the GEO engine tables.
"""

from app.core.database import engine, Base
from app.models.geo_sourcechain_models import (
    MaterialSpec, ContentChunk, SERPSnapshot,
    LeadInquiry, ReleaseGuard
)
from app.models.geo_alert_db_models import (
    GEOAlertRule, GEOAlert, GEOAlertHistory
)


def create_geo_tables():
    """Create all GEO tables"""
    logger.info('Creating GEO tables...')
    
    # Create tables (only if they don't exist)
    tables_to_create = [
        MaterialSpec.__table__,
        ContentChunk.__table__,
        SERPSnapshot.__table__,
        LeadInquiry.__table__,
        ReleaseGuard.__table__,
        GEOAlertRule.__table__,
        GEOAlert.__table__,
        GEOAlertHistory.__table__,
    ]
    
    Base.metadata.create_all(engine, tables=tables_to_create)
    logger.info('GEO tables created successfully!')


if __name__ == "__main__":
    create_geo_tables()
