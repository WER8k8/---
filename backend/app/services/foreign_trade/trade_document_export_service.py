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
