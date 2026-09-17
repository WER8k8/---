# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""全国县域建材SEO矩阵系统 API路由"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.content import (AIGenerationConfig, ContentTemplate,
                                GeneratedContent, InclusionStatus, Platform,
                                PlatformAccount, PlatformConfig, PublishLog,
                                PublishTask, RiskControlConfig, SystemSetting)
from app.models.region import (City, CombinatorialRule, District,
                               GeneratedKeyword, GroupKeyword, IndustryKeyword,
                               KeywordGroup, Province)
from app.models.user import User
from app.services.platform_catalog import catalog_summary
logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/seo-matrix", tags=["SEO矩阵"])


def _model_list(query, mapper_fn):
    """执行 model_list 相关数据处理。
    
    :param query: 查询条件
    :param mapper_fn: 参数 mapper_fn
    :return: 返回处理结果。
    """
    return [mapper_fn(r) for r in query]


class GenerateKeywordsBody(BaseModel):
    district_ids: Optional[List[str]] = None
    keyword_ids: Optional[List[str]] = None
    rule_ids: Optional[List[str]] = None
    rule_id: Optional[str] = None
    count: Optional[int] = None
    region_scope: Optional[str] = None


class GenerateContentBody(BaseModel):
    district_ids: Optional[List[str]] = None
    keyword_ids: Optional[List[str]] = None
    template_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    keyword_source: Optional[str] = "auto"
    count: Optional[int] = Field(default=10, ge=1, le=500)
    content_length: Optional[int] = None


class PublishTaskCreate(BaseModel):
    content_ids: List[str] = Field(..., min_length=1)
    platform_ids: Optional[List[str]] = None
    platform_id: Optional[str] = None
    account_ids: Optional[List[str]] = None
    account_id: Optional[str] = None
    publish_type: str = "immediate"
    scheduled_time: Optional[str] = None


def _run_generate_keywords(
    db: Session,
    district_ids: List[str],
    keyword_ids: List[str],
    rule_ids: Optional[List[str]],
) -> int:
    """执行 run_generate_keywords 相关逻辑处理。
    
    :param db: 数据库会话
    :param district_ids: 参数 district_ids
    :param keyword_ids: 参数 keyword_ids
    :param rule_ids: 参数 rule_ids
    :return: 返回处理结果。
    """
    if rule_ids:
        rules = db.query(CombinatorialRule).filter(
            CombinatorialRule.id.in_(rule_ids)).all()
    else:
        rules = db.query(CombinatorialRule).filter_by(is_active=True).all()
    if not rules:
        return 0
    districts = db.query(District).filter(District.id.in_(district_ids)).all()
    keywords = db.query(IndustryKeyword).filter(
        IndustryKeyword.id.in_(keyword_ids)).all()
    generated_keywords = [
        rule.template.format(district=district.name, product=keyword.keyword)
        for district in districts
        for keyword in keywords
        for rule in rules
    ]
    if generated_keywords:
        existing_keywords = set(
            row[0]
            for row in db.query(GeneratedKeyword.keyword)
            .filter(GeneratedKeyword.keyword.in_(generated_keywords))
            .all()
        )
    else:
        existing_keywords = set()
    generated_count = 0
    for district in districts:
        for keyword in keywords:
            for rule in rules:
                generated_keyword = rule.template.format(
                    district=district.name,
                    product=keyword.keyword,
                )
                exists = generated_keyword in existing_keywords
                if not exists:
                    db.add(
                        GeneratedKeyword(
                            keyword=generated_keyword,
                            district_id=district.id,
                            industry_keyword_id=keyword.id,
                            rule_id=rule.id,
                        )
                    )
                    generated_count += 1
    db.commit()
    return generated_count


# ==================== 模块1：系统全局设置 ====================


@router.get("/settings")
def get_settings(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    """获取系统全局设置"""
    settings = {}
    for setting in db.query(SystemSetting).all():
        if setting.setting_type == "json":
            settings[setting.setting_key] = json.loads(setting.setting_value)
        elif setting.setting_type == "int":
            settings[setting.setting_key] = int(setting.setting_value)
        elif setting.setting_type == "float":
            settings[setting.setting_key] = float(setting.setting_value)
        elif setting.setting_type == "bool":
            settings[setting.setting_key] = setting.setting_value.lower() == "true"
        else:
            settings[setting.setting_key] = setting.setting_value
    return success_response(data=settings)


@router.put("/settings")
def update_settings(
        settings: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """更新系统全局设置"""
    for key, value in settings.items():
        setting_type, setting_value = "string", str(value)
        if isinstance(value, dict):
            setting_value, setting_type = json.dumps(value), "json"
        elif isinstance(value, bool):
            setting_value, setting_type = str(value).lower(), "bool"
        elif isinstance(value, int):
            setting_type = "int"
        elif isinstance(value, float):
            setting_type = "float"

        s = db.query(SystemSetting).filter_by(setting_key=key).first()
        if s:
            s.setting_value, s.setting_type = setting_value, setting_type
        else:
            db.add(SystemSetting(setting_key=key, setting_value=setting_value, setting_type=setting_type))
    db.commit()
    return success_response(message="设置更新成功")


@router.get("/ai-config")
def get_ai_config(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    """获取AI生成配置"""
    configs = db.query(AIGenerationConfig).all()
    result = []
    for config in configs:
        result.append(
            {
                "id": config.id,
                "config_name": config.config_name,
                "model_name": config.model_name,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "creativity_level": config.creativity_level,
                "similarity_threshold": config.similarity_threshold,
                "compliance_check": config.compliance_check,
            }
        )
    return success_response(data=result)


@router.post("/ai-config")
def create_ai_config(
        config: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建AI生成配置"""
    new_config = AIGenerationConfig(
        config_name=config["config_name"],
        model_name=config.get("model_name", "default"),
        max_tokens=config.get("max_tokens", 2000),
        temperature=config.get("temperature", 0.7),
        creativity_level=config.get("creativity_level", "medium"),
        similarity_threshold=config.get("similarity_threshold", 0.1),
        compliance_check=config.get("compliance_check", True),
    )
    db.add(new_config)
    db.commit()
    return success_response(data={"id": new_config.id}, message="配置创建成功")


# ==================== 模块2：全国地域词库管理 ====================


@router.get("/provinces")
def list_provinces(db: Session = Depends(get_db)):
    """获取省份列表"""
    provinces = db.query(Province).filter_by(is_active=True).all()
    return success_response(data=_model_list(provinces, lambda p: {"id": p.id, "code": p.code, "name": p.name, "name_en": p.name_en}))


@router.get("/provinces/{province_id}/cities")
def list_cities(province_id: str, db: Session = Depends(get_db)):
    """获取指定省份的城市列表"""
    cities = db.query(City).filter_by(province_id=province_id, is_active=True).all()
    return success_response(data=_model_list(cities, lambda c: {"id": c.id, "code": c.code, "name": c.name, "name_en": c.name_en, "province_id": c.province_id}))


@router.get("/cities/{city_id}/districts")
def list_districts(city_id: str, db: Session = Depends(get_db)):
    """获取指定城市的区县列表"""
    districts = db.query(District).filter_by(city_id=city_id, is_active=True).all()
    return success_response(data=_model_list(districts, lambda d: {"id": d.id, "code": d.code, "name": d.name, "name_en": d.name_en, "city_id": d.city_id, "province_id": d.province_id, "is_disabled": d.is_disabled}))


@router.get("/districts")
def search_districts(
    province_id: Optional[str] = None,
    city_id: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """搜索区县"""
    query = db.query(District).filter_by(is_active=True)
    if province_id:
        query = query.filter_by(province_id=province_id)
    if city_id:
        query = query.filter_by(city_id=city_id)
    if keyword:
        query = query.filter(District.name.like(f"%{keyword}%"))

    total = query.count()
    districts = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for d in districts:
        result.append(
            {
                "id": d.id,
                "code": d.code,
                "name": d.name,
                "city_id": d.city_id,
                "province_id": d.province_id,
                "is_disabled": d.is_disabled,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.put("/districts/{district_id}/toggle")
def toggle_district(
        district_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """切换区县启用/禁用状态"""
    district = db.query(District).filter_by(id=district_id).first()
    if not district:
        return error_response(404, "区县不存在")
    district.is_disabled = not district.is_disabled
    db.commit()
    return success_response(data={"is_disabled": district.is_disabled})


@router.get("/keyword-groups")
def list_keyword_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /keyword-groups 请求，列出相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    groups = db.query(KeywordGroup).filter_by(is_active=True).all()
    group_ids = [g.id for g in groups]
    count_rows = {}
    if group_ids:
        count_rows = dict(
            db.query(GroupKeyword.group_id, func.count(GroupKeyword.id))
            .filter(GroupKeyword.group_id.in_(group_ids))
            .group_by(GroupKeyword.group_id)
            .all()
        )
    items = []
    for g in groups:
        cnt = count_rows.get(g.id, 0) or 0
        items.append({"id": g.id, "name": g.name, "count": int(cnt)})
    return success_response(
        data={
            "items": items,
            "total": len(items),
            "page": 1,
            "page_size": len(items)})


class RegionKeywordCreate(BaseModel):
    district_id: str
    keyword: str
    group_id: Optional[str] = None
    remark: Optional[str] = None


@router.get("/region-keywords")
def list_region_keywords(
    province_id: Optional[str] = None,
    city_id: Optional[str] = None,
    district_id: Optional[str] = None,
    group_ids: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /region-keywords 请求，列出相关资源。
    
    :param province_id: 参数 province_id
    :param city_id: 参数 city_id
    :param district_id: 参数 district_id
    :param group_ids: 参数 group_ids
    :param page: 页码
    :param page_size: 每页条数
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    q = (
        db.query(GeneratedKeyword, District, Province, City)
        .join(District, GeneratedKeyword.district_id == District.id)
        .join(Province, District.province_id == Province.id)
        .join(City, District.city_id == City.id)
    )
    if province_id:
        q = q.filter(Province.id == province_id)
    if city_id:
        q = q.filter(City.id == city_id)
    if district_id:
        q = q.filter(District.id == district_id)
    if group_ids:
        gids = [x.strip() for x in group_ids.split(",") if x.strip()]
        if gids:
            q = q.filter(
                db.query(
                    GroupKeyword.id) .filter(
                    GroupKeyword.keyword_id == GeneratedKeyword.industry_keyword_id,
                    GroupKeyword.group_id.in_(gids),
                ) .exists())
    total = q.count()
    rows = q.order_by(
        GeneratedKeyword.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    items = []
    row_keyword_ids = [gk.industry_keyword_id for gk, _, _, _ in rows]
    glink_map = {}
    if row_keyword_ids:
        glink_list = (
            db.query(GroupKeyword, KeywordGroup)
            .join(KeywordGroup, GroupKeyword.group_id == KeywordGroup.id)
            .filter(GroupKeyword.keyword_id.in_(row_keyword_ids))
            .all()
        )
        for gk_link, kg in glink_list:
            if gk_link.keyword_id not in glink_map:
                glink_map[gk_link.keyword_id] = (gk_link, kg)
    for gk, d, prov, city in rows:
        gname = ""
        glink = glink_map.get(gk.industry_keyword_id)
        if glink:
            gname = glink[1].name
        items.append(
            {
                "id": gk.id,
                "keyword": gk.keyword,
                "province_id": str(prov.id),
                "city_id": str(city.id),
                "district_id": str(d.id),
                "province_name": prov.name,
                "city_name": city.name,
                "district_name": d.name,
                "group_id": glink[1].id if glink else "",
                "group_name": gname,
                "is_active": gk.is_valid,
                "remark": "",
            }
        )
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.post("/region-keywords")
def create_region_keyword(
    body: RegionKeywordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /region-keywords 请求，创建相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    ik = db.query(IndustryKeyword).filter_by(
        keyword=body.keyword.strip(), is_active=True).first()
    if not ik:
        ik = IndustryKeyword(
            keyword=body.keyword.strip(),
            keyword_type="product",
            search_volume=0,
            difficulty=0.0,
            category="",
        )
        db.add(ik)
        db.flush()
    if body.group_id:
        exists_link = db.query(GroupKeyword).filter_by(
            group_id=body.group_id, keyword_id=ik.id).first()
        if not exists_link:
            db.add(GroupKeyword(group_id=body.group_id, keyword_id=ik.id))
    rule = db.query(CombinatorialRule).filter_by(
        is_active=True).order_by(
        CombinatorialRule.priority).first()
    if not rule:
        return error_response(400, "请先创建组词规则")
    district = db.query(District).filter_by(id=body.district_id).first()
    if not district:
        return error_response(404, "区县不存在")
    text = rule.template.format(district=district.name, product=ik.keyword)
    exists = db.query(GeneratedKeyword).filter_by(keyword=text).first()
    if exists:
        return error_response(400, "该地域组合已存在")
    row = GeneratedKeyword(
        keyword=text,
        district_id=district.id,
        industry_keyword_id=ik.id,
        rule_id=rule.id,
    )
    db.add(row)
    db.commit()
    return success_response(data={"id": row.id}, message="创建成功")


@router.put("/region-keywords/{row_id}")
def update_region_keyword(
    row_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /region-keywords/{row_id} 请求，更新相关资源。
    
    :param row_id: 参数 row_id
    :param data: 请求数据
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(GeneratedKeyword).filter_by(id=row_id).first()
    if not row:
        return error_response(404, "记录不存在")
    if "is_active" in data:
        row.is_valid = bool(data["is_active"])
    if "district_id" in data and data["district_id"]:
        row.district_id = data["district_id"]
    db.commit()
    return success_response(message="已更新")


@router.delete("/region-keywords/{row_id}")
def delete_region_keyword(
    row_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 DELETE /region-keywords/{row_id} 请求，删除相关资源。
    
    :param row_id: 参数 row_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(GeneratedKeyword).filter_by(id=row_id).first()
    if not row:
        return error_response(404, "记录不存在")
    db.delete(row)
    db.commit()
    return success_response(message="已删除")


@router.post("/region-keywords/import")
def import_region_keywords_placeholder(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /region-keywords/import 请求，导入相关资源。
    
    :param file: 上传文件
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    _ = file.filename
    return success_response(
        data={"imported": 0},
        message="批量导入已预留接口，请暂用单条添加或行业关键词管理",
    )


# ==================== 模块3：行业关键词库与AI组词 ====================


@router.get("/industry-keywords")
def list_industry_keywords(
        keyword_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """获取行业关键词列表"""
    query = db.query(IndustryKeyword).filter_by(is_active=True)
    if keyword_type:
        query = query.filter_by(keyword_type=keyword_type)

    total = query.count()
    keywords = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for kw in keywords:
        result.append(
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "keyword_type": kw.keyword_type,
                "search_volume": kw.search_volume,
                "difficulty": kw.difficulty,
                "category": kw.category,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.post("/industry-keywords")
def create_industry_keyword(
        keyword: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建行业关键词"""
    new_kw = IndustryKeyword(
        keyword=keyword["keyword"],
        keyword_type=keyword.get("keyword_type", "product"),
        search_volume=keyword.get("search_volume", 0),
        difficulty=keyword.get("difficulty", 0.0),
        category=keyword.get("category"),
    )
    db.add(new_kw)
    db.commit()
    return success_response(data={"id": new_kw.id}, message="关键词创建成功")


@router.put("/industry-keywords/{keyword_id}")
def update_industry_keyword(
    keyword_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /industry-keywords/{keyword_id} 请求，更新相关资源。
    
    :param keyword_id: 参数 keyword_id
    :param data: 请求数据
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    kw = db.query(IndustryKeyword).filter_by(id=keyword_id).first()
    if not kw:
        return error_response(404, "关键词不存在")
    if "keyword" in data:
        kw.keyword = data["keyword"]
    if "keyword_type" in data:
        kw.keyword_type = data["keyword_type"]
    if "search_volume" in data:
        kw.search_volume = int(data["search_volume"])
    if "difficulty" in data:
        kw.difficulty = float(data["difficulty"])
    if "category" in data:
        kw.category = data["category"]
    if "is_active" in data:
        kw.is_active = bool(data["is_active"])
    db.commit()
    return success_response(message="更新成功")


@router.delete("/industry-keywords/{keyword_id}")
def delete_industry_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 DELETE /industry-keywords/{keyword_id} 请求，删除相关资源。
    
    :param keyword_id: 参数 keyword_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    kw = db.query(IndustryKeyword).filter_by(id=keyword_id).first()
    if not kw:
        return error_response(404, "关键词不存在")
    kw.is_active = False
    db.commit()
    return success_response(message="已删除")


@router.get("/combinatorial-rules")
def list_combinatorial_rules(db: Session = Depends(get_db)):
    """获取组词规则列表"""
    rules = db.query(CombinatorialRule).filter_by(
        is_active=True).order_by(
        CombinatorialRule.priority).all()
    result = []
    for rule in rules:
        result.append(
            {
                "id": rule.id,
                "name": rule.name,
                "template": rule.template,
                "description": rule.description,
                "priority": rule.priority,
            }
        )
    return success_response(data=result)


@router.post("/combinatorial-rules")
def create_combinatorial_rule(
        rule: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建组词规则"""
    new_rule = CombinatorialRule(
        name=rule["name"],
        template=rule["template"],
        description=rule.get("description"),
        priority=rule.get("priority", 10),
    )
    db.add(new_rule)
    db.commit()
    return success_response(data={"id": new_rule.id}, message="规则创建成功")


@router.put("/combinatorial-rules/{rule_id}")
def update_combinatorial_rule(
    rule_id: str,
    rule: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /combinatorial-rules/{rule_id} 请求，更新相关资源。
    
    :param rule_id: 参数 rule_id
    :param rule: 参数 rule
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    r = db.query(CombinatorialRule).filter_by(id=rule_id).first()
    if not r:
        return error_response(404, "规则不存在")
    if "name" in rule:
        r.name = rule["name"]
    if "template" in rule:
        r.template = rule["template"]
    if "description" in rule:
        r.description = rule["description"]
    if "priority" in rule:
        r.priority = int(rule["priority"])
    db.commit()
    return success_response(message="规则已更新")


@router.post("/generate-keywords")
def generate_keywords(
    body: GenerateKeywordsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成关键词（支持前端仅传 rule_id 时自动取全部区县与行业词）。"""
    rule_ids = list(body.rule_ids or [])
    if body.rule_id:
        rule_ids.append(body.rule_id)
    district_ids = body.district_ids or [
        str(d.id) for d in db.query(District).filter_by(is_active=True).all()]
    keyword_ids = body.keyword_ids or [str(k.id) for k in db.query(
        IndustryKeyword).filter_by(is_active=True).all()]
    if not district_ids or not keyword_ids:
        return error_response(400, "缺少区县或行业关键词基础数据，请先在地域词库中维护")
    generated_count = _run_generate_keywords(
        db, district_ids, keyword_ids, rule_ids or None)
    return success_response(
        data={"generated_count": generated_count},
        message=f"成功生成 {generated_count} 条关键词",
    )


@router.post("/combinatorial-rules/{rule_id}/regenerate")
def regenerate_keywords_for_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /combinatorial-rules/{rule_id}/regenerate 请求，regenerate相关资源。
    
    :param rule_id: 参数 rule_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    district_ids = [str(d.id) for d in db.query(
        District).filter_by(is_active=True).all()]
    keyword_ids = [str(k.id) for k in db.query(
        IndustryKeyword).filter_by(is_active=True).all()]
    if not district_ids or not keyword_ids:
        return error_response(400, "缺少区县或行业关键词基础数据")
    generated_count = _run_generate_keywords(
        db, district_ids, keyword_ids, [rule_id])
    return success_response(
        data={"generated_count": generated_count},
        message=f"成功生成 {generated_count} 条关键词",
    )


@router.get("/generated-keywords")
def list_generated_keywords(
    district_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    valid_only: bool = True,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """获取生成的关键词列表"""
    query = db.query(GeneratedKeyword)
    if district_id:
        query = query.filter_by(district_id=district_id)
    if rule_id:
        query = query.filter_by(rule_id=rule_id)
    if valid_only:
        query = query.filter_by(is_valid=True)

    total = query.count()
    keywords = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for kw in keywords:
        result.append(
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "district_id": kw.district_id,
                "industry_keyword_id": kw.industry_keyword_id,
                "rule_id": kw.rule_id,
                "is_valid": kw.is_valid,
                "is_used": kw.is_used,
                "search_volume": kw.search_volume or 0,
                "difficulty": kw.difficulty or 0.0,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.delete("/generated-keywords/{keyword_row_id}")
def delete_generated_keyword_row(
    keyword_row_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 DELETE /generated-keywords/{keyword_row_id} 请求，删除相关资源。
    
    :param keyword_row_id: 参数 keyword_row_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(GeneratedKeyword).filter_by(id=keyword_row_id).first()
    if not row:
        return error_response(404, "记录不存在")
    db.delete(row)
    db.commit()
    return success_response(message="已删除")


class BatchIdsBody(BaseModel):
    ids: List[str] = Field(..., min_length=1)


@router.post("/generated-keywords/batch-delete")
def batch_delete_generated_keywords(
    body: BatchIdsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /generated-keywords/batch-delete 请求，batch相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    q = db.query(GeneratedKeyword).filter(GeneratedKeyword.id.in_(body.ids))
    n = q.delete(synchronize_session=False)
    db.commit()
    return success_response(data={"deleted": n}, message=f"已删除 {n} 条")


# ==================== 模块4：AI文案模板与全自动生成 ====================


@router.get("/content-templates")
def list_content_templates(
        template_type: Optional[str] = None,
        db: Session = Depends(get_db)):
    """获取文案模板列表"""
    query = db.query(ContentTemplate).filter_by(is_active=True)
    if template_type:
        query = query.filter_by(template_type=template_type)

    templates = query.order_by(ContentTemplate.priority).all()
    result = []
    for tpl in templates:
        result.append(
            {
                "id": tpl.id,
                "name": tpl.name,
                "description": tpl.description,
                "template_type": tpl.template_type,
                "variables": tpl.variables,
                "priority": tpl.priority,
            }
        )
    return success_response(data=result)


@router.post("/content-templates")
def create_content_template(
        template: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建文案模板"""
    new_tpl = ContentTemplate(
        name=template["name"],
        description=template.get("description") or template.get("remark"),
        template_type=template.get("template_type") or template.get(
            "category",
            "product"),
        content=template["content"],
        variables=template.get(
            "variables",
            []),
        priority=template.get(
            "priority",
            10),
    )
    db.add(new_tpl)
    db.commit()
    return success_response(data={"id": new_tpl.id}, message="模板创建成功")


@router.post("/generate-content")
def generate_content(
    body: GenerateContentBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 生成文案（兼容前端 keyword_source / count 简写）。"""
    from app.services.tenant_product_profile_service import (
        ProductProfileRequiredError,
        require_product_profile_for_content,
    )
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    tenant_id = resolve_tenant_id_for_user(db, current_user)
    if tenant_id:
        try:
            require_product_profile_for_content(db, str(tenant_id))
        except ProductProfileRequiredError as exc:
            return error_response(400, str(exc))

    tid = body.template_id
    if tid:
        template = db.query(ContentTemplate).filter_by(id=tid).first()
        if not template:
            return error_response(404, "模板不存在")
    else:
        template = db.query(ContentTemplate).filter_by(is_active=True).first()
        if not template:
            return error_response(404, "没有可用的模板")

    pairs: List[Tuple[District, GeneratedKeyword]] = []
    if body.district_ids and body.keyword_ids:
        districts = db.query(District).filter(
            District.id.in_(body.district_ids)).all()
        gks = db.query(GeneratedKeyword).filter(
            GeneratedKeyword.id.in_(body.keyword_ids)).all()
        for d in districts:
            for gk in gks:
                if gk.district_id == d.id:
                    pairs.append((d, gk))
    else:
        q = db.query(GeneratedKeyword).filter_by(is_valid=True)
        manual = body.keywords or []
        if isinstance(manual, str):
            manual = [x.strip() for x in manual.split("\n") if x.strip()]
        if manual and body.keyword_source == "manual":
            q = q.filter(GeneratedKeyword.keyword.in_(manual))
        gks = q.limit(int(body.count or 10)).all()
        # 批量加载district
        district_ids = [gk.district_id for gk in gks if gk.district_id]
        district_map = {
            d.id: d
            for d in db.query(District)
            .filter(District.id.in_(district_ids))
            .all()
        }
        for gk in gks:
            d = district_map.get(gk.district_id)
            if d:
                pairs.append((d, gk))

    generated_count = 0
    for district, keyword in pairs:
        title = f"{district.name} {keyword.keyword}"
        try:
            content = template.content.format(
                district_name=district.name,
                keyword=keyword.keyword,
                brand="示例建材",
                website="https://www.example-buildmat.com",
                phone="400-888-8888",
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("SEO内容生成模板应用失败，使用默认模板: %s", e)
            content = template.content.replace(
                "{district_name}", district.name).replace(
                "{keyword}", keyword.keyword)

        new_content = GeneratedContent(
            title=title,
            content=content,
            district_id=district.id,
            keyword_id=keyword.id,
            template_id=template.id,
            word_count=len(content),
            status="pending",
        )
        db.add(new_content)
        generated_count += 1

    db.commit()
    return success_response(
        data={"generated_count": generated_count},
        message=f"成功生成 {generated_count} 篇文案",
    )


@router.get("/generated-contents")
def list_generated_contents(
    district_id: Optional[str] = None,
    template_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """获取生成的文案列表"""
    query = db.query(GeneratedContent)
    if district_id:
        query = query.filter_by(district_id=district_id)
    if template_id:
        query = query.filter_by(template_id=template_id)
    if status:
        query = query.filter_by(status=status)

    total = query.count()
    contents = query.offset((page - 1) * page_size).limit(page_size).all()
    content_kw_ids = [c.keyword_id for c in contents if c.keyword_id]
    gk_map = {}
    if content_kw_ids:
        gk_map = {
            gk.id: gk
            for gk in db.query(GeneratedKeyword)
            .filter(GeneratedKeyword.id.in_(content_kw_ids))
            .all()
        }
    result = []
    for content in contents:
        gk = gk_map.get(content.keyword_id)
        result.append(
            {
                "id": content.id,
                "title": content.title,
                "keyword": gk.keyword if gk else "",
                "district_id": content.district_id,
                "keyword_id": content.keyword_id,
                "template_id": content.template_id,
                "word_count": content.word_count,
                "status": content.status,
                "similarity_rate": content.similarity_rate,
                "created_at": content.created_at,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/generated-contents/{content_id}")
def get_content_detail(content_id: str, db: Session = Depends(get_db)):
    """获取文案详情"""
    content = db.query(GeneratedContent).filter_by(id=content_id).first()
    if not content:
        return error_response(404, "文案不存在")

    return success_response(
        data={
            "id": content.id,
            "title": content.title,
            "content": content.content,
            "district_id": content.district_id,
            "keyword_id": content.keyword_id,
            "template_id": content.template_id,
            "word_count": content.word_count,
            "status": content.status,
            "similarity_rate": content.similarity_rate,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
        }
    )


@router.put("/content-templates/{template_id}")
def update_content_template(
    template_id: str,
    template: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /content-templates/{template_id} 请求，更新相关资源。
    
    :param template_id: 参数 template_id
    :param template: 参数 template
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    tpl = db.query(ContentTemplate).filter_by(id=template_id).first()
    if not tpl:
        return error_response(404, "模板不存在")
    if "name" in template:
        tpl.name = template["name"]
    if "content" in template:
        tpl.content = template["content"]
    if "description" in template or "remark" in template:
        tpl.description = template.get("description") or template.get("remark")
    if "template_type" in template or "category" in template:
        tpl.template_type = template.get("template_type") or template.get(
            "category", tpl.template_type)
    if "priority" in template:
        tpl.priority = int(template["priority"])
    if "variables" in template:
        tpl.variables = template["variables"]
    db.commit()
    return success_response(message="模板已更新")


@router.delete("/generated-contents/{content_id}")
def delete_generated_content(
    content_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 DELETE /generated-contents/{content_id} 请求，删除相关资源。
    
    :param content_id: 参数 content_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(GeneratedContent).filter_by(id=content_id).first()
    if not row:
        return error_response(404, "文案不存在")
    db.delete(row)
    db.commit()
    return success_response(message="已删除")


@router.post("/generated-contents/{content_id}/publish")
def mark_content_published(
    content_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /generated-contents/{content_id}/publish 请求，标记相关资源。
    
    :param content_id: 参数 content_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(GeneratedContent).filter_by(id=content_id).first()
    if not row:
        return error_response(404, "文案不存在")
    row.status = "published"
    db.commit()
    return success_response(message="已标记为发布")


# ==================== 模块5：多平台账号管理与AI分发中心 ====================


@router.get("/accounts")
def list_accounts_frontend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 使用的账号列表接口（GET /accounts）。"""
    from app.services.platform_account_service import (
        list_active_accounts,
        resolve_tenant_scope,
        serialize_account_for_frontend,
    )
    tenant_id = resolve_tenant_scope(db, current_user)
    accounts = list_active_accounts(db, tenant_id=tenant_id)
    result = [serialize_account_for_frontend(db, acc) for acc in accounts]
    return success_response(data=result)


@router.post("/accounts")
def create_account_frontend(
    account: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 使用的账号创建接口（POST /accounts）。
    支持 configs 字段（微信 AppID/AppSecret 等）。
    """
    from app.services.platform_account_service import (
        resolve_tenant_scope,
        upsert_bound_account,
    )
    from app.services.platform_catalog import resolve_or_create_platform_by_name
    from app.services.platform_sync_service import (
        SOURCE_CONNECT,
        apply_account_provision_defaults,
        sync_customer_platform_to_admin,
    )
    platform_id = (account.get("platform") or account.get("platform_id") or "").strip()
    platform_name = (account.get("platform_name") or "").strip()
    platform = None
    if platform_id:
        platform = db.query(Platform).filter_by(id=platform_id).first()
    if not platform and platform_name:
        platform = resolve_or_create_platform_by_name(
            db,
            platform_name,
            region=str(account.get("region") or "cn"),
            content_type=str(account.get("content_type") or "article"),
        )
    if not platform:
        return error_response(400, "平台不存在，请填写 platform 或 platform_name")

    tenant_id = resolve_tenant_scope(db, current_user)
    apply_account_provision_defaults(
        account, platform, tenant_id=tenant_id, db=db
    )
    new_acc, created = upsert_bound_account(
        db,
        tenant_id=tenant_id,
        platform=platform,
        payload=account,
    )
    sync_customer_platform_to_admin(
        db,
        tenant_id=tenant_id,
        platform=platform,
        source=SOURCE_CONNECT,
        is_new_platform=False,
        nurture_rules=account.get("nurture"),
        browser_profile_id=account.get("browser_profile_id"),
    )
    db.commit()
    db.refresh(new_acc)
    nurture = account.get("nurture") or {}
    from app.services import social_nurture_service as nurture_svc
    if nurture and created:
        nurture_svc.create_cycle(
            tenant_id=tenant_id or str(current_user.id),
            platform=platform.name,
            account_label=new_acc.account_name or new_acc.username or "",
            notes=f"warmup={nurture.get('warmup_days', 14)}d",
        )

    account_name = account.get("account_name") or account.get("username", "")
    return success_response(
        data={
            "id": new_acc.id,
            "platform": str(platform.id),
            "username": new_acc.username or account_name,
            "tenant_id": new_acc.tenant_id,
            "nurture": account.get("nurture"),
            "browser_profile_id": account.get("browser_profile_id"),
        },
        message="账号连接成功" if created else "账号已更新",
    )


@router.post("/platforms")
def create_custom_platform(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """客户自填平台名称（不在预置目录时创建 custom 平台，不锁死入口）。"""
    from app.services.platform_account_service import resolve_tenant_scope
    from app.services.platform_catalog import resolve_or_create_platform_by_name
    from app.services.platform_sync_service import (
        SOURCE_CUSTOM,
        sync_customer_platform_to_admin,
    )
    name = (body.get("name") or body.get("platform_name") or "").strip()
    if not name:
        return error_response(400, "请填写平台名称")
    region = body.get("region") or "cn"
    content_type = body.get("content_type") or "article"
    existed = db.query(Platform).filter(Platform.name == name).first() is not None
    try:
        p = resolve_or_create_platform_by_name(
            db, name, region=str(region), content_type=str(content_type)
        )
        tenant_id = resolve_tenant_scope(db, current_user)
        sync_customer_platform_to_admin(
            db,
            tenant_id=tenant_id,
            platform=p,
            source=SOURCE_CUSTOM,
            is_new_platform=not existed,
        )
        db.commit()
        db.refresh(p)
    except ValueError as e:
        return error_response(400, str(e))
    return success_response(
        data={
            "id": p.id,
            "name": p.name,
            "platform_type": p.platform_type,
            "region": p.region or "cn",
            "content_type": p.content_type or "article",
            "login_hint": _platform_login_hint(p.name, p.region or "cn"),
        },
        message="平台已添加",
    )


@router.get("/platforms")
def list_platforms(db: Session = Depends(get_db)):
    """获取平台列表（含国内/海外 region；空库时自动 seed 40 平台）"""
    summary = catalog_summary(db)
    if summary.get("total", 0) == 0:
        from app.services.platform_alignment_service import seed_full_platforms
        seed_full_platforms(db)

    platforms = db.query(Platform).filter_by(is_active=True).order_by(
        Platform.region, Platform.name
    ).all()
    from app.services.publish_capability_registry import video_publish_capability
    from app.services.publish_dispatch_service import publisher_key_for_platform
    result = []
    for p in platforms:
        pub_key = publisher_key_for_platform(p)
        video_cap = video_publish_capability(platform_name=p.name, publisher_key=pub_key)
        result.append(
            {
                "id": p.id,
                "name": p.name,
                "platform_type": p.platform_type,
                "region": getattr(p, "region", None) or "cn",
                "content_type": getattr(p, "content_type", None) or "article",
                "icon": p.icon,
                "base_url": p.base_url,
                "has_api": p.has_api,
                "login_hint": _platform_login_hint(p.name, p.region or "cn"),
                "video_publish_tier": video_cap["tier"],
                "video_publish_selectable": video_cap["selectable"],
                "video_publish_label": video_cap["label"],
                "video_publish_reason": video_cap["reason"],
            }
        )
    return success_response(data=result)


def _platform_login_hint(name: str, region: str) -> str:
    """执行 platform_login_hint 相关逻辑处理。
    
    :param name: 名称
    :param region: 参数 region
    :return: 返回处理结果。
    """
    if name == "微信公众号":
        return "wechat_api"
    if name in ("知乎", "头条号", "百家号", "简书", "Medium", "WordPress.com", "Blogger"):
        return "username_password"
    if name in ("LinkedIn", "Facebook", "Instagram", "X", "YouTube", "TikTok"):
        return "oauth_token"
    if region == "global":
        return "oauth_token"
    if name in ("新浪微博", "微博", "小红书"):
        return "phone_password"
    return "username_password"


@router.get("/platform-accounts")
def list_platform_accounts(
        platform_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取平台账号列表"""
    from app.services.platform_account_service import credential_status

    query = db.query(PlatformAccount).filter_by(is_active=True)
    if platform_id:
        query = query.filter_by(platform_id=platform_id)

    accounts = query.all()
    platforms = {str(p.id): p for p in db.query(Platform).all()}
    result = []
    for acc in accounts:
        platform = platforms.get(str(acc.platform_id))
        result.append(
            {
                "id": acc.id,
                "platform_id": acc.platform_id,
                "platform_name": getattr(platform, "name", None),
                "account_name": acc.account_name,
                "username": acc.username,
                "email": acc.email,
                "login_status": acc.login_status,
                "last_login_at": acc.last_login_at,
                # 凭证只回字段名与掩码，绝不回传密钥原文
                "credential_status": credential_status(db, acc, platform),
            }
        )
    return success_response(data=result)


@router.get("/platform-credential-guide")
def platform_credential_guide(current_user: User = Depends(get_current_user)):
    """凭证申请指引：每个平台去哪申请、要哪些字段、缺什么。

    出参不含任何密钥值，环境变量类凭证只回 configured 布尔。
    """
    from app.services.platform_credential_guide import env_credential_status, guides_payload

    return success_response(
        data={
            "guides": guides_payload(),
            "env_status": env_credential_status(),
            "storage_note": (
                "凭证有三处落点：平台账号（cookie / token_data / configs）、"
                "backend/.env 环境变量、platform_configs 键值表。"
                "读取优先级 configs < cookie < token_data。"
            ),
        }
    )


@router.post("/platform-accounts")
def create_platform_account(
        account: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建平台账号"""
    from app.services.platform_account_service import apply_credentials, resolve_tenant_scope

    platform = db.query(Platform).filter(Platform.id == account["platform_id"]).first()
    if not platform:
        return error_response(404, "平台不存在，请先确认 platform_id（见 /platforms 清单）")

    new_acc = PlatformAccount(
        platform_id=account["platform_id"],
        account_name=account["account_name"],
        username=account.get("username"),
        email=account.get("email"),
        tenant_id=resolve_tenant_scope(db, current_user),
    )
    db.add(new_acc)
    db.flush()  # 先取到 account.id，凭证才能落到 platform_configs
    written = apply_credentials(db, account=new_acc, platform=platform, payload=account)
    db.commit()
    return success_response(
        data={"id": new_acc.id, "credential_fields_written": written},
        message="账号创建成功" if written else "账号创建成功（本次未写入凭证）",
    )


@router.put("/platform-accounts/{account_id}")
def update_platform_account(
    account_id: str,
    account: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /platform-accounts/{account_id} 请求，更新相关资源。
    
    :param account_id: 账户ID
    :param account: 参数 account
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    acc = db.query(PlatformAccount).filter_by(id=account_id).first()
    if not acc:
        return error_response(404, "账号不存在")
    if "platform_id" in account:
        acc.platform_id = account["platform_id"]
    if "account_name" in account or "name" in account:
        acc.account_name = account.get("account_name") or account.get("name")
    if "username" in account:
        acc.username = account["username"]
    if "email" in account:
        acc.email = account["email"]
    if "is_active" in account:
        acc.is_active = bool(account["is_active"])
    if "login_status" in account:
        acc.login_status = str(account["login_status"])

    from app.services.platform_account_service import apply_credentials

    written = 0
    platform = db.query(Platform).filter(Platform.id == acc.platform_id).first()
    if platform is not None:
        written = apply_credentials(db, account=acc, platform=platform, payload=account)
    db.commit()
    return success_response(
        data={"credential_fields_written": written},
        message="账号已更新" if written else "账号已更新（本次未写入凭证）",
    )


@router.post("/platform-session-patrol")
def platform_session_patrol(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PC-04：手动触发平台账号会话巡检（cookie/token 过期判定）。

    dry_run=true 只出报告不改库，供运营先看「会命中谁」；
    正式执行会把命中的 logged_in 账号置为 expired（不会自动恢复，须重绑）。
    报告只含 account_id / 平台名 / 判定原因 / 有没有凭证，绝不回传凭证内容。
    """
    from app.core.config import settings
    from app.services.platform_session_patrol_service import patrol_platform_sessions

    dry_run = bool(payload.get("dry_run", False))
    stale_raw = payload.get("cookie_stale_days")
    stale_days = (
        int(stale_raw) if stale_raw is not None else int(settings.PLATFORM_COOKIE_STALE_DAYS)
    )
    report = patrol_platform_sessions(
        db,
        cookie_stale_days=stale_days,
        dry_run=dry_run,
        limit=int(payload.get("limit") or 500),
    )
    return success_response(
        data=report,
        message=(
            "试跑完成：未改动任何账号状态"
            if dry_run
            else f"巡检完成，已置 expired {report.get('expired_marked', 0)} 个账号"
        ),
    )


@router.post("/generate")
async def generate_content_frontend(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue AI 内容生成（scenario=article）。"""
    from app.services.ai_invocation_service import invoke_llm
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    topic = (body.get("topic") or "").strip()
    if not topic:
        return error_response(400, "请输入主题或关键词")

    style = (body.get("style") or "formal").strip()
    prompt = (
        f"请围绕主题「{topic}」撰写一篇 SEO 友好的建材行业推广文案，"
        f"风格：{style}，800～1200 字，结构清晰，适合多平台发布。"
    )
    try:
        result = await invoke_llm(
            db,
            prompt=prompt,
            scenario="article",
            task_type="seo_matrix:generate",
            max_tokens=2500,
            tenant_id=resolve_tenant_id_for_user(db, current_user),
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))

    content = (result.get("content") or "").strip()
    if not content:
        return error_response(502, "AI 未返回内容")

    new_content = GeneratedContent(
        title=topic,
        content=content,
        word_count=len(content),
        status="draft",
    )
    db.add(new_content)
    db.commit()
    return success_response(
        data={
            "content": content,
            "id": new_content.id,
            "scenario": result.get("scenario", "article"),
            "fallback": result.get("fallback", False),
            "token_usage": int(result.get("token_usage") or 0),
            "model_name": result.get("model_name"),
        },
        message="内容生成完成",
    )


@router.post("/optimize")
async def optimize_content_frontend(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 内容优化（scenario=article）。"""
    from app.services.ai_invocation_service import invoke_optimize
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    content = (body.get("content") or "").strip()
    if not content:
        return error_response(400, "内容为空")

    style = (body.get("style") or "formal").strip()
    try:
        result = await invoke_optimize(
            db,
            content=content,
            optimization_type="seo",
            keywords=[style],
            scenario="article",
            tenant_id=resolve_tenant_id_for_user(db, current_user),
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))

    optimized = (result.get("optimized_content") or content).strip()
    return success_response(
        data={
            "content": optimized,
            "scenario": result.get("scenario", "article"),
            "fallback": result.get("fallback", False),
            "token_usage": int(result.get("token_usage") or 0),
            "model_name": result.get("model_name"),
        },
        message="优化完成",
    )


@router.get("/drafts")
def list_drafts_frontend(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 草稿列表接口（GET /drafts）。"""
    query = db.query(GeneratedContent).filter_by(status="draft")
    total = query.count()
    items = query.order_by(GeneratedContent.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "title": item.title or "",
            "content": item.content or "",
            "type": "content",
            "typeLabel": "文案",
            "time": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
        })
    return success_response(data=result)


@router.post("/drafts")
def save_draft_frontend(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 保存草稿接口（POST /drafts）。"""
    new_content = GeneratedContent(
        title=body.get("title", "未命名草稿"),
        content=body.get("content", ""),
        word_count=len(body.get("content", "")),
        status="draft",
    )
    db.add(new_content)
    db.commit()
    return success_response(
        data={
            "id": new_content.id,
            "title": new_content.title,
            "content": new_content.content,
            "type": "content",
            "typeLabel": "文案",
            "time": new_content.created_at.strftime("%Y-%m-%d %H:%M") if new_content.created_at else "",
        },
        message="草稿已保存",
    )


@router.get("/publish-history")
def list_publish_history_frontend(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """前端 publish.vue 发布历史接口（GET /publish-history）。"""
    from collections import defaultdict
    query = db.query(PublishTask).order_by(PublishTask.created_at.desc())
    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    groups: dict = defaultdict(list)
    for t in tasks:
        groups[t.content_id].append(t)

    # 批量加载内容
    content_ids = list(groups.keys())
    content_map = {
        c.id: c
        for c in db.query(GeneratedContent)
        .filter(GeneratedContent.id.in_(content_ids))
        .all()
    }
    # 批量加载平台
    platform_ids = list({t.platform_id for t in tasks})
    platform_map = {
        p.id: p
        for p in db.query(Platform)
        .filter(Platform.id.in_(platform_ids))
        .all()
    }
    result = []
    for content_id, group in groups.items():
        content = content_map.get(content_id)
        results = []
        for t in group:
            plat = platform_map.get(t.platform_id)
            results.append({
                "platformId": t.platform_id,
                "success": t.status == "success" and bool((t.published_url or "").strip()),
                "message": t.error_message or (t.published_url or ""),
                "platformName": plat.name if plat else "",
            })
        result.append({
            "id": content_id,
            "time": group[0].created_at.strftime("%Y-%m-%d %H:%M") if group[0].created_at else "",
            "content": content.content if content else "",
            "type": "content",
            "results": results,
        })
    return success_response(data=result)


def _publish_from_media_task(db: Session, body: dict, media_task_id):
    """处理 media_render_task_id 形式的视频引流发布，返回响应。"""
    platforms = body.get("platforms") or body.get("platform_ids") or []
    publish_traffic = body.get("publish_traffic", True)
    try:
        if publish_traffic:
            from app.services.media_publish_service import publish_video_traffic_funnel_sync
            payload = publish_video_traffic_funnel_sync(
                db,
                str(media_task_id),
                list(platforms) if platforms else None,
            )
        else:
            from app.services.media_publish_service import publish_task_to_platforms_sync
            if not platforms:
                return error_response(400, "platforms 不能为空")
            payload = publish_task_to_platforms_sync(db, str(media_task_id), list(platforms))
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=payload, message="视频引流发布已处理")


def _publish_frontend_format(db: Session, body: dict, current_user: User):
    """处理前端 publish.vue 格式（content + platforms），返回响应。"""
    content_text = body.get("content", "")
    platforms = body.get("platforms", []) or body.get("platform_ids", [])
    if not content_text or not platforms:
        return error_response(400, "内容或平台列表为空")

    # 创建临时 GeneratedContent
    content_title = body.get("contentType", "发布内容") or "发布内容"
    gc = GeneratedContent(
        title=content_title,
        content=content_text,
        word_count=len(content_text),
        status="draft",
    )
    db.add(gc)
    db.flush()
    content_id = gc.id
    from app.services.publish_dispatch_service import SeoPublishService
    from app.services.tenant_scenario_service import resolve_tenant_id_for_user
    tenant_scope = resolve_tenant_id_for_user(db, current_user)
    svc = SeoPublishService(db)
    results = []
    # 批量预加载平台与账号，避免循环内逐条查询
    platform_map = {}
    account_map = {}
    if platforms:
        platform_map = {
            p.id: p
            for p in db.query(Platform)
            .filter(Platform.id.in_(platforms))
            .all()
        }
        account_q = db.query(PlatformAccount).filter(
            PlatformAccount.platform_id.in_(platforms),
            PlatformAccount.is_active.is_(True),
        )
        if tenant_scope:
            account_q = account_q.filter(PlatformAccount.tenant_id == tenant_scope)
        for acc in account_q.all():
            account_map.setdefault(acc.platform_id, acc)
    for platform_id in platforms:
        account = account_map.get(platform_id)
        if not account:
            results.append({
                "platformId": platform_id,
                "success": False,
                "message": "未找到已连接的账号",
            })
            continue

        try:
            platform = platform_map.get(platform_id)
            published_url = svc._dispatch_to_platform(platform, account, gc)
            if not (published_url or "").strip():
                results.append({
                    "platformId": platform_id,
                    "success": False,
                    "message": "发布未返回作品链接，视为失败",
                })
            else:
                results.append({
                    "platformId": platform_id,
                    "success": True,
                    "verified": True,
                    "platform_post_url": published_url,
                    "message": published_url,
                })
        except Exception as e:
            logger.warning(f"发布失败 platform={platform_id}: {e}")
            results.append({
                "platformId": platform_id,
                "success": False,
                "message": str(e),
            })

    db.commit()
    return success_response(
        data={"results": results, "content_id": content_id},
        message=f"完成 {len(results)} 个平台的分发",
    )


def _publish_task_create_format(db: Session, body: dict):
    """处理 PublishTaskCreate 格式（content_ids + platform_ids + account_ids），返回响应。"""
    platform_ids = list(body.get("platform_ids", []))
    if body.get("platform_id"):
        platform_ids.append(body["platform_id"])
    account_ids = list(body.get("account_ids", []))
    if body.get("account_id"):
        account_ids.append(body["account_id"])
    platform_ids = [p for p in platform_ids if p]
    account_ids = [a for a in account_ids if a]
    if not platform_ids or not account_ids:
        return error_response(400, "请选择平台与账号")

    content_ids = body.get("content_ids", [])
    if not content_ids:
        return error_response(400, "请选择内容")

    sched = None
    scheduled_time = body.get("scheduled_time")
    if scheduled_time:
        try:
            sched = datetime.fromisoformat(
                scheduled_time.replace("Z", "+00:00"))
        except (ValueError, TypeError, Exception):
            sched = None

    publish_type = body.get("publish_type", "immediate")
    task_count = 0
    for content_id in content_ids:
        for pid in platform_ids:
            for aid in account_ids:
                db.add(
                    PublishTask(
                        content_id=content_id,
                        platform_id=pid,
                        account_id=aid,
                        publish_type=publish_type,
                        scheduled_time=sched,
                    )
                )
                task_count += 1

    db.commit()
    return success_response(
        data={"task_count": task_count},
        message=f"成功创建 {task_count} 个发布任务",
    )


@router.post("/publish")
def create_publish_task(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建发布任务（兼容 PublishTaskCreate 和前端 publish.vue 两种格式）。

    格式1 (PublishTaskCreate): { content_ids, platform_ids, account_ids }
    格式2 (前端一键群发):     { content, contentType, platforms: [...] }
    """
    media_task_id = body.get("media_render_task_id") or body.get("media_task_id")
    if media_task_id:
        return _publish_from_media_task(db, body, media_task_id)

    # 检测格式: 如果有 content 字段则为前端格式，否则为 PublishTaskCreate 格式
    if "content" in body or "platforms" in body:
        return _publish_frontend_format(db, body, current_user)

    return _publish_task_create_format(db, body)


@router.get("/publish-tasks")
def list_publish_tasks(
    status: Optional[str] = None,
    platform_id: Optional[str] = None,
    account_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取发布任务列表"""
    query = db.query(PublishTask)
    if status:
        query = query.filter_by(status=status)
    if platform_id:
        query = query.filter_by(platform_id=platform_id)
    if account_id:
        query = query.filter_by(account_id=account_id)

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    # 批量加载
    content_ids = list({t.content_id for t in tasks})
    platform_ids = list({t.platform_id for t in tasks})
    content_map = {
        c.id: c
        for c in db.query(GeneratedContent)
        .filter(GeneratedContent.id.in_(content_ids))
        .all()
    }
    platform_map = {
        p.id: p
        for p in db.query(Platform)
        .filter(Platform.id.in_(platform_ids))
        .all()
    }
    result = []
    for task in tasks:
        gc = content_map.get(task.content_id)
        plat = platform_map.get(task.platform_id)
        result.append(
            {
                "id": task.id,
                "content_id": task.content_id,
                "platform_id": task.platform_id,
                "account_id": task.account_id,
                "status": task.status,
                "publish_type": task.publish_type,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "published_url": task.published_url,
                "created_at": task.created_at,
                "published_at": task.published_at,
                "title": gc.title if gc else "",
                "platform": plat.name if plat else "",
                "message": task.error_message or "",
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/publish-tasks/{task_id}/retry")
def retry_publish_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /publish-tasks/{task_id}/retry 请求，retry相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    t = db.query(PublishTask).filter_by(id=task_id).first()
    if not t:
        return error_response(404, "任务不存在")
    t.status = "pending"
    t.retry_count = (t.retry_count or 0) + 1
    db.commit()
    return success_response(message="已重新排队")


@router.delete("/publish-tasks/{task_id}")
def delete_publish_task_route(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 DELETE /publish-tasks/{task_id} 请求，删除相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    t = db.query(PublishTask).filter_by(id=task_id).first()
    if not t:
        return error_response(404, "任务不存在")
    db.delete(t)
    db.commit()
    return success_response(message="已删除")


# ==================== 模块6：发布记录、数据看板与收录监控 ====================


def _build_dashboard_platform_stats(db: Session):
    """构建各平台发布任务统计。"""
    platform_stats = []
    platforms = db.query(Platform).filter_by(is_active=True).all()
    platform_ids = [p.id for p in platforms]
    total_map = {}
    success_map = {}
    if platform_ids:
        total_map = dict(
            db.query(PublishTask.platform_id, func.count(PublishTask.id))
            .filter(PublishTask.platform_id.in_(platform_ids))
            .group_by(PublishTask.platform_id)
            .all()
        )
        success_map = dict(
            db.query(PublishTask.platform_id, func.count(PublishTask.id))
            .filter(
                PublishTask.platform_id.in_(platform_ids),
                PublishTask.status == "success",
            )
            .group_by(PublishTask.platform_id)
            .all()
        )
    for platform in platforms:
        platform_tasks = total_map.get(platform.id, 0) or 0
        platform_success = success_map.get(platform.id, 0) or 0
        platform_stats.append(
            {
                "platform_id": platform.id,
                "platform_name": platform.name,
                "name": platform.name,
                "total_tasks": platform_tasks,
                "success_tasks": platform_success,
                "published_count": platform_success,
                "success_rate": round(
                    (platform_success / platform_tasks) * 100,
                    2) if platform_tasks > 0 else 0,
            })
    return platform_stats


def _build_dashboard_recent_tasks(db: Session):
    """构建最近发布任务列表（含内容/平台名称）。"""
    recent_tasks = []
    recent_publish_tasks = db.query(PublishTask).order_by(
            PublishTask.created_at.desc()).limit(10).all()
    # 批量加载
    recent_content_ids = [t.content_id for t in recent_publish_tasks]
    recent_platform_ids = [t.platform_id for t in recent_publish_tasks]
    recent_content_map = {
        c.id: c
        for c in db.query(GeneratedContent)
        .filter(GeneratedContent.id.in_(recent_content_ids))
        .all()
    }
    recent_platform_map = {
        p.id: p
        for p in db.query(Platform)
        .filter(Platform.id.in_(recent_platform_ids))
        .all()
    }
    for t in recent_publish_tasks:
        gc = recent_content_map.get(t.content_id)
        plat = recent_platform_map.get(t.platform_id)
        recent_tasks.append(
            {
                "keyword": (gc.title if gc else "") or "",
                "platform": plat.name if plat else "",
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
        )
    return recent_tasks


def _build_dashboard_hot_keywords(db: Session):
    """构建热门关键词列表。"""
    hot_keywords = []
    for gk in (
        db.query(GeneratedKeyword)
        .filter_by(is_valid=True)
        .order_by(GeneratedKeyword.search_volume.desc())
        .limit(8)
        .all()
    ):
        hot_keywords.append(
            {
                "keyword": gk.keyword,
                "rank": 0,
                "search_volume": gk.search_volume or 0,
                "status": "tracking",
            }
        )
    return hot_keywords


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    """获取数据看板"""
    total_keywords = db.query(
        GeneratedKeyword).filter_by(is_valid=True).count()
    used_keywords = db.query(GeneratedKeyword).filter_by(is_used=True).count()
    total_contents = db.query(GeneratedContent).count()
    published_contents = db.query(GeneratedContent).filter_by(
        status="published").count()

    total_tasks = db.query(PublishTask).count()
    success_tasks = db.query(PublishTask).filter_by(status="success").count()
    failed_tasks = db.query(PublishTask).filter_by(status="failed").count()
    included_count = db.query(InclusionStatus).filter_by(
        is_included=True).count()
    total_inclusion = db.query(InclusionStatus).count()
    platform_stats = _build_dashboard_platform_stats(db)
    recent_tasks = _build_dashboard_recent_tasks(db)
    hot_keywords = _build_dashboard_hot_keywords(db)
    return success_response(
        data={
            "keyword_stats": {
                "total": total_keywords,
                "used": used_keywords,
                "unused": total_keywords - used_keywords,
            },
            "content_stats": {
                "total": total_contents,
                "published": published_contents,
                "draft": total_contents - published_contents,
            },
            "publish_stats": {
                "total": total_tasks,
                "success": success_tasks,
                "failed": failed_tasks,
                "success_rate": round(
                    (success_tasks / total_tasks) * 100,
                    2) if total_tasks > 0 else 0,
            },
            "inclusion_stats": {
                "total": total_inclusion,
                "included": included_count,
                "inclusion_rate": round(
                    (included_count / total_inclusion) * 100,
                    2) if total_inclusion > 0 else 0,
            },
            "platform_stats": platform_stats,
            "recent_tasks": recent_tasks,
            "hot_keywords": hot_keywords,
        })


@router.get("/inclusion-status")
def list_inclusion_status(
        task_id: Optional[str] = None,
        is_included: Optional[bool] = None,
        status: Optional[str] = Query(
            None,
            description="兼容前端：included / not_included"),
    keyword: Optional[str] = Query(None),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """获取收录状态列表"""
    query = db.query(InclusionStatus)
    if task_id:
        query = query.filter_by(task_id=task_id)
    if status == "included":
        query = query.filter_by(is_included=True)
    elif status == "not_included":
        query = query.filter_by(is_included=False)
    elif is_included is not None:
        query = query.filter_by(is_included=is_included)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(InclusionStatus.keyword.like(
            like), InclusionStatus.url.like(like)))

    total = query.count()
    status_list = query.offset((page - 1) * page_size).limit(page_size).all()
    # 一次性加载 probe_mode 缓存映射，避免循环内逐条查询
    from app.services.seo.inclusion_probe_cache import _load_map
    probe_mode_map = _load_map(db) if status_list else {}
    result = []
    for status in status_list:
        result.append(
            {
                "id": status.id,
                "task_id": status.task_id,
                "url": status.url,
                "keyword": status.keyword,
                "is_included": status.is_included,
                "ranking": status.ranking,
                "search_engine": status.search_engine,
                "probe_mode": probe_mode_map.get(str(status.task_id)),
                "last_checked_at": status.last_checked_at,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size})


@router.post("/check-inclusion")
def check_inclusion(
    task_ids: Optional[List[str]] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查收录状态（task_ids 为空则检查最近已发布 URL）。"""
    from app.services.seo.inclusion_check_service import recheck_inclusion_batch
    report = recheck_inclusion_batch(db, task_ids=list(task_ids or []))
    return success_response(
        data=report,
        message=f"成功检查 {report.get('updated_count', 0)} 条收录状态",
    )


@router.get("/inclusion-probe-config")
def get_inclusion_probe_config(
    current_user: User = Depends(get_current_user),
):
    """收录探测 honest 状态（P0-4）。"""
    from app.services.seo.inclusion_check_service import inclusion_probe_status
    return success_response(data=inclusion_probe_status())


@router.post("/seed-industry-keywords")
def seed_industry_keywords(
    body: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入产业带 SEO 词库（默认大城保温建材 P0-4）。"""
    from app.services.dacheng_keyword_seed_service import seed_industry_belt_keywords
    belt_id = str(body.get("belt_id") or "all")
    include_ranking = bool(body.get("include_ranking", True))
    data = seed_industry_belt_keywords(
        db,
        belt_id=belt_id,
        include_ranking=include_ranking,
    )
    return success_response(data=data, message=data.get("message") or "词库入库完成")


@router.post("/inclusion-status/{row_id}/recheck")
def recheck_single_inclusion(
    row_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /inclusion-status/{row_id}/recheck 请求，recheck相关资源。
    
    :param row_id: 参数 row_id
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    row = db.query(InclusionStatus).filter_by(id=row_id).first()
    if not row:
        return error_response(404, "记录不存在")
    return check_inclusion([str(row.task_id)], db, current_user)


@router.put("/inclusion-settings")
def save_inclusion_settings(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 PUT /inclusion-settings 请求，保存相关资源。
    
    :param payload: 请求体数据
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    key = "inclusion_ui_settings"
    raw = json.dumps(payload, ensure_ascii=False)
    s = db.query(SystemSetting).filter_by(setting_key=key).first()
    if s:
        s.setting_value = raw
        s.setting_type = "json"
    else:
        db.add(
            SystemSetting(
                setting_key=key,
                setting_value=raw,
                setting_type="json"))
    db.commit()
    return success_response(message="设置已保存")


@router.get("/publish-logs")
def list_publish_logs(
    task_id: Optional[str] = None,
    level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """获取发布日志（管理操作）"""
    query = db.query(PublishLog)
    if task_id:
        query = query.filter_by(task_id=task_id)
    if level:
        query = query.filter_by(level=level)

    query = query.order_by(PublishLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for log in logs:
        result.append(
            {
                "id": log.id,
                "task_id": log.task_id,
                "level": log.level,
                "message": log.message,
                "created_at": log.created_at,
            }
        )

    return success_response(
        data={
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size})
