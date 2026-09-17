# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""形式发票 PI / 商业发票 CI / 装箱单 PL / 原产地证 CO / 分批装运拆单 / 单据冲红全家桶。

30年外贸专家团队标准：
- PI: 形式发票（订单确认、首付30%定金与银行账户指引）
- CI: 商业发票（报关出运、清关完税与尾款核销）
- PL: 装箱单（总箱数、毛重GW、净重NW、外箱尺寸与集装箱20GP/40GP/40HQ装载配额）
- CO: 原产地证（优惠关税待遇、HS编码、原产地标准WO/PSR）
- Split Shipment: 分批装运拆单制单（批次单据与未交付余额追踪）
- Credit Note: 贷项凭单/单据冲红（退货退款与货损索赔冲销）
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── 1. 形式发票 Proforma Invoice (PI) ──────────────────────────────
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
    pi_no: Optional[str] = None,
    bank_details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """生成 PI 结构化包与 Markdown 文档。"""
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
                "hs_code": row.get("hs_code") or "6802.91.00",
                "quantity": qty,
                "unit": row.get("unit") or "pcs",
                "unit_price": price,
                "amount": amount,
                "currency": currency,
            }
        )

    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final_pi_no = pi_no or f"PI-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{buyer.get('code') or 'BUYER'}"
    default_bank = bank_details or {
        "beneficiary": seller.get("name", "YouDing Building Materials Tech Co., Ltd."),
        "bank_name": "Bank of China, Guangdong Branch",
        "swift_code": "BKCHCNBJ400",
        "account_no": "9558 8800 1234 5678 901",
    }

    markdown = _render_pi_markdown(
        pi_no=final_pi_no,
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
        bank_details=default_bank,
    )
    return {
        "document_type": "proforma_invoice",
        "pi_no": final_pi_no,
        "issued_date": issued,
        "currency": currency,
        "subtotal": round(subtotal, 2),
        "lines": normalized_lines,
        "seller": seller,
        "buyer": buyer,
        "bank_details": default_bank,
        "payment_terms": payment_terms,
        "delivery_terms": delivery_terms,
        "validity_days": validity_days,
        "markdown": markdown,
        "gw_task": "trade_doc_pi_contract",
        "source": "smart-trade-ai document playbook (enhanced)",
    }


def _render_pi_markdown(**kwargs: Any) -> str:
    seller = kwargs["seller"]
    buyer = kwargs["buyer"]
    lines = kwargs["lines"]
    bank = kwargs.get("bank_details") or {}
    md = [
        f"# Proforma Invoice {kwargs['pi_no']}",
        "",
        f"**Date:** {kwargs['issued']}",
        "",
        "## Seller",
        f"- **Name:** {seller.get('name', '')}",
        f"- **Address:** {seller.get('address', '')}",
        f"- **Email:** {seller.get('email', '')}",
        "",
        "## Buyer",
        f"- **Name:** {buyer.get('name', '')}",
        f"- **Company:** {buyer.get('company', buyer.get('name', ''))}",
        f"- **Country:** {buyer.get('country', '')}",
        f"- **Email:** {buyer.get('email', '')}",
        "",
        "## Line Items",
        "",
        "| # | Description | HS Code | Qty | Unit | Unit Price | Amount |",
        "|---|-------------|---------|-----|------|------------|--------|",
    ]
    for row in lines:
        md.append(
            f"| {row['line_no']} | {row['description']} | {row['hs_code']} | {row['quantity']} | {row['unit']} | "
            f"{row['unit_price']} {kwargs['currency']} | {row['amount']} {kwargs['currency']} |"
        )
    md.extend(
        [
            "",
            f"**Subtotal:** {kwargs['subtotal']} {kwargs['currency']}",
            "",
            f"**Payment Terms:** {kwargs['payment_terms']}",
            f"**Delivery Terms (Incoterms):** {kwargs['delivery_terms']}",
            f"**Validity:** {kwargs['validity_days']} days",
            "",
            "## Beneficiary Bank Details",
            f"- **Beneficiary:** {bank.get('beneficiary', '')}",
            f"- **Bank Name:** {bank.get('bank_name', '')}",
            f"- **SWIFT Code:** {bank.get('swift_code', '')}",
            f"- **Account Number:** {bank.get('account_no', '')}",
        ]
    )
    if kwargs.get("notes"):
        md.extend(["", f"**Notes:** {kwargs['notes']}"])
    return "\n".join(md)


# ── 2. 商业发票 Commercial Invoice (CI) ───────────────────────────
def build_commercial_invoice(
    *,
    seller: dict[str, Any],
    buyer: dict[str, Any],
    lines: list[dict[str, Any]],
    ci_no: Optional[str] = None,
    pi_ref: Optional[str] = None,
    order_ref: Optional[str] = None,
    currency: str = "USD",
    incoterms: str = "FOB Shenzhen",
    port_of_loading: str = "Shenzhen, China",
    port_of_discharge: str = "Rotterdam, Netherlands",
    vessel_voyage: Optional[str] = "EVER GIVEN / V.0124W",
    bl_number: Optional[str] = "COSU63289124",
    deposit_paid: float = 0.0,
    payment_terms: str = "30% deposit received, 70% against B/L copy",
    bank_details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """生成正式出口商业发票 (Commercial Invoice) 用于清关与收汇。"""
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
                "hs_code": row.get("hs_code") or "6802.91.00",
                "quantity": qty,
                "unit": row.get("unit") or "pcs",
                "unit_price": price,
                "amount": amount,
                "currency": currency,
            }
        )

    subtotal = round(subtotal, 2)
    deposit_paid = round(float(deposit_paid or 0.0), 2)
    balance_due = round(max(0.0, subtotal - deposit_paid), 2)

    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final_ci_no = ci_no or f"CI-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{buyer.get('code') or 'INV'}"

    default_bank = bank_details or {
        "beneficiary": seller.get("name", "YouDing Building Materials Tech Co., Ltd."),
        "bank_name": "Bank of China, Guangdong Branch",
        "swift_code": "BKCHCNBJ400",
        "account_no": "9558 8800 1234 5678 901",
    }

    md = [
        f"# Commercial Invoice {final_ci_no}",
        "",
        f"**Date:** {issued}",
        f"**PI Reference:** {pi_ref or 'N/A'}",
        f"**Order Ref:** {order_ref or 'N/A'}",
        f"**Bill of Lading (B/L):** {bl_number or 'Pending'}",
        "",
        "## Shipper / Exporter",
        f"- {seller.get('name', '')}",
        f"- {seller.get('address', '')}",
        "",
        "## Consignee / Buyer",
        f"- {buyer.get('name', '')}",
        f"- {buyer.get('company', buyer.get('name', ''))}",
        f"- {buyer.get('address', '')}",
        "",
        "## Shipping Details",
        f"- **Port of Loading (POL):** {port_of_loading}",
        f"- **Port of Discharge (POD):** {port_of_discharge}",
        f"- **Vessel/Voyage:** {vessel_voyage or 'TBA'}",
        f"- **Incoterms:** {incoterms}",
        "",
        "## Goods & Pricing",
        "",
        "| # | Description | HS Code | Qty | Unit | Unit Price | Amount |",
        "|---|-------------|---------|-----|------|------------|--------|",
    ]
    for row in normalized_lines:
        md.append(
            f"| {row['line_no']} | {row['description']} | {row['hs_code']} | {row['quantity']} | {row['unit']} | "
            f"{row['unit_price']} {currency} | {row['amount']} {currency} |"
        )
    md.extend(
        [
            "",
            f"**Total Invoice Value:** {subtotal} {currency}",
            f"**Less Deposit Paid:** {deposit_paid} {currency}",
            f"**Balance Due & Payable:** {balance_due} {currency}",
            "",
            f"**Payment Terms:** {payment_terms}",
            "",
            "## Remittance Bank Details",
            f"- **Beneficiary:** {default_bank.get('beneficiary', '')}",
            f"- **Bank:** {default_bank.get('bank_name', '')}",
            f"- **SWIFT:** {default_bank.get('swift_code', '')}",
            f"- **Account:** {default_bank.get('account_no', '')}",
        ]
    )

    return {
        "document_type": "commercial_invoice",
        "ci_no": final_ci_no,
        "pi_ref": pi_ref,
        "order_ref": order_ref,
        "issued_date": issued,
        "currency": currency,
        "subtotal": subtotal,
        "deposit_paid": deposit_paid,
        "balance_due": balance_due,
        "lines": normalized_lines,
        "seller": seller,
        "buyer": buyer,
        "incoterms": incoterms,
        "port_of_loading": port_of_loading,
        "port_of_discharge": port_of_discharge,
        "vessel_voyage": vessel_voyage,
        "bl_number": bl_number,
        "bank_details": default_bank,
        "markdown": "\n".join(md),
    }


# ── 3. 装箱单 Packing List (PL) ───────────────────────────────────
def build_packing_list(
    *,
    seller: dict[str, Any],
    buyer: dict[str, Any],
    packages: list[dict[str, Any]],
    pl_no: Optional[str] = None,
    ci_ref: Optional[str] = None,
    order_ref: Optional[str] = None,
    shipping_marks: str = "N/M (No Marks) or As Addressed",
    port_of_loading: str = "Shenzhen, China",
    port_of_discharge: str = "Rotterdam, Netherlands",
) -> dict[str, Any]:
    """生成正式出口装箱单 (Packing List) 并自动核算总箱数、毛重、净重与 CBM 体积。"""
    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final_pl_no = pl_no or f"PL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{buyer.get('code') or 'PKG'}"

    total_packages = 0
    total_qty = 0.0
    total_net_weight = 0.0
    total_gross_weight = 0.0
    total_cbm = 0.0

    normalized_packages: list[dict[str, Any]] = []
    for i, pkg in enumerate(packages, start=1):
        pkg_count = int(pkg.get("package_count") or 1)
        qty_per_pkg = float(pkg.get("qty_per_package") or pkg.get("quantity") or 1)
        item_qty = pkg_count * qty_per_pkg

        nw_unit = float(pkg.get("net_weight_kg") or 10.0)
        gw_unit = float(pkg.get("gross_weight_kg") or 11.5)
        length_cm = float(pkg.get("length_cm") or 60.0)
        width_cm = float(pkg.get("width_cm") or 40.0)
        height_cm = float(pkg.get("height_cm") or 30.0)

        cbm_per_pkg = (length_cm * width_cm * height_cm) / 1_000_000.0
        cbm_line = round(cbm_per_pkg * pkg_count, 3)

        line_nw = round(nw_unit * pkg_count, 2)
        line_gw = round(gw_unit * pkg_count, 2)

        total_packages += pkg_count
        total_qty += item_qty
        total_net_weight += line_nw
        total_gross_weight += line_gw
        total_cbm += cbm_line

        normalized_packages.append(
            {
                "item_no": i,
                "package_range": pkg.get("package_range") or f"CTN #{total_packages - pkg_count + 1}-{total_packages}",
                "description": pkg.get("description") or "Building Hardware Components",
                "package_type": pkg.get("package_type") or "Carton",
                "package_count": pkg_count,
                "total_quantity": item_qty,
                "unit": pkg.get("unit") or "pcs",
                "net_weight_kg": line_nw,
                "gross_weight_kg": line_gw,
                "dimensions_cm": f"{length_cm}x{width_cm}x{height_cm}",
                "cbm": cbm_line,
            }
        )

    total_net_weight = round(total_net_weight, 2)
    total_gross_weight = round(total_gross_weight, 2)
    total_cbm = round(total_cbm, 3)

    # 集装箱配载率测算 (Stuffing Calculation)
    stuffing = {
        "cbm_total": total_cbm,
        "gross_weight_total_kg": total_gross_weight,
        "fits_in_20gp_pct": round((total_cbm / 28.0) * 100, 1),
        "fits_in_40gp_pct": round((total_cbm / 58.0) * 100, 1),
        "fits_in_40hq_pct": round((total_cbm / 68.0) * 100, 1),
        "recommended_container": "20GP" if total_cbm <= 28.0 and total_gross_weight <= 21000 else "40HQ",
    }

    md = [
        f"# Packing List {final_pl_no}",
        "",
        f"**Date:** {issued}",
        f"**Invoice Ref:** {ci_ref or 'N/A'}",
        f"**Order Ref:** {order_ref or 'N/A'}",
        f"**Shipping Marks:** {shipping_marks}",
        "",
        "## Shipper",
        f"- {seller.get('name', '')}",
        "",
        "## Consignee",
        f"- {buyer.get('name', '')}",
        f"- {buyer.get('company', '')}",
        "",
        "## Cargo Details",
        "",
        "| Item | Package Range | Description | Pkgs | Qty | N.W. (KG) | G.W. (KG) | Dim (CM) | CBM |",
        "|------|---------------|-------------|------|-----|-----------|-----------|----------|-----|",
    ]
    for row in normalized_packages:
        md.append(
            f"| {row['item_no']} | {row['package_range']} | {row['description']} | {row['package_count']} | "
            f"{row['total_quantity']} {row['unit']} | {row['net_weight_kg']} | {row['gross_weight_kg']} | "
            f"{row['dimensions_cm']} | {row['cbm']} |"
        )
    md.extend(
        [
            "",
            f"**Total Packages:** {total_packages} Cartons/Packages",
            f"**Total Quantity:** {total_qty}",
            f"**Total Net Weight:** {total_net_weight} KGS",
            f"**Total Gross Weight:** {total_gross_weight} KGS",
            f"**Total Measurement:** {total_cbm} CBM",
            "",
            "## Container Stuffing Estimation",
            f"- Recommended: {stuffing['recommended_container']}",
            f"- 20GP Usage: {stuffing['fits_in_20gp_pct']}% (Capacity ~28 CBM)",
            f"- 40HQ Usage: {stuffing['fits_in_40hq_pct']}% (Capacity ~68 CBM)",
        ]
    )

    return {
        "document_type": "packing_list",
        "pl_no": final_pl_no,
        "ci_ref": ci_ref,
        "order_ref": order_ref,
        "issued_date": issued,
        "seller": seller,
        "buyer": buyer,
        "shipping_marks": shipping_marks,
        "port_of_loading": port_of_loading,
        "port_of_discharge": port_of_discharge,
        "packages": normalized_packages,
        "total_packages": total_packages,
        "total_quantity": total_qty,
        "total_net_weight_kg": total_net_weight,
        "total_gross_weight_kg": total_gross_weight,
        "total_cbm": total_cbm,
        "stuffing_estimation": stuffing,
        "markdown": "\n".join(md),
    }


# ── 4. 原产地证 Certificate of Origin (CO) ───────────────────────
def build_certificate_of_origin(
    *,
    exporter: dict[str, Any],
    consignee: dict[str, Any],
    items: list[dict[str, Any]],
    co_no: Optional[str] = None,
    invoice_no: Optional[str] = None,
    transport_details: str = "By Sea from Shenzhen to Rotterdam",
    origin_country: str = "The People's Republic of China",
    destination_country: str = "Netherlands",
) -> dict[str, Any]:
    """生成符合 CCPIT/海关格式的原产地证明书 (CO)。"""
    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final_co_no = co_no or f"CO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-CCPIT"

    normalized_items: list[dict[str, Any]] = []
    for i, it in enumerate(items, start=1):
        normalized_items.append({
            "item_no": i,
            "marks_and_numbers": it.get("shipping_marks") or "N/M",
            "packages_and_description": it.get("description") or "Building Materials Hardware",
            "hs_code": it.get("hs_code") or "6802.91.00",
            "origin_criterion": it.get("origin_criterion") or "WO",  # WO: Wholly Obtained, or PSR
            "gross_weight": f"{it.get('gross_weight_kg', 100)} KGS",
            "invoice_no_date": f"{invoice_no or 'CI-PENDING'} / {issued}",
        })

    md = [
        f"# Certificate of Origin (Form CO) - {final_co_no}",
        "",
        f"**Date:** {issued}",
        f"**Country of Origin:** {origin_country}",
        f"**Country of Destination:** {destination_country}",
        "",
        "## 1. Goods Consigned From (Exporter's Business Name, Address, Country)",
        f"- {exporter.get('name', '')}",
        f"- {exporter.get('address', '')}",
        "",
        "## 2. Goods Consigned To (Consignee's Name, Address, Country)",
        f"- {consignee.get('name', '')}",
        f"- {consignee.get('address', '')}",
        "",
        "## 3. Means of Transport & Route",
        f"- {transport_details}",
        "",
        "## 4. Itemized Goods & Origin Criteria",
        "",
        "| Item | Marks & Numbers | Number and Kind of Packages; Description of Goods | HS Code | Origin Criterion | Gross Weight | Invoice No. & Date |",
        "|------|-----------------|---------------------------------------------------|---------|------------------|--------------|-------------------|",
    ]
    for row in normalized_items:
        md.append(
            f"| {row['item_no']} | {row['marks_and_numbers']} | {row['packages_and_description']} | "
            f"{row['hs_code']} | {row['origin_criterion']} | {row['gross_weight']} | {row['invoice_no_date']} |"
        )
    md.extend(
        [
            "",
            "## 5. Declaration by the Exporter",
            "The undersigned hereby declares that the above details and statements are correct; that all the goods were produced in China.",
            "",
            "## 6. Certification",
            "It is hereby certified, on the basis of control carried out, that the declaration by the exporter is correct.",
        ]
    )

    return {
        "document_type": "certificate_of_origin",
        "co_no": final_co_no,
        "issued_date": issued,
        "exporter": exporter,
        "consignee": consignee,
        "origin_country": origin_country,
        "destination_country": destination_country,
        "transport_details": transport_details,
        "items": normalized_items,
        "markdown": "\n".join(md),
    }


# ── 5. 分批装运拆单制单 (Split Shipment) ──────────────────────────
def build_split_shipment_documents(
    *,
    parent_order_id: str,
    seller: dict[str, Any],
    buyer: dict[str, Any],
    total_order_lines: list[dict[str, Any]],
    batch_lines: list[dict[str, Any]],
    batch_index: int = 1,
    currency: str = "USD",
    incoterms: str = "FOB Shenzhen",
) -> dict[str, Any]:
    """处理分批装运（如 1000 件首批发 500 件），自动拆分该批次 CI/箱单并核算剩余未发尾数。"""
    # 匹配与校验发货量
    batch_shipped: list[dict[str, Any]] = []
    remaining_balance: list[dict[str, Any]] = []

    batch_map = {b.get("description") or b.get("product_name"): float(b.get("quantity") or 0) for b in batch_lines}
    # 若仅有 1 项总行与 1 项分批出运，即使品名别名略有不同也直接匹配数量
    single_batch_qty = float(batch_lines[0].get("quantity") or 0) if len(batch_lines) == 1 else None

    for idx, item in enumerate(total_order_lines):
        desc = item.get("description") or item.get("product_name") or ""
        total_q = float(item.get("quantity") or 0)
        unit_price = float(item.get("unit_price") or 0)
        hs_code = item.get("hs_code") or "6802.91.00"

        shipped_q = batch_map.get(desc)
        if shipped_q is None:
            if single_batch_qty is not None and len(total_order_lines) == 1:
                shipped_q = single_batch_qty
            elif idx < len(batch_lines):
                shipped_q = float(batch_lines[idx].get("quantity") or 0)
            else:
                shipped_q = 0.0

        if shipped_q > total_q:
            shipped_q = total_q
        remain_q = max(0.0, total_q - shipped_q)

        batch_shipped.append({
            "description": desc,
            "quantity": shipped_q,
            "unit_price": unit_price,
            "hs_code": hs_code,
            "unit": item.get("unit", "pcs"),
        })
        remaining_balance.append({
            "description": desc,
            "total_ordered": total_q,

            "shipped_quantity": shipped_q,
            "remaining_quantity": remain_q,
            "unit_price": unit_price,
            "hs_code": hs_code,
            "unit": item.get("unit", "pcs"),
        })

    # 为本批次生成独立 CI
    batch_ci_no = f"CI-{parent_order_id[:8]}-B{batch_index}"
    ci = build_commercial_invoice(
        seller=seller,
        buyer=buyer,
        lines=batch_shipped,
        ci_no=batch_ci_no,
        order_ref=parent_order_id,
        currency=currency,
        incoterms=incoterms,
    )

    # 为本批次生成独立 Packing List
    batch_packages = [
        {
            "package_count": max(1, int(row["quantity"] // 10)),
            "qty_per_package": 10,
            "description": row["description"],
            "net_weight_kg": 15.0,
            "gross_weight_kg": 16.5,
        }
        for row in batch_shipped
    ]
    batch_pl_no = f"PL-{parent_order_id[:8]}-B{batch_index}"
    pl = build_packing_list(
        seller=seller,
        buyer=buyer,
        packages=batch_packages,
        pl_no=batch_pl_no,
        ci_ref=batch_ci_no,
        order_ref=parent_order_id,
    )

    is_all_fulfilled = all(r["remaining_quantity"] <= 0 for r in remaining_balance)

    return {
        "parent_order_id": parent_order_id,
        "batch_index": batch_index,
        "is_all_fulfilled": is_all_fulfilled,
        "commercial_invoice": ci,
        "packing_list": pl,
        "remaining_backlog": remaining_balance,
        "summary": {
            "batch_shipped_count": sum(r["quantity"] for r in batch_shipped),
            "remaining_pending_count": sum(r["remaining_quantity"] for r in remaining_balance),
        }
    }


# ── 6. 单据冲红 Credit Note ─────────────────────────────────────────
def build_credit_note(
    *,
    credit_note_no: Optional[str] = None,
    original_ci_no: str,
    seller: dict[str, Any],
    buyer: dict[str, Any],
    credited_items: list[dict[str, Any]],
    currency: str = "USD",
    reason: str = "Defective goods compensation / Return adjustment",
) -> dict[str, Any]:
    """生成正式出口贷项凭单（单据冲红），用于退货退款、破损索赔或价格纠错。"""
    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final_cn_no = credit_note_no or f"CN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{original_ci_no[-6:]}"

    total_credit = 0.0
    normalized_lines = []
    for i, it in enumerate(credited_items, start=1):
        qty = float(it.get("quantity") or 0)
        rate = float(it.get("unit_price") or 0)
        amt = round(qty * rate, 2)
        total_credit += amt
        normalized_lines.append({
            "line_no": i,
            "description": it.get("description", "Quality Defect Compensation"),
            "quantity": qty,
            "unit": it.get("unit", "pcs"),
            "credit_rate": rate,
            "credit_amount": amt,
            "reason": it.get("reason", reason),
        })

    total_credit = round(total_credit, 2)

    md = [
        f"# Credit Note (单据冲红) {final_cn_no}",
        "",
        f"**Date:** {issued}",
        f"**Original Invoice Reference:** {original_ci_no}",
        f"**Reason for Credit:** {reason}",
        "",
        "## Creditor (Seller)",
        f"- {seller.get('name', '')}",
        "",
        "## Debtor (Buyer)",
        f"- {buyer.get('name', '')}",
        f"- {buyer.get('company', '')}",
        "",
        "## Credited Items",
        "",
        "| Line | Description | Qty | Unit | Rate | Credited Amount | Specific Reason |",
        "|------|-------------|-----|------|------|-----------------|-----------------|",
    ]
    for row in normalized_lines:
        md.append(
            f"| {row['line_no']} | {row['description']} | {row['quantity']} | {row['unit']} | "
            f"-{row['credit_rate']} {currency} | -{row['credit_amount']} {currency} | {row['reason']} |"
        )
    md.extend([
        "",
        f"**Total Credit Reversal Amount:** -{total_credit} {currency}",
        "",
        "This Credit Note reduces the outstanding accounts receivable balance on the original invoice referenced above.",
    ])

    return {
        "document_type": "credit_note",
        "credit_note_no": final_cn_no,
        "original_ci_no": original_ci_no,
        "issued_date": issued,
        "seller": seller,
        "buyer": buyer,
        "currency": currency,
        "total_credit_amount": total_credit,
        "credited_items": normalized_lines,
        "reason": reason,
        "markdown": "\n".join(md),
    }
