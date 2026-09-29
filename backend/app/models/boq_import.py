# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 导入管道模型（修正设计稿 模块3 / Production Gate G6）。

状态机（设计稿 3.4，禁止 extracted → quote 跳步）：
    uploaded → extracting → extracted → normalizing → matching
            → review_required（需人工）| calculating → calculated → approved / failed

置信度门控（设计稿 3.5）：
    match_confidence ≥ 0.85 自动采用；0.60~0.85 人工确认；< 0.60 必须人工选择。
    硬条件优先：材料不兼容 / 标准不满足 / 单位无法确认 → 直接 Reject（LLM 不能覆盖）。

用户体验红线（模块 20）：对外只暴露「上传 → AI 识别 → 需要确认 N 项 → 核价单」，
extractor/confidence/trace_id 等术语仅管理员视图。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from app.core.database import UUID_TYPE, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Job 状态机 ───────────────────────────────────────────────
JOB_STATUSES = (
    "uploaded", "extracting", "extracted", "normalizing", "matching",
    "review_required", "calculating", "calculated", "approved", "failed",
)

LEGAL_JOB_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "uploaded": ("extracting", "failed"),
    "extracting": ("extracted", "failed"),
    "extracted": ("normalizing", "failed"),
    "normalizing": ("matching", "failed"),
    "matching": ("review_required", "calculating", "failed"),
    "review_required": ("calculating", "matching", "failed"),  # 人工确认后可回 matching 重评
    "calculating": ("calculated", "review_required", "failed"),
    "calculated": ("approved", "calculating"),  # approved 需人工；可重算
    "approved": (),
    "failed": ("extracting",),  # 失败可重试（回到抽取）
}

# ── Line 审核状态 ────────────────────────────────────────────
LINE_REVIEW_STATUSES = (
    "pending",          # 待匹配
    "auto_selected",    # 置信度 ≥0.85 自动采用
    "review_required",  # 0.60~0.85 人工确认
    "manual_required",  # <0.60 必须人工选择
    "confirmed",        # 人工已确认
    "rejected",         # 硬规则拒绝（材料不兼容/单位无法确认…），终态
)


class BoqImportJob(Base):
    """BOQ 标书导入作业（一次一份数据源文档）。"""

    __tablename__ = "boq_import_jobs"
    __table_args__ = (
        Index("ix_boq_jobs_tenant_status", "tenant_id", "status"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, nullable=False, index=True)
    source_name = Column(String(255), nullable=True)  # 原始文件名/标题
    source_artifact_id = Column(String(100), nullable=True)  # files/artifact 引用（视觉抽取用）
    status = Column(String(30), nullable=False, default="uploaded", index=True)

    extractor = Column(String(40), nullable=True)  # manual / text_table / moss_vl
    extractor_version = Column(String(30), nullable=True)
    confidence = Column(Float, nullable=True)  # 整单聚合置信度（行均）

    defaults_json = Column(JSON, default=dict)  # 核价默认参数（incoterms/ports/grade…）
    result_json = Column(JSON, default=dict)  # 核价单输出（行明细 + grand_total）

    error_code = Column(String(60), nullable=True)
    error_detail = Column(Text, nullable=True)
    trace_id = Column(String(100), nullable=True)

    created_by = Column(String(100), nullable=True)  # 操作人（审计）
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BoqLineItem(Base):
    """BOQ 行项：raw（抽取原貌）→ normalized（归一）→ matched（候选+置信）→ 复核终态。"""

    __tablename__ = "boq_line_items"
    __table_args__ = (
        Index("ix_boq_items_job", "boq_job_id"),
        Index("ix_boq_items_review", "review_status"),
    )

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    boq_job_id = Column(UUID_TYPE, ForeignKey("boq_import_jobs.id"), nullable=False, index=True)
    source_row = Column(Integer, nullable=False, default=0)

    raw_description = Column(Text, nullable=True)
    raw_quantity = Column(String(50), nullable=True)
    raw_unit = Column(String(30), nullable=True)

    normalized_description = Column(Text, nullable=True)
    normalized_quantity = Column(Float, nullable=True)
    normalized_unit = Column(String(20), nullable=True)  # canonical: sqm/cbm/ton/pcs/box/…

    candidate_products = Column(JSON, default=list)  # [{product_id,name,score}]
    selected_product_id = Column(UUID_TYPE, nullable=True)
    match_confidence = Column(Float, nullable=True)

    review_status = Column(String(30), nullable=False, default="pending", index=True)
    reject_reason = Column(String(255), nullable=True)
    source_evidence_ref = Column(String(255), nullable=True)  # 原文位置/页码/截图引用

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
