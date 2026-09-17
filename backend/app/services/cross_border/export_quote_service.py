# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""FOB/MOQ 出口报价一页 — 绑定产品库（W3 / XF-D2）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.tenant import Tenant
from app.services.foreign_trade.trade_document_service import build_proforma_invoice
from app.services.tenant_product_profile_service import get_tenant_product_profile


def _seller_block(tenant: Tenant, profile: dict[str, Any]) -> dict[str, Any]:
    """实现 sellerblock 的功能。
    
    :param tenant: 参数 tenant（类型: Tenant）
    :param profile: 参数 profile（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    return {
        "name": tenant.name,
        "name_en": profile.get("company_name_en") or tenant.name,
        "address": profile.get("region_label_zh") or "Langfang, Hebei, China",
        "contact": profile.get("contact_phone") or "",
        "email": profile.get("contact_email") or "",
    }


def _pick_product_row(db: Session, product_id: str | None) -> Product | None:
    """实现 pick产品row 的功能。
    
    :param db: 参数 db（类型: Session）
    :param product_id: 参数 product_id（类型: str | None）
    :return: 返回 Product | None 结果
    """
    if not product_id:
        return (
            db.query(Product)
            .filter(Product.is_active.is_(True))
            .order_by(Product.sort_order.asc(), Product.created_at.desc())
            .first()
        )
    return (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.id == product_id)
        .first()
    )


def build_export_quote_onepager(
    db: Session,
    tenant: Tenant,
    *,
    product_id: str | None = None,
    moq: str | None = None,
    unit_price: float | None = None,
    currency: str = "USD",
    delivery_terms: str = "FOB Tianjin",
    payment_terms: str = "30% T/T deposit, 70% before shipment",
    validity_days: int = 15,
    notes_zh: str = "",
) -> dict[str, Any]:
    """实现 构建导出quoteonepager 的功能。
    
    :param db: 参数 db（类型: Session）
    :param tenant: 参数 tenant（类型: Tenant）
    :param product_id: 参数 product_id（类型: str | None）
    :param moq: 参数 moq（类型: str | None）
    :param unit_price: 参数 unit_price（类型: float | None）
    :param currency: 参数 currency（类型: str）
    :param delivery_terms: 参数 delivery_terms（类型: str）
    :param payment_terms: 参数 payment_terms（类型: str）
    :param validity_days: 参数 validity_days（类型: int）
    :param notes_zh: 参数 notes_zh（类型: str）
    :return: 返回 dict[str, Any] 结果
    """
    profile = get_tenant_product_profile(db, str(tenant.id))
    row = _pick_product_row(db, product_id)
    if not row and not profile.get("primary_product"):
        return {
            "ready": False,
            "error": "请先在产品库填写至少 1 个真实产品",
            "route_hint": "/client/products",
        }

    desc_zh = row.name if row else profile.get("primary_product") or ""
    if row:
        desc_en = (row.subtitle or row.description or profile.get("primary_product") or "")[:400]
    else:
        desc_en = (profile.get("primary_product") or "")[:400]
    spec = (row.technical_params if row else None) or profile.get("spec_summary") or ""
    qty = float(moq) if moq and str(moq).replace(".", "", 1).isdigit() else 0
    price = float(unit_price) if unit_price is not None else 0.0
    lines = [
        {
            "description": f"{desc_zh} / {desc_en[:120]}".strip(" /"),
            "product_name": desc_zh,
            "quantity": qty or 0,
            "unit": "m³" if "棉" in desc_zh or "板" in desc_zh else "pcs",
            "unit_price": price,
            "hs_code": "",
        }
    ]
    buyer = {
        "name": "To be confirmed",
        "code": "TBC",
        "country": "",
    }
    doc = build_proforma_invoice(
        seller=_seller_block(tenant, profile),
        buyer=buyer,
        lines=lines,
        currency=currency,
        payment_terms=payment_terms,
        delivery_terms=delivery_terms,
        validity_days=validity_days,
        notes=notes_zh or "Prices subject to final specification confirmation.",
    )
    one_pager_zh = (
        f"【出口报价一页 · {tenant.name}】\n"
        f"产品: {desc_zh}\n"
        f"规格要点: {spec[:200] or '见 PI 附件'}\n"
        f"MOQ: {moq or '待填'}\n"
        f"单价: {currency} {price if price else '待填'}\n"
        f"贸易条款: {delivery_terms}\n"
        f"付款: {payment_terms}\n"
        f"有效期: {validity_days} 天\n"
        "说明: 以上须人工核对后再发买家，勿把示例价当成交价。"
    )
    return {
        "ready": True,
        "product_id": str(row.id) if row else None,
        "product_name_zh": desc_zh,
        "moq": moq,
        "unit_price": price,
        "currency": currency,
        "delivery_terms": delivery_terms,
        "payment_terms": payment_terms,
        "one_pager_zh": one_pager_zh,
        "pi": doc,
        "human_confirm_required": True,
        "honest_note": "未填单价/MOQ 时 PI 仅作模板，不含虚假成交价。",
    }
