"""形式发票 PI / 报价单 — 改编自 smart-trade-ai 商务文档能力（Markdown 结构化输出）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_proforma_invoice(
    *,
    seller: dict[str, Any],
    buyer: dict[str, Any],
    lines: list[dict[str, Any]],
    currency: str = "USD",
    payment_terms: str = "30% deposit, 70% before shipment",
    delivery_terms: str = "FOB",
    validity_days: int = 15,
    notes: str = "",
) -> dict[str, Any]:
    """生成 PI 结构化包（可导出 PDF/DOCX 由前端或后续 P1 处理）。"""
    subtotal = 0.0
    normalized_lines: list[dict[str, Any]] = []
    for i, row in enumerate(lines, start=1):
        qty = float(row.get("quantity") or 0)
        price = float(row.get("unit_price") or 0)
        amount = round(qty * price, 2)
        subtotal += amount
        normalized_lines.append(
            {
                "line_no": i,
                "description": row.get("description") or row.get("product_name") or "",
                "hs_code": row.get("hs_code"),
                "quantity": qty,
                "unit": row.get("unit") or "pcs",
                "unit_price": price,
                "amount": amount,
                "currency": currency,
            }
        )

    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pi_no = f"PI-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{buyer.get('code') or 'BUYER'}"
    markdown = _render_pi_markdown(
        pi_no=pi_no,
        issued=issued,
        seller=seller,
        buyer=buyer,
        lines=normalized_lines,
        currency=currency,
        subtotal=subtotal,
        payment_terms=payment_terms,
        delivery_terms=delivery_terms,
        validity_days=validity_days,
        notes=notes,
    )
    return {
        "document_type": "proforma_invoice",
        "pi_no": pi_no,
        "issued_date": issued,
        "currency": currency,
        "subtotal": round(subtotal, 2),
        "lines": normalized_lines,
        "seller": seller,
        "buyer": buyer,
        "payment_terms": payment_terms,
        "delivery_terms": delivery_terms,
        "validity_days": validity_days,
        "markdown": markdown,
        "gw_task": "trade_doc_pi_contract",
        "source": "smart-trade-ai document playbook (adapted)",
    }


def _render_pi_markdown(**kwargs: Any) -> str:
    """实现 渲染pimarkdown 的功能。
    
    :param kwargs: 参数 kwargs（类型: Any）
    :return: 返回 str 结果
    """
    seller = kwargs["seller"]
    buyer = kwargs["buyer"]
    lines = kwargs["lines"]
    md = [
        f"# Proforma Invoice {kwargs['pi_no']}",
        "",
        f"**Date:** {kwargs['issued']}",
        "",
        "## Seller",
        f"- {seller.get('name', '')}",
        f"- {seller.get('address', '')}",
        f"- Email: {seller.get('email', '')}",
        "",
        "## Buyer",
        f"- {buyer.get('name', '')}",
        f"- {buyer.get('company', buyer.get('name', ''))}",
        f"- {buyer.get('country', '')}",
        f"- Email: {buyer.get('email', '')}",
        "",
        "## Line Items",
        "",
        "| # | Description | Qty | Unit | Unit Price | Amount |",
        "|---|-------------|-----|------|------------|--------|",
    ]
    for row in lines:
        md.append(
            f"| {row['line_no']} | {row['description']} | {row['quantity']} | {row['unit']} | "
            f"{row['unit_price']} {kwargs['currency']} | {row['amount']} {kwargs['currency']} |"
        )
    md.extend(
        [
            "",
            f"**Subtotal:** {kwargs['subtotal']} {kwargs['currency']}",
            "",
            f"**Payment Terms:** {kwargs['payment_terms']}",
            f"**Delivery Terms:** {kwargs['delivery_terms']}",
            f"**Validity:** {kwargs['validity_days']} days",
        ]
    )
    if kwargs.get("notes"):
        md.extend(["", f"**Notes:** {kwargs['notes']}"])
    return "\n".join(md)
