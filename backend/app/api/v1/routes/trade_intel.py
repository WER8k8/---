"""出海参谋 — 公开查询 + 超管维护。"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.trade_intel import TradeCountryCategory
from app.models.user import User
from app.services.trade_intel_data import load_market_sources, matrix_stats, full_customs_catalog
from app.services.trade_intel_customs_service import (
    customs_stats_for_category,
    enrich_blue_ocean_result,
)
from app.services.trade_intel_commercial_service import commercial_customs_stats
from app.services.trade_intel_seed import seed_trade_matrix
from app.services.trade_intel_service import (
    _resolve_category,
    blue_ocean,
    export_feasibility,
    hs_lookup,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/trade-intel", tags=["出海参谋"])


def _admin_only(user: User):
    """执行 admin_only 相关逻辑处理。
    
    :param user: 用户对象
    :return: 返回处理结果。
    """
    if user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可维护规则矩阵")
    return None


@router.get("/feasibility")
def trade_feasibility(
    message: str = Query("", description="自然语言或留空用 category+country"),
    category: str | None = Query(None),
    country: str | None = Query(None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /feasibility 请求，trade相关资源。
    
    :param message: 参数 message
    :param category: 分类
    :param country: 参数 country
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    text = message or f"{category or ''} {country or ''}"
    fr = export_feasibility(text, category=category, country=country, db=db)
    return success_response(data=fr.to_dict())


@router.get("/blue-ocean")
def trade_blue_ocean(
    message: str = Query(""),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /blue-ocean 请求，trade相关资源。
    
    :param message: 参数 message
    :param category: 分类
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    text = message or (category or "保温板蓝海")
    data = blue_ocean(text, category=category, db=db)
    cat_key = category or _resolve_category(text) or "insulation_board"
    data = enrich_blue_ocean_result(data, cat_key)
    return success_response(data=data)


@router.get("/matrix-stats")
def trade_matrix_stats(current_user: User = Depends(get_current_user)):
    """M0 矩阵规模（JSON 种子）。"""
    _ = current_user
    return success_response(data=matrix_stats())


@router.get("/market-sources")
def trade_market_sources(current_user: User = Depends(get_current_user)):
    """市场调研与海关公开数据工具索引。"""
    _ = current_user
    doc = load_market_sources()
    return success_response(
        data={
            "disclaimer": doc.get("disclaimer"),
            "sources": doc.get("sources") or [],
        }
    )


@router.get("/customs-catalog")
def trade_customs_catalog(
    category_key: str | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """全量海关公开统计（20×50），供后台与旺财同源。"""
    _ = current_user
    if category_key:
        from app.services.trade_intel_data import customs_for_category
        row = customs_for_category(category_key)
        if not row:
            return error_response(404, "品类不存在")
        return success_response(data=row)
    return success_response(data=full_customs_catalog())


@router.get("/customs-stats")
def trade_customs_stats(
    category: str = Query("insulation_board"),
    current_user: User = Depends(get_current_user),
):
    """AI-M1：海关公开统计试点（带来源）。"""
    _ = current_user
    return success_response(data=customs_stats_for_category(category))


@router.get("/commercial-stats")
def trade_commercial_stats(
    category: str = Query("insulation_board"),
    current_user: User = Depends(get_current_user),
):
    """AI-M2：商业海关 API 适配（TRADE_INTEL_M2_API_URL），失败回退 M1。"""
    _ = current_user
    return success_response(data=commercial_customs_stats(category))


@router.get("/hs")
def trade_hs(
    message: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /hs 请求，trade相关资源。
    
    :param message: 参数 message
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    return success_response(data=hs_lookup(message))


@router.get("/rules")
def list_rules(
    category_key: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /rules 请求，列出相关资源。
    
    :param category_key: 参数 category_key
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    q = db.query(TradeCountryCategory).filter(TradeCountryCategory.is_active.is_(True))
    if category_key:
        q = q.filter(TradeCountryCategory.category_key == category_key)
    rows = q.order_by(
        TradeCountryCategory.category_key,
        TradeCountryCategory.country_code,
    ).limit(1200).all()
    return success_response(
        data=[
            {
                "id": r.id,
                "category_key": r.category_key,
                "category_label": r.category_label,
                "hs_chapter": r.hs_chapter,
                "country_code": r.country_code,
                "verdict": r.verdict,
                "growth": r.growth,
                "competition": r.competition,
                "certs": json.loads(r.certs_json or "[]"),
                "notes": r.notes,
            }
            for r in rows
        ]
    )


@router.post("/rules/seed")
def seed_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /rules/seed 请求，seed相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if err := _admin_only(current_user):
        return err
    stats = seed_trade_matrix(db)
    return success_response(data=stats, message="规则矩阵已同步")
