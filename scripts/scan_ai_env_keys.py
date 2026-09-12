#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

try:
    from dotenv import load_dotenv

    for p in [
        BACKEND / "config" / "dev" / ".env",
        BACKEND.parent / ".env",
        BACKEND / ".env",
    ]:
        if p.is_file():
            load_dotenv(p, override=True)
            print("loaded", p)
            break
except ImportError:
    pass

os.environ.setdefault("JWT_SECRET_KEY", "key-scan-" + ("x" * 24))
os.environ.setdefault("SECRET_KEY", os.environ["JWT_SECRET_KEY"])

from app.core.config import settings
from app.services.ai_key_probe import ai_key_status, configured_ai_providers

PLACEHOLDER = ("your_", "here", "change-me", "sk-xxx")


def _looks_real(val: str | None) -> bool:
    v = (val or "").strip()
    if len(v) < 8:
        return False
    low = v.lower()
    return not any(p in low for p in PLACEHOLDER)


checks = {
    "openai": _looks_real(settings.AI_OPENAI_API_KEY),
    "anthropic": _looks_real(settings.AI_ANTHROPIC_API_KEY),
    "gemini": _looks_real(settings.AI_GEMINI_API_KEY),
    "deepseek": _looks_real(settings.AI_DEEPSEEK_API_KEY),
    "nvidia": _looks_real(settings.AI_NVIDIA_API_KEY),
}
print("env_keys", json.dumps(checks))
print("providers", configured_ai_providers())
print("status", json.dumps(ai_key_status(), ensure_ascii=False))
