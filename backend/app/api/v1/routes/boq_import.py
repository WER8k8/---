# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 导入管道路由（修正设计稿 模块3 / Gate G6）。

阶段门控严格：/normalize、/match、/calculate、/approve 各自校验作业当前状态，
禁止 extracted → quote 跳步（服务层 PipelineError → 4xx）。
对外话术见 services.boq_pipeline_service.human_view（不暴露内部术语）。
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.boq_import import BoqImportJob, BoqLineItem
from app.models.tenant import UserTenant
from app.models.user import User
from app.services import boq_pipeline_service as bps
from app.services.boq_vision_extractor import VisionExtractionError, extract_file_table

# FIX-30 自动注入：保留自定义前缀与标签
ROUTE_PREFIX = "/boq"
ROUTE_TAGS = ["BOQ 标书管道"]

router = APIRouter(tags=["BOQ 标书管道"])


def _ensure_tenant_access(tenant_id: str, user: User, db: Session) -> bool:
    link = (
        db.query(UserTenant)
        .filter(
            UserTenant.tenant_id == str(tenant_id),
            UserTenant.user_id == str(user.id),
            UserTenant.is_active.is_(True),
        )
        .first()
    )
    return bool(link) or user.role in ("admin", "super_admin")


def _get_job_for(db: Session, job_id: str, tenant_id: str, user: User) -> Optional[BoqImportJob]:
    job = db.query(BoqImportJob).filter(BoqImportJob.id == str(job_id)).first()
    if not job or str(job.tenant_id) != str(tenant_id):
        return None
    return job


def _err(exc: bps.PipelineError):
    return error_response(exc.status_code, exc.message)


# ---------- 创建 / 列表 / 详情 ----------


@router.post("/tenants/{tenant_id}/imports")
def create_import(
    tenant_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传标书（创建作业）。v1 支持直接带 rows（手工/表格文本抽取结果）。"""
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    try:
        job = bps.create_job(
            db,
            tenant_id=tenant_id,
            source_name=(body or {}).get("source_name"),
            defaults=(body or {}).get("defaults"),
            created_by=str(current_user.id),
        )
    except Exception as exc:  # noqa: BLE001
        return error_response(400, f"创建失败: {exc}")
    rows = (body or {}).get("rows") or []
    added = 0
    if rows:
        try:
            added = bps.add_manual_lines(db, job, rows, extractor=str((body or {}).get("extractor") or "manual"))
        except bps.PipelineError as exc:
            return _err(exc)
    return success_response(
        data={"job_id": str(job.id), "status": job.status, "lines": added},
        message="标书已上传",
    )


@router.get("/tenants/{tenant_id}/imports")
def list_imports(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    jobs = (
        db.query(BoqImportJob)
        .filter(BoqImportJob.tenant_id == str(tenant_id))
        .order_by(BoqImportJob.created_at.desc())
        .limit(100)
        .all()
    )
    return success_response(
        data={
            "items": [
                {"job_id": str(j.id), "source_name": j.source_name, "status": j.status,
                 "confidence": j.confidence}
                for j in jobs
            ]
        }
    )


@router.get("/tenants/{tenant_id}/imports/{job_id}")
def get_import(
    tenant_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    lines = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).order_by(BoqLineItem.source_row).all()
    return success_response(
        data={
            "job_id": str(job.id),
            "status": job.status,
            "human_view": bps.human_view(job, lines),
            "lines": [
                {
                    "id": str(l.id),
                    "row": l.source_row,
                    "description": l.normalized_description or l.raw_description,
                    "quantity": l.normalized_quantity,
                    "unit": l.normalized_unit,
                    "candidates": l.candidate_products,
                    "review_status": l.review_status,
                    "reject_reason": l.reject_reason,
                }
                for l in lines
            ],
            "result": job.result_json,
        }
    )


# ---------- 抽取 ----------


def _dispatch_vision_rows(
    db: Session,
    job: BoqImportJob,
    rows: list[dict[str, Any]],
    extractor: str,
    *,
    source_name: Optional[str] = None,
    source_artifact_id: Optional[str] = None,
) -> int:
    """把视觉/文件抽取出的 rows 登记进管道；无 rows 时 422（不伪造）。"""
    job.source_name = source_name or job.source_name
    if source_artifact_id:
        job.source_artifact_id = source_artifact_id
    if not rows:
        raise bps.PipelineError(422, "no_extractable_rows", "未能从文件/图片中解析出任何行项")
    return bps.add_manual_lines(db, job, rows, extractor=extractor)


@router.post("/tenants/{tenant_id}/imports/{job_id}/extract")
def extract_import(
    tenant_id: str,
    job_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """抽取行项。

    - extractor=text_table：粘贴表格文本
    - extractor=manual：直接带 rows
    - extractor=moss_vl：视觉/文件抽取分发（PDF/Excel/CSV 确定性解析；
      图片/扫描件无 OCR 时诚实 503，不伪造）
    """
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    extractor = str((body or {}).get("extractor") or "text_table")
    if extractor == "moss_vl":
        # 视觉抽取：从 body 传 file_bytes（base64）或直接带 rows；
        # 未给文件时保持诚实 503（不伪造抽取结果）
        file_bytes_b64 = (body or {}).get("file_bytes")
        filename = str((body or {}).get("filename") or "boq_upload")
        rows = (body or {}).get("rows")
        if rows:
            try:
                added = _dispatch_vision_rows(
                    db, job, list(rows), extractor,
                    source_name=filename,
                )
            except bps.PipelineError as exc:
                return _err(exc)
            return success_response(
                data={"job_id": str(job.id), "status": job.status, "lines": added},
                message="识别完成",
            )
        if not file_bytes_b64:
            return error_response(
                503, "视觉抽取需要文件输入（file_bytes）；仅文本时不支持图片抽取，不伪造结果"
            )
        import base64
        import io

        try:
            payload = base64.b64decode(file_bytes_b64, validate=True)
        except Exception as exc:  # noqa: BLE001
            return error_response(400, f"file_bytes 非合法 base64: {exc}")
        stream = io.BytesIO(payload)
        try:
            rows = extract_file_table(stream, filename=filename)
            added = _dispatch_vision_rows(db, job, rows, extractor, source_name=filename)
        except VisionExtractionError as exc:
            return error_response(exc.status_code, f"[{exc.code}] {exc.message}")
        except bps.PipelineError as exc:
            return _err(exc)
        return success_response(
            data={"job_id": str(job.id), "status": job.status, "lines": added},
            message="识别完成",
        )
    if extractor not in ("text_table", "manual"):
        return error_response(400, f"不支持的抽取器: {extractor}")
    try:
        if job.status == "uploaded":
            text = str((body or {}).get("text") or "")
            rows = bps.parse_text_table(text) if extractor == "text_table" else list((body or {}).get("rows") or [])
            if not rows:
                return error_response(422, "未能从输入中解析出任何行项")
            added = bps.add_manual_lines(db, job, rows, extractor=extractor)
        else:
            added = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).count()
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(
        data={"job_id": str(job.id), "status": job.status, "lines": added},
        message="识别完成",
    )


@router.post("/tenants/{tenant_id}/imports/{job_id}/extract-file")
def extract_import_file(
    tenant_id: str,
    job_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """文件抽取端点：上传 PDF/Excel/CSV/图片，按扩展名分发到 boq_vision_extractor。

    图片/扫描件在无 OCR/视觉模型时返回 503（诚实降级，不伪造）。
    """
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    data = file.file.read()
    import io

    stream = io.BytesIO(data)
    filename = file.filename or "boq_upload"
    try:
        rows = extract_file_table(stream, filename=filename)
        added = _dispatch_vision_rows(
            db, job, rows, extractor="file",
            source_name=filename,
            source_artifact_id=None,
        )
    except VisionExtractionError as exc:
        return error_response(exc.status_code, f"[{exc.code}] {exc.message}")
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(
        data={"job_id": str(job.id), "status": job.status, "lines": added},
        message="识别完成",
    )


# ---------- 归一 / 匹配 ----------


@router.post("/tenants/{tenant_id}/imports/{job_id}/normalize")
def normalize_import(
    tenant_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    try:
        count = bps.run_normalization(db, job)
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(data={"job_id": str(job.id), "status": job.status, "lines": count})


@router.post("/tenants/{tenant_id}/imports/{job_id}/match")
def match_import(
    tenant_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    try:
        report = bps.run_matching(db, job)
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(
        data={"job_id": str(job.id), "status": job.status, **report},
        message="匹配完成" if not report["needs_human"] else f"需要确认 {report['needs_human']} 项",
    )


# ---------- 人工复核 ----------


@router.post("/items/{item_id}/confirm")
def confirm_item(
    item_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = db.query(BoqLineItem).filter(BoqLineItem.id == str(item_id)).first()
    if not line:
        return error_response(404, "行项不存在")
    job = db.query(BoqImportJob).filter(BoqImportJob.id == line.boq_job_id).first()
    if not job or not _ensure_tenant_access(str(job.tenant_id), current_user, db):
        return error_response(404, "作业不存在或无权访问")
    product_id = str((body or {}).get("product_id") or line.selected_product_id or "")
    if not product_id:
        return error_response(400, "缺少 product_id（需选择候选产品）")
    try:
        line = bps.confirm_line(db, line, product_id)
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(data={"item_id": str(line.id), "review_status": line.review_status})


@router.post("/items/{item_id}/reject")
def reject_item(
    item_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    line = db.query(BoqLineItem).filter(BoqLineItem.id == str(item_id)).first()
    if not line:
        return error_response(404, "行项不存在")
    job = db.query(BoqImportJob).filter(BoqImportJob.id == line.boq_job_id).first()
    if not job or not _ensure_tenant_access(str(job.tenant_id), current_user, db):
        return error_response(404, "作业不存在或无权访问")
    line = bps.reject_line(db, line, str((body or {}).get("reason") or "manual_reject"))
    return success_response(data={"item_id": str(line.id), "review_status": line.review_status})


# ---------- 计算 / 放行 ----------


@router.post("/tenants/{tenant_id}/imports/{job_id}/calculate")
def calculate_import(
    tenant_id: str,
    job_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    try:
        result = bps.run_calculation(db, job, defaults=(body or {}).get("defaults"))
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(
        data={"job_id": str(job.id), "status": job.status, "result": result},
        message="核价单已生成",
    )


@router.post("/tenants/{tenant_id}/imports/{job_id}/approve")
def approve_import(
    tenant_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _ensure_tenant_access(tenant_id, current_user, db):
        return error_response(404, "租户不存在或无权访问")
    job = _get_job_for(db, job_id, tenant_id, current_user)
    if not job:
        return error_response(404, "作业不存在")
    try:
        job = bps.approve_job(db, job, approver=str(current_user.id))
    except bps.PipelineError as exc:
        return _err(exc)
    return success_response(data={"job_id": str(job.id), "status": job.status}, message="核价单已确认")
