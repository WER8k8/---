# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Lab BFF — FE-11 站点编辑器试点草稿"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.admin_bff.user_context import load_tenant_for_user
from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.lab_site_editor_service import get_draft, save_draft

router = APIRouter()


class SiteEditorDraftBody(BaseModel):
    title: str = Field(default="", max_length=200)
    hero: str = Field(default="", max_length=2000)
    locale: str = Field(default="zh-CN", max_length=16)
    showCta: bool = True
    brandName: str = Field(default="", max_length=200)
    aboutText: str = Field(default="", max_length=4000)
    contactPhone: str = Field(default="", max_length=64)
    contactEmail: str = Field(default="", max_length=128)
    ctaLabel: str = Field(default="Get a Quote", max_length=120)
    primaryPromise: str = Field(default="", max_length=500)
    inquiryHook: str = Field(default="", max_length=500)
    stage1Title: str = Field(default="", max_length=120)
    stage1Desc: str = Field(default="", max_length=300)
    stage2Title: str = Field(default="", max_length=120)
    stage2Desc: str = Field(default="", max_length=300)
    stage3Title: str = Field(default="", max_length=120)
    stage3Desc: str = Field(default="", max_length=300)
    stage4Title: str = Field(default="", max_length=120)
    stage4Desc: str = Field(default="", max_length=300)
    knowledge1Title: str = Field(default="", max_length=200)
    knowledge1Hook: str = Field(default="", max_length=300)
    knowledge2Title: str = Field(default="", max_length=200)
    knowledge2Hook: str = Field(default="", max_length=300)
    knowledge3Title: str = Field(default="", max_length=200)
    knowledge3Hook: str = Field(default="", max_length=300)


@router.get("/site-editor")
async def read_site_editor_draft(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """read_site_editor_draft。

    参数说明：
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    tenant = load_tenant_for_user(db, user)
    return success_response(data=get_draft(db, user, tenant))


@router.put("/site-editor")
async def write_site_editor_draft(
    body: SiteEditorDraftBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """write_site_editor_draft。

    参数说明：
    :param body: 参数 body
    :param user: 参数 user
    :param db: 参数 db
    :return: 返回处理结果。
    """
    tenant = load_tenant_for_user(db, user)
    data = save_draft(db, user, tenant, body.model_dump())
    return success_response(data=data)
