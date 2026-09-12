"""P1-08：租户账单简易 PDF（无第三方依赖）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _pdf_escape(text: str) -> str:
    """_pdf_escape。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_invoice_pdf_bytes(invoice: dict[str, Any], tenant_name: str = "") -> bytes:
    """生成最小可用 PDF 1.4 单页文本账单。"""
    lines = [
        "INVOICE / 账单",
        f"Tenant: {tenant_name or invoice.get('tenant_id', '')}",
        f"Invoice ID: {invoice.get('id', '')}",
        f"Status: {invoice.get('status', '')}",
        f"Amount (cents): {invoice.get('amount', 0)}",
        f"Due: {invoice.get('due_at', '')}",
        f"Paid: {invoice.get('paid_at', '') or '-'}",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "优丁建材 SaaS · 本文件为系统生成草案，正式发票以财务盖章为准。",
    ]
    y = 750
    content_parts = ["BT", "/F1 12 Tf"]
    for line in lines:
        content_parts.append(f"50 {y} Td ({_pdf_escape(str(line)[:120])}) Tj")
        content_parts.append("0 -18 Td")
        y -= 18
    content_parts.append("ET")
    stream = "\n".join(content_parts)
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode()
        + stream_bytes
        + b"\nendstream endobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    pdf = b"%PDF-1.4\n"
    xref_positions = [0]
    for obj in objects:
        xref_positions.append(len(pdf))
        pdf += obj
    xref_start = len(pdf)
    pdf += f"xref\n0 {len(xref_positions)}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for pos in xref_positions[1:]:
        pdf += f"{pos:010d} 00000 n \n".encode()
    pdf += (
        f"trailer<< /Size {len(xref_positions)} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF"
    ).encode()
    return pdf


def build_invoice_application_pdf_bytes(
    application: dict[str, Any],
    *,
    seller: Any = None,
    disclaimer: str = "",
) -> bytes:
    """开票申请回执 PDF（非增值税发票，须明确免责）。"""
    seller_name = getattr(seller, "seller_name", "") if seller else ""
    seller_tax = getattr(seller, "seller_tax_id", "") if seller else ""
    amount_yuan = (application.get("amount_cents") or 0) / 100
    inv_type = application.get("invoice_type") or ""
    type_label = "增值税专用发票" if inv_type == "vat_special" else "增值税普通发票"
    lines = [
        "开票申请回执 / INVOICE APPLICATION RECEIPT",
        "【本文件不是增值税发票，仅供申请记录】",
        f"申请单号: {application.get('id', '')}",
        f"关联订单: {application.get('order_no', '')}",
        f"申请金额(元): {amount_yuan:.2f}",
        f"发票类型: {type_label}",
        f"购方抬头: {application.get('title', '')}",
        f"购方税号: {application.get('tax_id') or '-'}",
        f"收票邮箱: {application.get('recipient_email', '')}",
        f"状态: {application.get('status', '')}",
        f"销售方(平台): {seller_name or '-'}",
        f"销售方税号: {seller_tax or '-'}",
        f"申请时间: {application.get('created_at', '')}",
        "",
        disclaimer[:400] if disclaimer else "正式发票须财务审核后在税控系统开具。",
    ]
    y = 750
    content_parts = ["BT", "/F1 11 Tf"]
    for line in lines:
        content_parts.append(f"40 {y} Td ({_pdf_escape(str(line)[:120])}) Tj")
        content_parts.append("0 -16 Td")
        y -= 16
    content_parts.append("ET")
    stream = "\n".join(content_parts)
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode()
        + stream_bytes
        + b"\nendstream endobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")
    pdf = b"%PDF-1.4\n"
    xref_positions = [0]
    for obj in objects:
        xref_positions.append(len(pdf))
        pdf += obj
    xref_start = len(pdf)
    pdf += f"xref\n0 {len(xref_positions)}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for pos in xref_positions[1:]:
        pdf += f"{pos:010d} 00000 n \n".encode()
    pdf += (
        f"trailer<< /Size {len(xref_positions)} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF"
    ).encode()
    return pdf
