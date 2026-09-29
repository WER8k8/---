# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 视觉/文件抽取器 —— Site/BOQ 行「文件抽取」缺口收口。

设计口径（延续 boq_pipeline_service 红线：不伪造抽取）：
- PDF：优先按**文本型 PDF** 确定性解析（pypdf）；扫描/图片型 PDF 在无 OCR/VLM 配置时**诚实 503**，不伪造。
- Excel/CSV：按单元格确定性解析（openpyxl/csv）。
- 图片：需要 OCR/视觉模型（moss_vl 系）才能抽表格；当前未配置 → **诚实 503 `vision_ocr_not_configured`**。

输出统一为 `parse_text_table` 兼容的 row dict（raw_* + normalized_*），供
`add_manual_lines` 进入归一/匹配/计算主链路。
"""
from __future__ import annotations

import csv
import io
import os
import re
from typing import Any, BinaryIO, Optional

from app.services.boq_pipeline_service import normalize_quantity, normalize_unit


class VisionExtractionError(Exception):
    """视觉/文件抽取错误，携带 HTTP 语义。"""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


# 常见 BOQ/清单表头 → 列语义（描述/数量/单位）
_HEADER_HINTS = {
    "desc": ("description", "desc", "item", "item description", "品名", "描述", "名称", "项目", "material", "材质"),
    "qty": ("qty", "quantity", "数量", "数", "amt", "amount"),
    "unit": ("unit", "uom", "uoms", "单位", "规格单位"),
}

_DESC_RE = re.compile(r"\d+(?:\.\d+)?")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return re.sub(r"\s+", " ", s)


def _is_blank_row(cells: list[str]) -> bool:
    return all(not c.strip() for c in cells)


def _is_header_row(cells: list[str]) -> bool:
    low = [c.strip().lower() for c in cells]
    joined = " ".join(low)
    if any(h in joined for h in ("description", "item", "描述", "品名")) and (
        "qty" in joined or "quantity" in joined or "数量" in joined
    ):
        return True
    return False


def _find_column_indexes(cells: list[str]) -> tuple[int, int, int]:
    """从表头行推断（desc, qty, unit）列下标；找不到则按默认 (0,1,2)。"""
    low = [c.strip().lower() for c in cells]

    def _find(names: tuple[str, ...]) -> int:
        for i, cell in enumerate(low):
            if any(name in cell for name in names):
                return i
        return -1

    d = _find(_HEADER_HINTS["desc"])
    q = _find(_HEADER_HINTS["qty"])
    u = _find(_HEADER_HINTS["unit"])
    return (d if d >= 0 else 0, q if q >= 0 else 1, u if u >= 0 else 2)


def _cells_to_row(cells: list[str], source_row: int) -> Optional[dict[str, Any]]:
    """把一行单元格转成 row dict；无法解析（无数量）则返回 None（不伪造）。"""
    if _is_blank_row(cells):
        return None
    d, q, u = _find_column_indexes(cells) if _is_header_row(cells) else (0, 1, 2)

    # 表头行：若识别出是表头但本身没有可解析数量，跳过
    desc = cells[d] if d < len(cells) else ""
    qty_raw = cells[q] if q < len(cells) else ""
    unit_raw = cells[u] if u < len(cells) else ""
    qty = normalize_quantity(qty_raw)
    unit = normalize_unit(unit_raw)
    if not desc or qty is None:
        return None
    return {
        "source_row": source_row,
        "raw_description": _clean(desc),
        "raw_quantity": _clean(qty_raw),
        "raw_unit": _clean(unit_raw),
        "normalized_description": _clean(desc),
        "normalized_quantity": qty,
        "normalized_unit": unit,
    }


def _rows_from_table_rows(table_rows: list[list[Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, raw in enumerate(table_rows, start=1):
        cells = [_clean(c) for c in raw]
        if not cells:
            continue
        row = _cells_to_row(cells, idx)
        if row:
            out.append(row)
    return out


def extract_table_from_excel(stream: BinaryIO, *, filename: str = "boq.xlsx") -> list[dict[str, Any]]:
    """Excel(.xlsx) 表格抽取（首个含数据的 sheet）。确定性，无 AI。"""
    import openpyxl  # 惰性：避免主链导入时强依赖

    wb = openpyxl.load_workbook(stream, data_only=True, read_only=True)
    try:
        sheet = None
        for name in wb.sheetnames:
            ws = wb[name]
            if ws.max_row and ws.max_row > 1:
                sheet = ws
                break
        if sheet is None:
            sheet = wb[wb.sheetnames[0]]
        rows: list[list[Any]] = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(list(row))
        return _rows_from_table_rows(rows)
    finally:
        wb.close()


def extract_table_from_csv_bytes(data: bytes, *, filename: str = "boq.csv") -> list[dict[str, Any]]:
    """CSV/TSV 表格抽取。确定性。"""
    text = data.decode("utf-8-sig", errors="replace")
    delimiter = ","
    first_line = text.splitlines()[0] if text else ""
    if "\t" in first_line:
        delimiter = "\t"
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    return _rows_from_table_rows(rows)


def extract_table_from_pdf(stream: BinaryIO, *, filename: str = "boq.pdf") -> list[dict[str, Any]]:
    """PDF 文本层抽取（确定性，需 pypdf）。

    策略：逐页取文本，若某页含「描述+数量」样式的分隔行（| 或 Tab 或 多空格对齐），
    逐行解析为 row。纯扫描/图片型 PDF 无文本层 → 抛 VisionExtractionError(503,
    "pdf_scan_ocr_required")，**不伪造**（OCR/视觉模型未配置）。
    """
    try:
        import pypdf  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise VisionExtractionError(
            501, "pdf_backend_unavailable", f"PDF 解析库未安装（pypdf: {exc}）"
        ) from exc

    reader = pypdf.PdfReader(stream)
    rows: list[dict[str, Any]] = []
    parsed_any_page = False
    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        parsed_any_page = True
        page_rows = _rows_from_pdf_page_text(text, page_no)
        rows.extend(page_rows)
    if not parsed_any_page:
        raise VisionExtractionError(
            503,
            "pdf_scan_ocr_required",
            "PDF 无可提取文本层（疑似扫描件），需 OCR/视觉模型（未配置）；暂不伪造抽取结果",
        )
    return rows


def _rows_from_pdf_page_text(text: str, page_no: int) -> list[dict[str, Any]]:
    """从单页 PDF 文本解析「描述 | 数量 | 单位」样式行。"""
    rows: list[dict[str, Any]] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or set(line) <= {"|-+ "}:
            continue
        # 分隔符：管道 / Tab / ≥3 个空格
        if "|" in line or "\t" in line:
            parts = re.split(r"\||\t", line)
        else:
            parts = re.split(r"\s{2,}", line)
        cells = [c.strip() for c in parts if c.strip()]
        if len(cells) < 2:
            continue
        row = _cells_to_row(cells, page_no * 10000 + idx)
        if row:
            rows.append(row)
    return rows


def extract_table_from_image(stream: BinaryIO, *, filename: str = "boq.png") -> list[dict[str, Any]]:
    """图片表格抽取：需 OCR/视觉模型。当前未配置 → 诚实 503（不伪造）。"""
    # 读取字节仅用于后续接入 OSS/视觉网关；当前不落地、不假抽取
    _ = stream.read()
    raise VisionExtractionError(
        503,
        "vision_ocr_not_configured",
        "图片/扫描件表格抽取需 OCR 或视觉模型（moss_vl 系）；当前未配置，暂不伪造抽取结果",
    )


_PDF_EXTS = {".pdf"}
_XLSX_EXTS = {".xlsx", ".xlsm"}
_CSV_EXTS = {".csv", ".tsv"}
_IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def extract_file_table(stream: BinaryIO, *, filename: str) -> list[dict[str, Any]]:
    """按扩展名分发文件抽取。不支持的类型抛 415。"""
    ext = os.path.splitext(filename or "")[1].lower()
    if ext in _PDF_EXTS:
        return extract_table_from_pdf(stream, filename=filename)
    if ext in _XLSX_EXTS:
        return extract_table_from_excel(stream, filename=filename)
    if ext in _CSV_EXTS:
        data = stream.read()
        return extract_table_from_csv_bytes(data, filename=filename)
    if ext in _IMG_EXTS:
        return extract_table_from_image(stream, filename=filename)
    raise VisionExtractionError(
        415,
        "unsupported_file_type",
        f"不支持的文件类型: {ext or '(无扩展名)'}；支持 PDF/XLSX/CSV/PNG/JPG",
    )
