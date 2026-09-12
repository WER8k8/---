"""租户官网 site_content 持久化。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def _safe_json_loads(raw: str | None) -> dict[str, Any]:
    """_safe_json_loads。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def persist_tenant_site_content(
    db: Session,
    tenant: Tenant,
    site_content: dict[str, Any],
    product_name: str,
) -> None:
    """写入 brand.site_content 并标记 onboarding.site_built。"""
    from app.services.jtbd_site_service import apply_jtbd_site_pass
    site_content = apply_jtbd_site_pass(site_content)
    existing = _safe_json_loads(tenant.settings)
    brand = existing.get("brand") if isinstance(existing.get("brand"), dict) else {}
    brand["site_content"] = site_content
    from app.services.site_content_bridge import sync_site_content_to_brand
    existing["brand"] = sync_site_content_to_brand(brand, site_content)
    onboarding = existing.get("onboarding") if isinstance(existing.get("onboarding"), dict) else {}
    onboarding["site_built"] = True
    onboarding["primary_product"] = product_name
    onboarding["site_built_at"] = datetime.now(timezone.utc).isoformat()
    onboarding["site_builder"] = "hermes_ai_site_builder"
    from app.services.site_l_pro_service import validate_l_pro_publish_gate
    gate = validate_l_pro_publish_gate(site_content)
    onboarding["l_pro_publish_ready"] = bool(gate.get("publish_ready"))
    onboarding["l_pro_publish_gate"] = gate
    existing["onboarding"] = onboarding
    tenant.settings = json.dumps(existing, ensure_ascii=False)
    tenant.updated_at = datetime.now(timezone.utc)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    try:
        from app.services.tenant_product_profile_service import build_and_persist_product_profile
        build_and_persist_product_profile(
            db,
            tenant,
            product_hint=product_name,
            location_hint=onboarding.get("location_hint"),
            run_web_research=False,
        )
    except Exception:
        pass
