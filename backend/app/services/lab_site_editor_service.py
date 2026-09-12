"""FE-11 站点编辑器试点 — 草稿读写（租户 settings 或用户级文件兜底）"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User

DRAFT_KEY = "site_editor_lab_draft"
_LAB_DIR = Path(__file__).resolve().parents[2] / "data" / "lab" / "site_editor"


def default_draft() -> dict[str, Any]:
    """default_draft。
    :return: 返回处理结果。
    """
    return {
        "title": "优丁独立站",
        "hero": "建材外贸 · AI 营销",
        "locale": "zh-CN",
        "showCta": True,
        "brandName": "",
        "aboutText": "",
        "contactPhone": "",
        "contactEmail": "",
        "ctaLabel": "Get a Quote",
    }


def _safe_settings(raw: str | None) -> dict[str, Any]:
    """_safe_settings。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def get_draft(db: Session, user: User, tenant: Tenant | None) -> dict[str, Any]:
    """get_draft。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    if tenant:
        settings = _safe_settings(tenant.settings)
        draft = settings.get(DRAFT_KEY)
        if isinstance(draft, dict):
            return {**default_draft(), **draft}
        return default_draft()
    path = _LAB_DIR / f"{user.id}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {**default_draft(), **data}
        except (json.JSONDecodeError, OSError):
            pass
    return default_draft()


def save_draft(
    db: Session,
    user: User,
    tenant: Tenant | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """save_draft。

    参数说明：
    :param db: 参数 db
    :param user: 参数 user
    :param tenant: 参数 tenant
    :param payload: 参数 payload
    :return: 返回处理结果。
    """
    merged = {**default_draft(), **payload}
    if tenant:
        settings = _safe_settings(tenant.settings)
        settings[DRAFT_KEY] = merged
        tenant.settings = json.dumps(settings, ensure_ascii=False)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return merged
    _LAB_DIR.mkdir(parents=True, exist_ok=True)
    path = _LAB_DIR / f"{user.id}.json"
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged
