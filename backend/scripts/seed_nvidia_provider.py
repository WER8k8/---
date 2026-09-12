"""Seed NVIDIA NIM provider and per-scenario model mappings."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / "config" / "dev" / ".env", override=True)
os.environ.setdefault("DATABASE_URL", "sqlite:///./youding_dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "dev-" + "x" * 28)
os.environ.setdefault("MVP_LAUNCH", "1")

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.ai_config import AIModelProvider
from app.services.nvidia_scenario_service import save_scenario_mappings


def main() -> int:
    api_key = (os.getenv("AI_NVIDIA_API_KEY") or "").strip()
    base_url = (os.getenv("AI_NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1").strip()
    default_model = settings.AI_NVIDIA_MODELS.get("general", "meta/llama-3.1-70b-instruct")

    if not api_key:
        logger.info('AI_NVIDIA_API_KEY missing in config/dev/.env')
        return 1

    db = SessionLocal()
    try:
        provider = (
            db.query(AIModelProvider)
            .filter(AIModelProvider.provider_type == "nvidia")
            .first()
        )
        if provider is None:
            provider = AIModelProvider(
                id=str(uuid.uuid4()),
                name="NVIDIA NIM",
                provider_type="nvidia",
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                is_active=True,
                is_default=True,
                description="NVIDIA NIM via integrate.api.nvidia.com",
            )
            db.add(provider)
            db.commit()
            logger.info('Created NVIDIA provider')
        else:
            provider.api_key = api_key
            provider.base_url = base_url
            provider.default_model = default_model
            provider.is_active = True
            provider.is_default = True
            db.commit()
            logger.info('Updated NVIDIA provider')

        mappings = save_scenario_mappings(db, dict(settings.AI_NVIDIA_MODELS))
        logger.info('Seeded {len(mappings)} scenario mappings', len(mappings))
        for k, v in sorted(mappings.items()):
            logger.info('  {k}: {v}', k, v)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
