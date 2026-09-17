# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""PI / 报价单导出 — DOCX（OOXML）与可打印 HTML。"""

from __future__ import annotations

import html
import io
import zipfile
from typing import Any
from xml.sax.saxutils import escape

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""


def _docx_paragraph(text: str, *, bold: bool = False) -> str:
    """实现 docxparagraph 的功能。
    
    :param text: 参数 text（类型: str）
    :param bold: 参数 bold（类型: bool）
    :return: 返回 str 结果
    """
    t = escape(text or "")
    if bold:
        return f"<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space=\"preserve\">{t}</w:t></w:r></w:p>"
    return f"<w:p><w:r><w:t xml:space=\"preserve\">{t}</w:t></w:r></w:p>"


def build_proforma_docx(doc: dict[str, Any]) -> bytes:
    """最小 OOXML Word 文档（无 python-docx 依赖）。"""
    lines: list[str] = []
    lines.append(_docx_paragraph(f"Proforma Invoice {doc.get('pi_no', '')}", bold=True))
    lines.append(_docx_paragraph(f"Date: {doc.get('issued_date', '')}"))
    lines.append(_docx_paragraph(""))
    seller = doc.get("seller") or {}
    buyer = doc.get("buyer") or {}
    lines.append(_docx_paragraph("Seller", bold=True))
    lines.append(_docx_paragraph(str(seller.get("name") or "")))
    lines.append(_docx_paragraph(str(seller.get("address") or "")))
    lines.append(_docx_paragraph(f"Email: {seller.get('email') or ''}"))
    lines.append(_docx_paragraph(""))
    lines.append(_docx_paragraph("Buyer", bold=True))
    lines.append(_docx_paragraph(str(buyer.get("company") or buyer.get("name") or "")))
    lines.append(_docx_paragraph(f"Email: {buyer.get('email') or ''}"))
    lines.append(_docx_paragraph(""))
    lines.append(_docx_paragraph("Line Items", bold=True))
    currency = doc.get("currency") or "USD"
    for row in doc.get("lines") or []:
        desc = row.get("description") or ""
        qty = row.get("quantity")
        unit = row.get("unit") or "pcs"
        price = row.get("unit_price")
        amount = row.get("amount")
        lines.append(
            _docx_paragraph(
                f"{row.get('line_no', '')}. {desc} | {qty} {unit} @ {price} {currency} = {amount} {currency}"
            )
        )
    lines.append(_docx_paragraph(""))
    lines.append(_docx_paragraph(f"Subtotal: {doc.get('subtotal')} {currency}", bold=True))
    lines.append(_docx_paragraph(f"Payment: {doc.get('payment_terms') or ''}"))
    lines.append(_docx_paragraph(f"Delivery: {doc.get('delivery_terms') or ''}"))
    if doc.get("notes"):
        lines.append(_docx_paragraph(f"Notes: {doc['notes']}"))

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(lines)}</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        zf.writestr("word/document.xml", document_xml)
    return buf.getvalue()


def build_proforma_print_html(doc: dict[str, Any]) -> str:
    """浏览器打开后可「打印 → 另存为 PDF」。"""
    seller = doc.get("seller") or {}
    buyer = doc.get("buyer") or {}
    currency = doc.get("currency") or "USD"
    rows = doc.get("lines") or []
    tr_html = ""
    for row in rows:
        tr_html += (
            f"<tr><td>{html.escape(str(row.get('line_no', '')))}</td>"
            f"<td>{html.escape(str(row.get('description') or ''))}</td>"
            f"<td>{html.escape(str(row.get('quantity') or ''))}</td>"
            f"<td>{html.escape(str(row.get('unit') or ''))}</td>"
            f"<td>{html.escape(str(row.get('unit_price') or ''))}</td>"
            f"<td>{html.escape(str(row.get('amount') or ''))} {html.escape(currency)}</td></tr>"
        )
    md = doc.get("markdown") or ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<title>{html.escape(str(doc.get('pi_no') or 'PI'))}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #111; }}
h1 {{ font-size: 20px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; font-size: 13px; }}
.meta {{ font-size: 13px; line-height: 1.6; }}
@media print {{ body {{ margin: 16px; }} }}
</style></head><body>
<h1>Proforma Invoice {html.escape(str(doc.get('pi_no') or ''))}</h1>
<p class="meta">Date: {html.escape(str(doc.get('issued_date') or ''))}</p>
<div class="meta"><strong>Seller</strong><br/>
{html.escape(str(seller.get('name') or ''))}<br/>
{html.escape(str(seller.get('address') or ''))}<br/>
Email: {html.escape(str(seller.get('email') or ''))}</div>
<div class="meta" style="margin-top:12px"><strong>Buyer</strong><br/>
{html.escape(str(buyer.get('company') or buyer.get('name') or ''))}<br/>
Email: {html.escape(str(buyer.get('email') or ''))}</div>
<table><thead><tr><th>#</th><th>Description</th><th>Qty</th><th>Unit</th><th>Unit Price</th><th>Amount</th></tr></thead>
<tbody>{tr_html}</tbody></table>
<p class="meta"><strong>Subtotal:</strong> {html.escape(str(doc.get('subtotal') or ''))} {html.escape(currency)}</p>
<p class="meta"><strong>Payment:</strong> {html.escape(str(doc.get('payment_terms') or ''))}</p>
<p class="meta"><strong>Delivery:</strong> {html.escape(str(doc.get('delivery_terms') or ''))}</p>
<pre style="white-space:pre-wrap;font-size:12px;margin-top:24px;border-top:1px solid #eee;padding-top:12px">{html.escape(md)}</pre>
</body></html>"""


def build_proforma_pdf(doc: dict[str, Any]) -> bytes:
    """原生 PDF（reportlab）。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    x = 20 * mm
    y = height - 20 * mm
    line_h = 6 * mm
    def line(text: str, *, bold: bool = False) -> None:
        """实现 line 的功能。
        
        :param text: 参数 text（类型: str）
        :param bold: 参数 bold（类型: bool）
        :return: 返回 None 结果
        """
        nonlocal y
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm
        if bold:
            c.setFont("Helvetica-Bold", 11)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(x, y, (text or "")[:120])
        y -= line_h

    seller = doc.get("seller") or {}
    buyer = doc.get("buyer") or {}
    currency = doc.get("currency") or "USD"
    line(f"Proforma Invoice {doc.get('pi_no', '')}", bold=True)
    line(f"Date: {doc.get('issued_date', '')}")
    line("")
    line("Seller", bold=True)
    line(str(seller.get("name") or ""))
    line(str(seller.get("address") or ""))
    line(f"Email: {seller.get('email') or ''}")
    line("")
    line("Buyer", bold=True)
    line(str(buyer.get("company") or buyer.get("name") or ""))
    line(f"Email: {buyer.get('email') or ''}")
    line("")
    line("Line Items", bold=True)
    for row in doc.get("lines") or []:
        desc = row.get("description") or ""
        qty = row.get("quantity")
        unit = row.get("unit") or "pcs"
        price = row.get("unit_price")
        amount = row.get("amount")
        line(
            f"{row.get('line_no', '')}. {desc} | {qty} {unit} @ {price} {currency} = {amount} {currency}"
        )
    line("")
    line(f"Subtotal: {doc.get('subtotal')} {currency}", bold=True)
    line(f"Payment: {doc.get('payment_terms') or ''}")
    line(f"Delivery: {doc.get('delivery_terms') or ''}")
    if doc.get("notes"):
        line(f"Notes: {doc['notes']}")

    c.save()
    return buf.getvalue()


def build_trade_document_html(doc: dict[str, Any]) -> str:
    """通用外贸单证专业级 HTML 导出（支持 PI、CI、Packing List、CO、Credit Note 全面排版）。"""
    doc_type = doc.get("document_type") or "document"
    doc_label = doc_type.replace("_", " ").title()
    title = (
        doc.get("pi_no")
        or doc.get("ci_no")
        or doc.get("pl_no")
        or doc.get("co_no")
        or doc.get("credit_note_no")
        or doc_type.upper()
    )
    seller = doc.get("seller") or doc.get("exporter") or {}
    buyer = doc.get("buyer") or doc.get("consignee") or {}
    currency = doc.get("currency") or "USD"
    issued_date = doc.get("issued_date") or ""

    # 提取明细行
    lines = doc.get("lines") or doc.get("items") or doc.get("packages") or []
    lines_html = ""
    for idx, row in enumerate(lines, start=1):
        desc = html.escape(str(row.get("description") or row.get("product_name") or ""))
        hs = html.escape(str(row.get("hs_code") or "-"))
        qty = row.get("quantity") or row.get("package_count") or ""
        unit = html.escape(str(row.get("unit") or "pcs"))
        unit_price = f"{currency} {float(row.get('unit_price') or 0):,.2f}" if "unit_price" in row else "-"
        amount = f"{currency} {float(row.get('amount') or (float(row.get('quantity') or 0) * float(row.get('unit_price') or 0))):,.2f}" if "amount" in row or "unit_price" in row else "-"
        lines_html += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td><strong>{desc}</strong></td>
            <td style="text-align: center; font-family: monospace;">{hs}</td>
            <td style="text-align: right;">{qty} {unit}</td>
            <td style="text-align: right;">{unit_price}</td>
            <td style="text-align: right; font-weight: 600;">{amount}</td>
        </tr>"""

    # 财务与履约数据
    subtotal = float(doc.get("subtotal") or doc.get("total_amount") or 0.0)
    deposit_paid = float(doc.get("deposit_paid") or 0.0)
    balance_due = float(doc.get("balance_due") or (subtotal - deposit_paid))

    bank = doc.get("bank_details") or {}
    bank_html = ""
    if bank:
        bank_html = f"""
        <div class="card bank-box">
            <h4>International Wire Transfer / 国际收汇银行路径</h4>
            <p><strong>Beneficiary Name / 收款人:</strong> {html.escape(str(bank.get('beneficiary', seller.get('name', ''))))}</p>
            <p><strong>Bank Name / 收款银行:</strong> {html.escape(str(bank.get('bank_name', '')))}</p>
            <p><strong>SWIFT Code:</strong> <code>{html.escape(str(bank.get('swift_code', '')))}</code></p>
            <p><strong>Account / IBAN:</strong> <code>{html.escape(str(bank.get('account_no', '')))}</code></p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{html.escape(str(doc_label))} - {html.escape(str(title))}</title>
<style>
    @page {{ size: A4; margin: 15mm; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        margin: 30px auto; max-width: 960px; color: #1f2937; line-height: 1.5; background: #fff;
    }}
    .header-bar {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #4a9b8c; padding-bottom: 16px; margin-bottom: 24px; }}
    .logo-area h1 {{ margin: 0; font-size: 26px; color: #111827; letter-spacing: -0.5px; }}
    .logo-area p {{ margin: 4px 0 0 0; font-size: 13px; color: #6b7280; }}
    .doc-meta {{ text-align: right; }}
    .badge {{ display: inline-block; padding: 4px 12px; font-size: 14px; font-weight: 700; border-radius: 4px; background: #e6f4f1; color: #2a6b60; margin-bottom: 8px; text-transform: uppercase; }}
    .doc-num {{ font-size: 18px; font-weight: 700; color: #111827; font-family: monospace; }}
    .doc-date {{ font-size: 12px; color: #6b7280; }}
    
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .card {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 18px; }}
    .card h3, .card h4 {{ margin-top: 0; margin-bottom: 10px; font-size: 14px; color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
    .card p {{ margin: 4px 0; font-size: 13px; color: #4b5563; }}
    
    .params-table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px; }}
    .params-table td {{ padding: 6px 12px; border: 1px solid #e5e7eb; }}
    .params-table td.label {{ background: #f3f4f6; font-weight: 600; width: 18%; color: #374151; }}
    
    table.data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; }}
    table.data-table th {{ background: #4a9b8c; color: #ffffff; padding: 10px 12px; border: 1px solid #4a9b8c; text-align: left; font-weight: 600; }}
    table.data-table td {{ padding: 9px 12px; border: 1px solid #e5e7eb; color: #374151; }}
    table.data-table tr:nth-child(even) {{ background: #f9fafb; }}
    
    .totals-area {{ display: flex; justify-content: flex-end; margin-bottom: 24px; }}
    .totals-table {{ width: 340px; border-collapse: collapse; font-size: 13px; }}
    .totals-table td {{ padding: 6px 12px; border: 1px solid #e5e7eb; }}
    .totals-table td.total-label {{ background: #f3f4f6; font-weight: 600; text-align: right; }}
    .totals-table td.total-val {{ font-weight: 700; text-align: right; color: #111827; }}
    .totals-table tr.grand-total td {{ background: #e6f4f1; color: #1b4d44; font-size: 15px; }}
    
    .bank-box code {{ background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
    
    .signatures {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px; padding-top: 20px; border-top: 1px dashed #d1d5db; }}
    .sig-block {{ text-align: center; }}
    .sig-line {{ margin-top: 60px; border-bottom: 1px solid #374151; width: 80%; margin-left: auto; margin-right: auto; }}
    .sig-title {{ margin-top: 6px; font-size: 12px; color: #6b7280; font-weight: 600; }}
    .stamp-box {{ width: 110px; height: 110px; border: 2px dashed #f87171; color: #ef4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 10px auto; font-size: 11px; font-weight: 700; text-transform: uppercase; transform: rotate(-8deg); }}
    
    @media print {{
        body {{ margin: 0; padding: 0; max-width: 100%; }}
        .badge {{ border: 1px solid #4a9b8c; }}
    }}
</style>
</head>
<body>

<div class="header-bar">
    <div class="logo-area">
        <h1>{html.escape(str(seller.get('name') or 'YouDing B2B Trade'))}</h1>
        <p>Official Trade Document | {html.escape(str(seller.get('address') or 'China International Commerce Center'))} | Tel/Email: {html.escape(str(seller.get('email') or 'sales@youding.com'))}</p>
    </div>
    <div class="doc-meta">
        <div class="badge">{html.escape(doc_label)}</div>
        <div class="doc-num">{html.escape(str(title))}</div>
        <div class="doc-date">Issued Date: {html.escape(str(issued_date))}</div>
    </div>
</div>

<div class="grid-2">
    <div class="card">
        <h3>SELLER / EXPORTER / 卖方</h3>
        <p><strong>{html.escape(str(seller.get('name') or ''))}</strong></p>
        <p>{html.escape(str(seller.get('address') or ''))}</p>
        <p>Email: {html.escape(str(seller.get('email') or ''))}</p>
        {f"<p>Phone: {html.escape(str(seller.get('phone')))}</p>" if seller.get('phone') else ""}
    </div>
    <div class="card">
        <h3>BUYER / CONSIGNEE / 买方</h3>
        <p><strong>{html.escape(str(buyer.get('company') or buyer.get('name') or ''))}</strong></p>
        <p>{html.escape(str(buyer.get('address') or ''))}</p>
        <p>Email: {html.escape(str(buyer.get('email') or ''))}</p>
        {f"<p>Country: {html.escape(str(buyer.get('country')))}</p>" if buyer.get('country') else ""}
    </div>
</div>

<table class="params-table">
    <tr>
        <td class="label">Incoterms 2020:</td>
        <td>{html.escape(str(doc.get('delivery_terms') or doc.get('incoterms') or 'FOB Shenzhen'))}</td>
        <td class="label">Payment Terms:</td>
        <td>{html.escape(str(doc.get('payment_terms') or '30% T/T Deposit, 70% against B/L'))}</td>
    </tr>
    <tr>
        <td class="label">Port of Loading:</td>
        <td>{html.escape(str(doc.get('port_of_loading') or 'Shenzhen / Guangzhou, China'))}</td>
        <td class="label">Port of Discharge:</td>
        <td>{html.escape(str(doc.get('port_of_discharge') or buyer.get('country') or 'Main Destination Port'))}</td>
    </tr>
    {f"<tr><td class='label'>Bill of Lading:</td><td>{html.escape(str(doc.get('bl_number')))}</td><td class='label'>Container No:</td><td>{html.escape(str(doc.get('container_no') or '-'))}</td></tr>" if doc.get('bl_number') else ""}
</table>

<table class="data-table">
    <thead>
        <tr>
            <th style="width: 5%; text-align: center;">#</th>
            <th style="width: 45%;">Description of Goods / 货物描述</th>
            <th style="width: 15%; text-align: center;">HS Code</th>
            <th style="width: 12%; text-align: right;">Quantity</th>
            <th style="width: 11%; text-align: right;">Unit Price</th>
            <th style="width: 12%; text-align: right;">Amount</th>
        </tr>
    </thead>
    <tbody>
        {lines_html}
    </tbody>
</table>

<div class="totals-area">
    <table class="totals-table">
        <tr>
            <td class="total-label">Subtotal / 货款总额:</td>
            <td class="total-val">{currency} {subtotal:,.2f}</td>
        </tr>
        {f"<tr><td class='total-label'>Deposit Paid / 已付定金:</td><td class='total-val'>{currency} {deposit_paid:,.2f}</td></tr>" if deposit_paid > 0 else ""}
        <tr class="grand-total">
            <td class="total-label">{ 'Balance Due / 应付尾款:' if deposit_paid > 0 else 'Total Amount / 合计:' }</td>
            <td class="total-val">{currency} {balance_due:,.2f}</td>
        </tr>
    </table>
</div>

{bank_html}

<div class="signatures">
    <div class="sig-block">
        <div class="stamp-box">COMPANY SEAL<br/>OFFICIAL STAMP</div>
        <div class="sig-line"></div>
        <div class="sig-title">Authorized Signature / 卖方授权签字</div>
    </div>
    <div class="sig-block">
        <div style="height: 110px;"></div>
        <div class="sig-line"></div>
        <div class="sig-title">Confirmed & Accepted by Buyer / 买方确认盖章</div>
    </div>
</div>

</body>
</html>"""


def build_trade_document_docx(doc: dict[str, Any]) -> bytes:
    """通用外贸单证 DOCX 导出（无第三方库依赖的 OOXML 生成）。"""
    doc_type = doc.get("document_type") or "trade_document"
    title = (
        doc.get("pi_no")
        or doc.get("ci_no")
        or doc.get("pl_no")
        or doc.get("co_no")
        or doc.get("credit_note_no")
        or doc_type.upper()
    )
    md = doc.get("markdown") or ""
    lines: list[str] = []
    lines.append(_docx_paragraph(f"{doc_type.replace('_', ' ').title()} - {title}", bold=True))
    lines.append(_docx_paragraph(f"Generated: {doc.get('issued_date', '')}"))
    lines.append(_docx_paragraph(""))
    for p in md.split("\n"):
        p_clean = p.strip()
        if not p_clean:
            lines.append(_docx_paragraph(""))
        elif p_clean.startswith("#"):
            lines.append(_docx_paragraph(p_clean.lstrip("#").strip(), bold=True))
        else:
            lines.append(_docx_paragraph(p_clean))

    body_xml = "".join(lines)
    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{body_xml}<w:sectPr/></w:body>
</w:document>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
    return buf.getvalue()
