# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO诊断工具路由 - 免费SEO诊断线索收集"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import success_response, error_response
from app.db.session import get_db
from app.models.inquiry import Inquiry


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["SEO诊断"]

router = APIRouter()


class DiagnosisLeadBody(BaseModel):
    """诊断线索提交体"""
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    phone: str = Field(..., min_length=1, max_length=50, description="手机号")


@router.get("/seo-diagnosis", tags=["SEO诊断"])
def get_seo_diagnosis():
    """获取SEO诊断状态/配置"""
    return success_response(data={"status": "idle", "diagnoses": []})


@router.post("/seo-diagnosis", tags=["SEO诊断"])
def submit_diagnosis_lead(body: DiagnosisLeadBody, db: Session = Depends(get_db)):
    """提交SEO诊断线索（姓名+手机号），保存到 inquiries 表"""
    inquiry = Inquiry(
        name=body.name,
        phone=body.phone,
        message=f"【SEO诊断】用户 {body.name}（{body.phone}）请求获取完整SEO诊断报告",
        product="SEO诊断",
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return success_response(
        data={"id": inquiry.id, "name": inquiry.name, "phone": inquiry.phone},
        message="提交成功，我们将在24小时内联系您并发送完整报告",
    )
