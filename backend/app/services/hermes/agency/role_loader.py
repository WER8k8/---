# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""agency-orchestrator 角色库加载 — 产品内嵌 agency-agents 中文专家人格。"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import json

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
_DEFAULT_ROLES_DIR = _DATA_ROOT / "agency_roles"
_MANIFEST_PATH = _DATA_ROOT / "agency_manifest.json"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def resolve_roles_dir() -> Path:
    """resolve_roles_dir。
    :return: 返回处理结果。
    """
    try:
        from app.core.config import settings
        custom = getattr(settings, "AGENCY_ROLES_DIR", None)
        if custom:
            p = Path(str(custom))
            if p.is_dir():
                return p
    except Exception:
        pass
    return _DEFAULT_ROLES_DIR


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """_parse_frontmatter。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    body = text[m.end() :]
    return meta, body


@lru_cache(maxsize=256)
def load_role(role_id: str) -> dict[str, Any] | None:
    """role_id 形如 marketing/marketing-seo-specialist"""
    rid = (role_id or "").strip().strip("/")
    if not rid:
        return None
    path = resolve_roles_dir() / f"{rid}.md"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(raw)
    trimmed = body[:3200]
    return {
        "role_id": rid,
        "name": meta.get("name") or rid.split("/")[-1],
        "description": meta.get("description") or "",
        "emoji": meta.get("emoji") or "",
        "system_prompt": (
            f"你是「{meta.get('name') or rid}」专家角色。\n"
            f"{meta.get('description') or ''}\n\n"
            f"{trimmed}\n\n"
            "输出要求：用中文（除非任务明确要求英文）；结构清晰；面向 B2B 建材出口与国内平台运营场景。"
        ),
        "path": str(path),
    }


def list_roles(*, category: str | None = None) -> list[dict[str, Any]]:
    """list_roles。

    参数说明：
    :param category: 参数 category
    :return: 返回处理结果。
    """
    root = resolve_roles_dir()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root).as_posix()
        role_id = rel[:-3] if rel.endswith(".md") else rel
        if category and not role_id.startswith(f"{category}/"):
            continue
        meta = load_role(role_id)
        if meta:
            rows.append(
                {
                    "role_id": role_id,
                    "name": meta.get("name"),
                    "description": meta.get("description"),
                    "emoji": meta.get("emoji"),
                }
            )
    return rows


def roles_meta() -> dict[str, Any]:
    """roles_meta。
    :return: 返回处理结果。
    """
    roles = list_roles()
    cats: dict[str, int] = {}
    for r in roles:
        cat = r["role_id"].split("/")[0] if "/" in r["role_id"] else "other"
        cats[cat] = cats.get(cat, 0) + 1
    manifest: dict[str, Any] = {}
    if _MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            manifest = {}
    return {
        "roles_dir": str(resolve_roles_dir()),
        "role_count": len(roles),
        "categories": cats,
        "source": "agency-orchestrator / agency-agents-zh",
        "sync_manifest": manifest,
    }


def resolve_persona_ref(persona_ref: str | None, category: str | None = None) -> dict[str, Any] | None:
    """P1-9: runtime persona resolution for TaskNode.persona_ref.

    persona_ref 为 None / 查不到时返回 None（并记录日志），禁止编造默认 persona（不假交付）。
    返回 load_role() 的结果 dict（含 system_prompt）或 None。
    """
    rid = (persona_ref or "").strip()
    if not rid:
        return None
    role = load_role(rid)
    if role is None:
        import logging
        logging.getLogger(__name__).warning(
            "resolve_persona_ref: persona_ref=%r 未在 AgencyZH roles 目录找到，按 None 处理（不编造）", rid
        )
        return None
    return role
