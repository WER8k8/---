# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ECC SOP Resolver: resolve `sop_ref` URIs to skill content.

The sop_ref format is `ecc://<skill_code>/<action>`.
Resolution strategy:
1. Look up the skill in the skills DB by matching scene/skill_code
2. If found, return the SKILL.md content (SOP body)
3. If not found, return a graceful fallback with guidance

This is consumed by executors via ExecutorContext.sop_ref (J.2).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def resolve_sop_ref(sop_ref: str | None, db=None) -> dict[str, Any]:
    """Resolve an `ecc://...` SOP reference to content + metadata.

    Args:
        sop_ref: e.g. "ecc://ai-seo/optimize"
        db: optional SQLAlchemy session for DB lookup

    Returns:
        {
            "sop_ref": str,
            "resolved": bool,
            "skill_code": str | None,
            "content": str | None,
            "fallback": bool,
            "note": str,
        }
    """
    if not sop_ref:
        return {"sop_ref": None, "resolved": False, "fallback": True, "note": "no sop_ref provided"}

    # Parse the URI: ecc://<skill_code>/<action>
    parts = sop_ref.replace("ecc://", "").split("/", 1)
    skill_code = parts[0] if parts and parts[0] else ""
    action = parts[1] if len(parts) > 1 else ""

    # Try DB lookup via skills table
    if db and skill_code:
        try:
            from app.models.skill import Skill
            skill = (
                db.query(Skill)
                .filter(Skill.code == skill_code, Skill.is_active.is_(True))
                .first()
            )
            if skill:
                content = skill.content or skill.description or ""
                return {
                    "sop_ref": sop_ref,
                    "resolved": True,
                    "skill_code": skill_code,
                    "action": action,
                    "content": content,
                    "fallback": False,
                    "note": f"resolved from skills table (id={skill.id})",
                }
        except Exception as exc:  # noqa: BLE001
            logger.debug("sop_ref DB lookup failed for %s: %s", sop_ref, exc)

    # Try skill_service match_skill
    if db:
        try:
            from app.services.registry.skill_service import match_skill
            matched = match_skill(db, scene_type=skill_code)
            if matched:
                content = getattr(matched, "content") or getattr(matched, "body") or str(matched)
                return {
                    "sop_ref": sop_ref,
                    "resolved": True,
                    "skill_code": skill_code,
                    "action": action,
                    "content": content,
                    "fallback": False,
                    "note": "resolved via skill_service.match_skill",
                }
        except Exception as exc:  # noqa: BLE001
            logger.debug("sop_ref skill_service lookup failed: %s", exc)

    # Graceful fallback
    return {
        "sop_ref": sop_ref,
        "resolved": False,
        "skill_code": skill_code or None,
        "action": action or None,
        "content": None,
        "fallback": True,
        "note": f"sop_ref '{sop_ref}' not resolved; executor should proceed with default behavior",
    }
