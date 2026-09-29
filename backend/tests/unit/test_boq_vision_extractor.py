# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 视觉/文件抽取器测试（Site/BOQ 行缺口收口）。

覆盖：
- PDF 真文件抽取（pypdf 文本层）：含可解析行 → 输出 row dict；
- Excel 真文件抽取（openpyxl）：.xlsx 工作表 → row dict；
- CSV 字节抽取：标准库 csv；
- 图片诚实 503：无 OCR/VLM 配置 → VisionExtractionError(503, vision_ocr_not_configured)；
- 不支持文件类型 → 415；
- 扫描型 PDF（无文本层）→ 503 pdf_scan_ocr_required；
- 路由 extract-file 端点分发 + 状态机衔接（uploaded→extracted）；
- 负向：无行可解析 → 422 no_extractable_rows。
"""
from __future__ import annotations

import io
import uuid
from typing import Any
from unittest.mock import patch

import openpyxl
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.boq_import import BoqImportJob, BoqLineItem
from app.services import boq_pipeline_service as bps
from app.services.boq_vision_extractor import (
    VisionExtractionError,
    extract_file_table,
    extract_table_from_csv_bytes,
    extract_table_from_excel,
    extract_table_from_image,
    extract_table_from_pdf,
)

TENANT = "6a111111-1111-4111-8111-111111111111"


# ── 测试文件生成 ─────────────────────────────────────────────


def _make_xlsx_bytes() -> bytes:
    """生成真实 .xlsx 字节（含 BOQ 样表）。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOQ"
    ws.append(["Description", "Qty", "Unit"])
    ws.append(["Full Polished Ceramic Tile 800x800", 1200, "sqm"])
    ws.append(["Marble Slab Italian White", 300, "sqm"])
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    return buf.getvalue()


def _make_csv_bytes() -> bytes:
    return (
        "description,quantity,unit\n"
        "Full Polished Ceramic Tile 800x800,1200,sqm\n"
        "Marble Slab Italian White,300,sqm\n"
    ).encode("utf-8")


def _make_pdf_bytes() -> bytes:
    """生成含文本层的最小 PDF（用 reportlab，requirements 已含）。"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 700
    lines = [
        "Description | Qty | Unit",
        "Full Polished Ceramic Tile 800x800 | 1200 | sqm",
        "Marble Slab Italian White | 300 | sqm",
    ]
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()


def _make_scanned_pdf_bytes() -> bytes:
    """无文本层 PDF（模拟扫描件：只有图形指令、无可抽取文本）。"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    # 只画一个矩形，不写任何文本 → 无文本层
    c.rect(100, 100, 200, 100)
    c.showPage()
    c.save()
    return buf.getvalue()


def _make_png_bytes() -> bytes:
    """最小 1x1 PNG。"""
    import struct
    import zlib

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)
    raw = b"\x00\xff\x00\x00"  # filter + RGB
    idat = _chunk(b"IDAT", zlib.compress(raw))
    iend = _chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


# ── 服务层测试 ───────────────────────────────────────────────


class TestExcelExtraction:
    def test_extract_table_from_excel_real_file(self):
        data = _make_xlsx_bytes()
        rows = extract_table_from_excel(io.BytesIO(data), filename="boq.xlsx")
        assert len(rows) == 2
        assert rows[0]["raw_description"] == "Full Polished Ceramic Tile 800x800"
        assert rows[0]["normalized_quantity"] == 1200.0
        assert rows[0]["normalized_unit"] == "sqm"
        assert rows[1]["raw_description"] == "Marble Slab Italian White"
        assert rows[1]["normalized_quantity"] == 300.0

    def test_excel_rows_compatible_with_add_manual_lines(self, db_session):
        """正向：Excel 抽取的 rows 可直接进管道 uploaded→extracted。"""
        data = _make_xlsx_bytes()
        rows = extract_table_from_excel(io.BytesIO(data), filename="boq.xlsx")
        job = bps.create_job(db_session, tenant_id=TENANT, source_name="boq.xlsx")
        added = bps.add_manual_lines(db_session, job, rows, extractor="file")
        assert added == 2
        assert job.status == "extracted"
        assert job.extractor == "file"
        lines = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).all()
        assert len(lines) == 2
        desc_set = {l.normalized_description for l in lines}
        assert "Full Polished Ceramic Tile 800x800" in desc_set


class TestCsvExtraction:
    def test_extract_table_from_csv_bytes(self):
        rows = extract_table_from_csv_bytes(_make_csv_bytes(), filename="boq.csv")
        assert len(rows) == 2
        assert rows[0]["normalized_quantity"] == 1200.0
        assert rows[0]["normalized_unit"] == "sqm"

    def test_csv_dispatch_via_extract_file_table(self):
        data = _make_csv_bytes()
        rows = extract_file_table(io.BytesIO(data), filename="boq.csv")
        assert len(rows) == 2


class TestPdfExtraction:
    def test_extract_table_from_pdf_real_file(self):
        data = _make_pdf_bytes()
        rows = extract_table_from_pdf(io.BytesIO(data), filename="boq.pdf")
        assert len(rows) == 2
        assert any("Ceramic" in r["raw_description"] for r in rows)
        assert all(r["normalized_quantity"] is not None for r in rows)

    def test_scanned_pdf_raises_503_not_forged(self):
        data = _make_scanned_pdf_bytes()
        with pytest.raises(VisionExtractionError) as ei:
            extract_table_from_pdf(io.BytesIO(data), filename="scan.pdf")
        assert ei.value.status_code == 503
        assert ei.value.code == "pdf_scan_ocr_required"
        # 关键：不返回伪造 rows
        assert ei.value.message

    def test_pdf_dispatch_via_extract_file_table(self):
        data = _make_pdf_bytes()
        rows = extract_file_table(io.BytesIO(data), filename="boq.pdf")
        assert len(rows) == 2


class TestImageHonest503:
    def test_image_extraction_raises_503_when_no_ocr(self):
        data = _make_png_bytes()
        with pytest.raises(VisionExtractionError) as ei:
            extract_table_from_image(io.BytesIO(data), filename="boq.png")
        assert ei.value.status_code == 503
        assert ei.value.code == "vision_ocr_not_configured"
        assert "OCR" in ei.value.message or "视觉" in ei.value.message

    def test_image_dispatch_via_extract_file_table(self):
        data = _make_png_bytes()
        with pytest.raises(VisionExtractionError) as ei:
            extract_file_table(io.BytesIO(data), filename="boq.png")
        assert ei.value.status_code == 503
        assert ei.value.code == "vision_ocr_not_configured"


class TestUnsupportedType:
    def test_unsupported_extension_raises_415(self):
        with pytest.raises(VisionExtractionError) as ei:
            extract_file_table(io.BytesIO(b"binary"), filename="boq.docx")
        assert ei.value.status_code == 415
        assert ei.value.code == "unsupported_file_type"


class TestNoExtractableRows:
    def test_empty_csv_yields_no_rows(self):
        rows = extract_table_from_csv_bytes(b"", filename="empty.csv")
        assert rows == []

    def test_add_manual_lines_empty_rows_rejected(self, db_session):
        """负向：无 rows 时管道拒绝（不伪造）。"""
        job = bps.create_job(db_session, tenant_id=TENANT, source_name="empty.csv")
        with pytest.raises(bps.PipelineError) as ei:
            bps.add_manual_lines(db_session, job, [], extractor="file")
        assert ei.value.status_code == 422
        assert ei.value.code == "no_extractable_rows"


# ── 路由层测试（extract-file 端点） ──────────────────────────


def _build_boq_app(db_session: Any) -> FastAPI:
    """最小 app：只挂 boq_import 路由，覆盖 get_db / get_current_user。"""
    from app.api.v1.routes import boq_import

    app = FastAPI()
    app.include_router(boq_import.router, prefix="/api/v1/boq")

    fake_user = type(
        "FakeUser",
        (),
        {
            "id": str(uuid.uuid4()),
            "role": "super_admin",
            "tenant_id": None,
        },
    )()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return app


class TestExtractFileEndpoint:
    def _new_job(self, db_session) -> BoqImportJob:
        job = bps.create_job(db_session, tenant_id=TENANT, source_name="boq.xlsx")
        db_session.commit()
        return job

    def test_xlsx_upload_end_to_end(self, db_session):
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        data = _make_xlsx_bytes()
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract-file",
            files={"file": ("boq.xlsx", io.BytesIO(data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "extracted"
        assert body["data"]["lines"] == 2
        # 状态机：uploaded → extracting → extracted
        assert job.status == "extracted"
        lines = db_session.query(BoqLineItem).filter_by(boq_job_id=job.id).all()
        assert len(lines) == 2

    def test_csv_upload_end_to_end(self, db_session):
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        data = _make_csv_bytes()
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract-file",
            files={"file": ("boq.csv", io.BytesIO(data), "text/csv")},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["lines"] == 2

    def test_image_upload_honest_503(self, db_session):
        """负向：图片无 OCR → 503（不伪造）。"""
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        data = _make_png_bytes()
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract-file",
            files={"file": ("boq.png", io.BytesIO(data), "image/png")},
        )
        assert resp.status_code == 503
        body = resp.json()
        assert "vision_ocr_not_configured" in body["message"]
        # 作业仍停留在 uploaded（未被非法推进）
        assert job.status == "uploaded"

    def test_unsupported_type_415(self, db_session):
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract-file",
            files={"file": ("boq.docx", io.BytesIO(b"binary"), "application/octet-stream")},
        )
        assert resp.status_code == 415
        assert "unsupported_file_type" in resp.json()["message"]


class TestMossVlDispatchInExtractImport:
    """extract 端点：moss_vl 给 rows 时直接登记；给 file_bytes 时按文件分发。"""

    def test_moss_vl_with_rows_dispatches(self, db_session):
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        rows = [
            {"description": "Full Polished Ceramic Tile 800x800", "quantity": "1000", "unit": "sqm"},
        ]
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract",
            json={"extractor": "moss_vl", "rows": rows, "filename": "manual.png"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["lines"] == 1
        assert job.status == "extracted"

    def test_moss_vl_no_input_honest_503(self, db_session):
        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract",
            json={"extractor": "moss_vl"},
        )
        assert resp.status_code == 503
        assert "file_bytes" in resp.json()["message"]

    def test_moss_vl_with_xlsx_file_bytes_dispatches(self, db_session):
        """正向：moss_vl + file_bytes(base64 xlsx) → 真实解析。"""
        import base64

        job = self._new_job(db_session)
        app = _build_boq_app(db_session)
        client = TestClient(app)
        b64 = base64.b64encode(_make_xlsx_bytes()).decode("ascii")
        resp = client.post(
            f"/api/v1/boq/tenants/{TENANT}/imports/{job.id}/extract",
            json={"extractor": "moss_vl", "file_bytes": b64, "filename": "boq.xlsx"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["lines"] == 2
        assert job.status == "extracted"

    def _new_job(self, db_session) -> BoqImportJob:
        job = bps.create_job(db_session, tenant_id=TENANT, source_name="boq.xlsx")
        db_session.commit()
        return job
