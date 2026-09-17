# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""T-QA-08 / G4：检测是否配置可用 AI Key（非仅 Mock）。"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings


def _looks_like_key(val: str | None) -> bool:
    """_looks_like_key。

    参数说明：
    :param val: 参数 val
    :return: 返回处理结果。
    """
    v = (val or "").strip()
    if len(v) < 8:
        return False
    low = v.lower()
    for bad in ("your_", "here", "change-me", "sk-xxx", "api-key-here"):
        if bad in low:
            return False
    return True


def configured_ai_providers(db: Session | None = None) -> list[str]:
    """configured_ai_providers。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    found: set[str] = set()
    pairs = (
        ("openai", settings.AI_OPENAI_API_KEY),
        ("anthropic", settings.AI_ANTHROPIC_API_KEY),
        ("gemini", settings.AI_GEMINI_API_KEY),
        ("deepseek", settings.AI_DEEPSEEK_API_KEY),
        ("nvidia", settings.AI_NVIDIA_API_KEY),
    )
    for name, val in pairs:
        if _looks_like_key(val):
            found.add(name)
    if db is not None:
        try:
            from app.models.ai_config import AIModelProvider
            rows = (
                db.query(AIModelProvider)
                .filter(AIModelProvider.is_active.is_(True))
                .all()
            )
            for row in rows:
                if _looks_like_key(row.api_key):
                    found.add((row.provider_type or row.name or "custom").lower())
        except Exception:
            pass
    return sorted(found)


def ai_key_status(db: Session | None = None) -> dict[str, Any]:
    """返回 Key 配置态；不发起外网调用（CI 友好）。"""
    providers = configured_ai_providers(db)
    mvp = settings.MVP_LAUNCH
    env = (settings.ENVIRONMENT or "development").lower()
    real_key = len(providers) > 0
    non_mock_ok = real_key and not (mvp and env == "production")
    return {
        "providers": providers,
        "has_real_key": real_key,
        "mvp_launch": mvp,
        "environment": env,
        "g4_pass": non_mock_ok or (real_key and env != "production"),
        "hint": "生产商用须至少一个 AI Key 且 MVP_LAUNCH=0",
    }


def probe_ubrain_non_mock(db: Session | None = None) -> dict[str, Any]:
    """有 Key 时走引擎路由，确认未强制 Mock（轻量）。"""
    st = ai_key_status(db)
    if not st["has_real_key"]:
        return {**st, "engine_probe": "skipped_no_key"}
    try:
        from app.services.ai_engine import AIEngine
        engine = AIEngine()
        llm = engine._get_llm("general")
        is_mock = llm.__class__.__name__ == "MockLLM"
        engine_ok = not is_mock
        return {
            **st,
            "engine_probe": "mock" if is_mock else "real",
            "current_provider": getattr(engine, "current_provider", None),
            "g4_pass": engine_ok and st["g4_pass"],
        }
    except Exception as exc:
        return {**st, "engine_probe": f"error:{exc}", "g4_pass": False}
