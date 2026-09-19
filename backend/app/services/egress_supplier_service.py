# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""静态 IP 上游供应商 — 增删改查与切换启用。"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.egress import EgressEndpoint, EgressSupplier

_CODE_RE = re.compile(r"^[a-z][a-z0-9_-]{1,47}$")

_BUILTIN_DEFAULTS: list[dict[str, Any]] = [
    {
        "code": "iproyal",
        "name": "IPRoyal",
        "subtitle": "纯静态住宅 ISP",
        "adapter": "iproyal",
        "ip_type": "static_residential",
        "long_term_fixed": True,
        "description": "长期固定纯静态住宅 IP，支持自动续费，适合养号。",
        "supports_pool_replenish": True,
        "is_builtin": True,
        "sort_order": 0,
        "config_json": {"plan_id": 4, "product_id": 9},
    },
    {
        "code": "manual",
        "name": "手工录入",
        "subtitle": "外采固定静态 IP",
        "adapter": "manual",
        "ip_type": "static_manual",
        "long_term_fixed": True,
        "description": "其它渠道购买的长期固定静态住宅 IP，手工录入平台池。",
        "supports_pool_replenish": False,
        "is_builtin": True,
        "sort_order": 1,
        "config_json": {},
    },
    {
        "code": "asocks",
        "name": "ASocks",
        "subtitle": "按流量住宅（非固定）",
        "adapter": "asocks",
        "ip_type": "residential_rotating",
        "long_term_fixed": False,
        "description": "按流量住宅代理，IP 可能轮换，不建议养号主链路。",
        "supports_pool_replenish": False,
        "is_builtin": True,
        "sort_order": 2,
        "config_json": {},
    },
]


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _normalize_code(raw: str) -> str:
    """_normalize_code。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    code = (raw or "").strip().lower().replace(" ", "-")
    if not _CODE_RE.match(code):
        raise ValueError("供应商代码须为小写字母开头，仅含 a-z、0-9、_、-")
    return code


def _mask_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """_mask_config。

    参数说明：
    :param config: 参数 config
    :return: 返回处理结果。
    """
    cfg = dict(config or {})
    if cfg.get("api_token"):
        cfg["api_token"] = "***"
    if cfg.get("api_key"):
        cfg["api_key"] = "***"
    return cfg


def _supplier_ready(row: EgressSupplier) -> bool:
    """_supplier_ready。

    参数说明：
    :param row: 参数 row
    :return: 返回处理结果。
    """
    cfg = row.config_json if isinstance(row.config_json, dict) else {}
    if row.adapter == "iproyal":
        token = (cfg.get("api_token") or settings.IPROYAL_API_TOKEN or "").strip()
        return bool(token)
    if row.adapter == "asocks":
        key = (cfg.get("api_key") or settings.ASOCKS_API_KEY or "").strip()
        url = (cfg.get("list_url") or settings.ASOCKS_LIST_URL or "").strip()
        return bool(key or url)
    return True


def _pool_stats(db: Session, code: str) -> dict[str, int]:
    """_pool_stats。

    参数说明：
    :param db: 参数 db
    :param code: 参数 code
    :return: 返回处理结果。
    """
    if code == "manual":
        q = db.query(EgressEndpoint).filter(
            ~EgressEndpoint.provider.in_(("iproyal", "asocks", "mock"))
            | EgressEndpoint.provider.is_(None)
        )
    else:
        q = db.query(EgressEndpoint).filter(EgressEndpoint.provider == code)
    total = q.count()
    return {
        "total": total,
        "available": q.filter(EgressEndpoint.slot_status == "available").count(),
        "assigned": q.filter(EgressEndpoint.slot_status == "assigned").count(),
    }


def serialize_supplier(db: Session, row: EgressSupplier) -> dict[str, Any]:
    """serialize_supplier。

    参数说明：
    :param db: 参数 db
    :param row: 参数 row
    :return: 返回处理结果。
    """
    cfg = row.config_json if isinstance(row.config_json, dict) else {}
    return {
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "subtitle": row.subtitle,
        "adapter": row.adapter,
        "ip_type": row.ip_type,
        "long_term_fixed": bool(row.long_term_fixed),
        "description": row.description,
        "config": _mask_config(cfg),
        "supports_pool_replenish": bool(row.supports_pool_replenish),
        "is_active": bool(row.is_active),
        "is_builtin": bool(row.is_builtin),
        "enabled": bool(row.enabled),
        "sort_order": row.sort_order,
        "ready": _supplier_ready(row),
        "pool": _pool_stats(db, row.code),
    }


def apply_supplier_runtime(row: EgressSupplier) -> None:
    """将启用供应商同步到运行时 settings（JIT / 补池）。"""
    settings.EGRESS_PROVIDER = (row.adapter or "manual").strip().lower()
    cfg = row.config_json if isinstance(row.config_json, dict) else {}
    if row.adapter == "iproyal":
        token = (cfg.get("api_token") or "").strip()
        if token:
            settings.IPROYAL_API_TOKEN = token
        if cfg.get("plan_id") is not None:
            settings.IPROYAL_PLAN_ID = int(cfg["plan_id"])
        if cfg.get("product_id") is not None:
            settings.IPROYAL_PRODUCT_ID = int(cfg["product_id"])
        if cfg.get("batch_size") is not None:
            settings.IPROYAL_BATCH_SIZE = int(cfg["batch_size"])
        if cfg.get("pool_low_watermark") is not None:
            settings.IPROYAL_POOL_LOW_WATERMARK = int(cfg["pool_low_watermark"])


def _sync_env_credentials(db: Session) -> None:
    """将 .env 中的 Token 写入供应商配置（用户已提供但未入库时）。"""
    iproyal = (
        db.query(EgressSupplier).filter(EgressSupplier.code == "iproyal").first()
    )
    if iproyal:
        cfg = dict(iproyal.config_json or {})
        env_token = (settings.IPROYAL_API_TOKEN or "").strip()
        if env_token and not (cfg.get("api_token") or "").strip():
            cfg["api_token"] = env_token
            iproyal.config_json = cfg
    asocks = db.query(EgressSupplier).filter(EgressSupplier.code == "asocks").first()
    if asocks:
        cfg = dict(asocks.config_json or {})
        env_key = (settings.ASOCKS_API_KEY or "").strip()
        if env_key and not (cfg.get("api_key") or "").strip():
            cfg["api_key"] = env_key
            asocks.config_json = cfg
        env_url = (settings.ASOCKS_LIST_URL or "").strip()
        if env_url and not (cfg.get("list_url") or "").strip():
            cfg["list_url"] = env_url
            asocks.config_json = cfg
    db.flush()


def seed_default_suppliers(db: Session) -> int:
    """幂等写入内置供应商；若无启用项则启用 iproyal 或 manual。"""
    created = 0
    for item in _BUILTIN_DEFAULTS:
        exists = (
            db.query(EgressSupplier).filter(EgressSupplier.code == item["code"]).first()
        )
        if exists:
            continue
        db.add(
            EgressSupplier(
                id=str(uuid.uuid4()),
                is_active=False,
                enabled=True,
                **item,
            )
        )
        created += 1
    db.flush()
    _sync_env_credentials(db)
    if not db.query(EgressSupplier).filter(EgressSupplier.is_active.is_(True)).first():
        preferred = (settings.EGRESS_PROVIDER or "manual").strip().lower()
        candidates = [
            preferred,
            "iproyal" if preferred != "manual" else "manual",
            "manual",
        ]
        row = None
        for code in candidates:
            row = (
                db.query(EgressSupplier)
                .filter(EgressSupplier.code == code, EgressSupplier.enabled.is_(True))
                .first()
            )
            if row and (row.adapter != "iproyal" or _supplier_ready(row)):
                break
            row = None
        if not row:
            row = (
                db.query(EgressSupplier)
                .filter(EgressSupplier.enabled.is_(True))
                .order_by(EgressSupplier.sort_order.asc())
                .first()
            )
        if row:
            try:
                activate_supplier(db, str(row.id))
            except ValueError:
                manual = (
                    db.query(EgressSupplier)
                    .filter(EgressSupplier.code == "manual")
                    .first()
                )
                if manual:
                    manual.is_active = True
                    apply_supplier_runtime(manual)
                    db.commit()
    return created


def list_suppliers(db: Session) -> list[dict[str, Any]]:
    """list_suppliers。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    seed_default_suppliers(db)
    _sync_env_credentials(db)
    rows = (
        db.query(EgressSupplier)
        .filter(EgressSupplier.enabled.is_(True))
        .order_by(EgressSupplier.sort_order.asc(), EgressSupplier.created_at.asc())
        .all()
    )
    return [serialize_supplier(db, r) for r in rows]


def get_active_supplier(db: Session) -> EgressSupplier | None:
    """get_active_supplier。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    seed_default_suppliers(db)
    return (
        db.query(EgressSupplier)
        .filter(EgressSupplier.is_active.is_(True), EgressSupplier.enabled.is_(True))
        .first()
    )


def create_supplier(
    db: Session,
    *,
    code: str,
    name: str,
    adapter: str = "manual",
    subtitle: str | None = None,
    ip_type: str = "static_residential",
    long_term_fixed: bool = True,
    description: str | None = None,
    supports_pool_replenish: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """create_supplier。

    参数说明：
    :param db: 参数 db
    :param code: 参数 code
    :param name: 参数 name
    :param adapter: 参数 adapter
    :param subtitle: 参数 subtitle
    :param ip_type: 参数 ip_type
    :param long_term_fixed: 参数 long_term_fixed
    :param description: 参数 description
    :param supports_pool_replenish: 参数 supports_pool_replenish
    :param config: 参数 config
    :return: 返回处理结果。
    """
    norm = _normalize_code(code)
    if db.query(EgressSupplier).filter(EgressSupplier.code == norm).first():
        raise ValueError(f"供应商代码已存在: {norm}")
    adapter = (adapter or "manual").strip().lower()
    if adapter not in ("manual", "iproyal", "asocks"):
        raise ValueError("adapter 仅支持 manual / iproyal / asocks")
    row = EgressSupplier(
        id=str(uuid.uuid4()),
        code=norm,
        name=(name or norm).strip(),
        subtitle=subtitle,
        adapter=adapter,
        ip_type=ip_type,
        long_term_fixed=long_term_fixed,
        description=description,
        supports_pool_replenish=supports_pool_replenish or adapter == "iproyal",
        config_json=config or {},
        is_builtin=False,
        is_active=False,
        enabled=True,
        sort_order=100 + db.query(EgressSupplier).count(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_supplier(db, row)


def update_supplier(
    db: Session,
    supplier_id: str,
    *,
    name: str | None = None,
    subtitle: str | None = None,
    adapter: str | None = None,
    ip_type: str | None = None,
    long_term_fixed: bool | None = None,
    description: str | None = None,
    supports_pool_replenish: bool | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """update_supplier。

    参数说明：
    :param db: 参数 db
    :param supplier_id: 参数 supplier_id
    :param name: 参数 name
    :param subtitle: 参数 subtitle
    :param adapter: 参数 adapter
    :param ip_type: 参数 ip_type
    :param long_term_fixed: 参数 long_term_fixed
    :param description: 参数 description
    :param supports_pool_replenish: 参数 supports_pool_replenish
    :param config: 参数 config
    :return: 返回处理结果。
    """
    row = db.query(EgressSupplier).filter(EgressSupplier.id == supplier_id).first()
    if not row or not row.enabled:
        raise ValueError("供应商不存在")
    if name is not None:
        row.name = name.strip()
    if subtitle is not None:
        row.subtitle = subtitle
    if adapter is not None:
        ad = adapter.strip().lower()
        if ad not in ("manual", "iproyal", "asocks"):
            raise ValueError("adapter 仅支持 manual / iproyal / asocks")
        row.adapter = ad
    if ip_type is not None:
        row.ip_type = ip_type
    if long_term_fixed is not None:
        row.long_term_fixed = long_term_fixed
    if description is not None:
        row.description = description
    if supports_pool_replenish is not None:
        row.supports_pool_replenish = supports_pool_replenish
    if config is not None:
        merged = dict(row.config_json or {})
        for k, v in config.items():
            if v is None or v == "":
                merged.pop(k, None)
            elif k in ("api_token", "api_key") and v == "***":
                continue
            else:
                merged[k] = v
        row.config_json = merged
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    if row.is_active:
        apply_supplier_runtime(row)
    return serialize_supplier(db, row)


def delete_supplier(db: Session, supplier_id: str) -> None:
    """delete_supplier。

    参数说明：
    :param db: 参数 db
    :param supplier_id: 参数 supplier_id
    :return: 返回处理结果。
    """
    row = db.query(EgressSupplier).filter(EgressSupplier.id == supplier_id).first()
    if not row or not row.enabled:
        raise ValueError("供应商不存在")
    if row.is_active:
        raise ValueError("当前启用的供应商不可删除，请先切换到其它供应商")
    used = (
        db.query(EgressEndpoint)
        .filter(EgressEndpoint.provider == row.code)
        .count()
    )
    if used:
        raise ValueError(f"该供应商下仍有 {used} 个 IP 槽位，请先释放或迁移后再删除")
    if row.is_builtin:
        row.enabled = False
        row.is_active = False
    else:
        db.delete(row)
    db.commit()


def activate_supplier(db: Session, supplier_id: str) -> dict[str, Any]:
    """activate_supplier。

    参数说明：
    :param db: 参数 db
    :param supplier_id: 参数 supplier_id
    :return: 返回处理结果。
    """
    row = db.query(EgressSupplier).filter(EgressSupplier.id == supplier_id).first()
    if not row or not row.enabled:
        raise ValueError("供应商不存在")
    if row.adapter == "iproyal" and not _supplier_ready(row):
        raise ValueError("IPRoyal 供应商未配置 API Token，请先编辑保存")
    for other in db.query(EgressSupplier).filter(EgressSupplier.is_active.is_(True)).all():
        other.is_active = False
    row.is_active = True
    row.updated_at = _utcnow()
    db.commit()
    apply_supplier_runtime(row)
    db.refresh(row)
    return serialize_supplier(db, row)


def build_providers_page_payload(db: Session) -> dict[str, Any]:
    """build_providers_page_payload。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    suppliers = list_suppliers(db)
    # 每供应商补 has_token/ready，便于 UI 诚实展示「自动采购是否开通」
    for s in suppliers:
        adapter = str(s.get("adapter") or "")
        if adapter == "iproyal":
            has = bool((settings.IPROYAL_API_TOKEN or "").strip())
        elif adapter == "asocks":
            has = bool((settings.ASOCKS_API_KEY or "").strip() or (settings.ASOCKS_LIST_URL or "").strip())
        else:
            has = True  # manual 不依赖上游 Token
        s["has_token"] = has
        s["ready"] = bool(s.get("is_active")) and has if adapter != "manual" else bool(s.get("is_active"))
        if adapter == "iproyal" and not has:
            s["not_ready_reason"] = "IPROYAL_API_TOKEN 未配置 — 仅可手工录入，自动采购未开通"
        elif adapter == "asocks" and not has:
            s["not_ready_reason"] = "ASOCKS_API_KEY / ASOCKS_LIST_URL 未配置"
        else:
            s["not_ready_reason"] = None

    active = next((s for s in suppliers if s.get("is_active")), None)
    auto_ready = any(s.get("adapter") in ("iproyal", "asocks") and s.get("has_token") and s.get("is_active") for s in suppliers)
    return {
        "active_provider": active.get("code") if active else None,
        "active_supplier_id": active.get("id") if active else None,
        "active_label": active.get("name") if active else None,
        "long_term_fixed": bool(active.get("long_term_fixed")) if active else False,
        "auto_purchase_ready": auto_ready,
        "mode_hint": (
            "自动采购已开通"
            if auto_ready
            else "当前手工录入模式：IPROYAL/ASocks Token 未配置，自动采购未开通（非故障）"
        ),
        "checklist": "docs/ops/external-integration-keys-checklist.md",
        "providers": suppliers,
        "iproyal_config": {
            "plan_id": settings.IPROYAL_PLAN_ID,
            "product_id": settings.IPROYAL_PRODUCT_ID,
            "batch_size": settings.IPROYAL_BATCH_SIZE,
            "pool_low_watermark": settings.IPROYAL_POOL_LOW_WATERMARK,
            "auto_renew_days": settings.IPROYAL_AUTO_RENEW_DAYS,
            "has_token": bool((settings.IPROYAL_API_TOKEN or "").strip()),
        },
        "asocks_config": {
            "has_api_key": bool((settings.ASOCKS_API_KEY or "").strip()),
            "has_list_url": bool((settings.ASOCKS_LIST_URL or "").strip()),
        },
    }
