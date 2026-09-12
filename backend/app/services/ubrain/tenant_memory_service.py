"""租户副驾记忆 — Accio「越用越智能」底座。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.ubrain_accio import UbrainTenantMemory

_DEFAULT: dict[str, Any] = {
    "product_category": "保温建材",
    "preferred_regions": ["中东", "东南亚"],
    "letter_language": "bilingual",  # zh | en | bilingual
    "tone": "专业、简洁",
    "brand_name": "",
    "site_cta": "独立域询盘表单或电话",
    "tool_stats": {},
    "last_export_feasibility": {},
    "icp_value_props": "",
    "icp_certifications": [],
    "website_url": "",
}


def _parse(row: UbrainTenantMemory | None) -> dict[str, Any]:
    """_parse。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    if not row:
        return dict(_DEFAULT)
    try:
        data = json.loads(row.memory_json or "{}")
    except json.JSONDecodeError:
        data = {}
    out = dict(_DEFAULT)
    out.update(data)
    return out


def resolve_company_name(
    db: Session,
    tenant_id: str,
    mem: dict[str, Any] | None = None,
) -> str:
    """客户对外展示名：记忆 brand_name → 租户 settings.brand → tenant.name。"""
    if mem is None:
        row = (
            db.query(UbrainTenantMemory)
            .filter(UbrainTenantMemory.tenant_id == tenant_id)
            .first()
        )
        mem = _parse(row)

    for key in ("brand_name", "company_name"):
        val = str(mem.get(key) or "").strip()
        if val:
            return val

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return "您的公司"

    if tenant.settings:
        try:
            brand = json.loads(tenant.settings).get("brand") or {}
            for key in ("company_name", "site_title"):
                val = str(brand.get(key) or "").strip()
                if val:
                    return val
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return str(tenant.name or "您的公司").strip() or "您的公司"


def get_memory(db: Session, tenant_id: str) -> dict[str, Any]:
    """get_memory。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    row = (
        db.query(UbrainTenantMemory)
        .filter(UbrainTenantMemory.tenant_id == tenant_id)
        .first()
    )
    mem = _parse(row)
    mem["tool_use_count"] = row.tool_use_count if row else 0
    resolved = resolve_company_name(db, tenant_id, mem)
    if not str(mem.get("brand_name") or "").strip() and resolved not in ("", "您的公司"):
        if row is None:
            row = UbrainTenantMemory(tenant_id=tenant_id, memory_json="{}", tool_use_count=0)
            db.add(row)
        current = _parse(row)
        current["brand_name"] = resolved
        row.memory_json = json.dumps(
            {k: current[k] for k in _DEFAULT},
            ensure_ascii=False,
        )
        db.commit()
        mem["brand_name"] = resolved
    mem["company_name"] = resolved
    return mem


def merge_memory(db: Session, tenant_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """merge_memory。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param patch: 参数 patch
    :return: 返回处理结果。
    """
    row = (
        db.query(UbrainTenantMemory)
        .filter(UbrainTenantMemory.tenant_id == tenant_id)
        .first()
    )
    current = _parse(row)
    for key, val in patch.items():
        if val is None:
            continue
        if key == "preferred_regions" and isinstance(val, list):
            current["preferred_regions"] = [str(x) for x in val][:8]
        elif key == "tool_stats" and isinstance(val, dict):
            current.setdefault("tool_stats", {}).update(val)
        elif key == "last_export_feasibility" and isinstance(val, dict):
            current["last_export_feasibility"] = val
        else:
            current[key] = val
    if row is None:
        row = UbrainTenantMemory(tenant_id=tenant_id, memory_json="{}", tool_use_count=0)
        db.add(row)
    row.memory_json = json.dumps(current, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    out = _parse(row)
    out["tool_use_count"] = row.tool_use_count
    out["company_name"] = resolve_company_name(db, tenant_id, out)
    return out


def record_tool_use(
    db: Session,
    tenant_id: str,
    tool: str,
    *,
    context_patch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """record_tool_use。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param tool: 参数 tool
    :param context_patch: 参数 context_patch
    :return: 返回处理结果。
    """
    row = (
        db.query(UbrainTenantMemory)
        .filter(UbrainTenantMemory.tenant_id == tenant_id)
        .first()
    )
    if row is None:
        row = UbrainTenantMemory(tenant_id=tenant_id, memory_json="{}", tool_use_count=0)
        db.add(row)
    current = _parse(row)
    stats = current.setdefault("tool_stats", {})
    stats[tool] = int(stats.get(tool, 0)) + 1
    if context_patch:
        for k, v in context_patch.items():
            if v is None:
                continue
            if k == "last_export_feasibility" and isinstance(v, dict):
                current["last_export_feasibility"] = v
            elif k in ("icp_value_props", "icp_certifications", "website_url") and v:
                current[k] = v
            elif k in _DEFAULT:
                current[k] = v
    row.memory_json = json.dumps(current, ensure_ascii=False)
    row.tool_use_count = (row.tool_use_count or 0) + 1
    db.commit()
    db.refresh(row)
    out = _parse(row)
    out["tool_use_count"] = row.tool_use_count
    out["company_name"] = resolve_company_name(db, tenant_id, out)
    return out
