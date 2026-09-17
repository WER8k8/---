# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""认知智能与知识图谱路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/cognitive"
ROUTE_TAGS = ["认知智能"]

router = APIRouter()


@router.get("/")
def get_cognitive_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取认知智能概览"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "knowledge_graph_nodes": 0,
            "knowledge_graph_edges": 0,
            "qa_capability": "idle",
            "expert_rules_count": 0})


@router.get("/qa-engine")
def get_qa_engine_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取智能问答引擎状态"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "questions_answered": 0,
            "accuracy_rate": 0,
            "common_queries": [],
            "unanswered_queries": []})


@router.get("/expert-system")
def get_expert_system_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取专家系统状态"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "rules_loaded": 0,
            "inference_engine": "ready",
            "supported_domains": [
                "建材选型",
                "施工方案",
                "成本核算"]})


@router.get("/semantic-index")
def get_semantic_index_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取语义索引状态"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(
        data={
            "indexed_documents": 0,
            "index_size_mb": 0,
            "last_indexed": None,
            "searchable_fields": []})
