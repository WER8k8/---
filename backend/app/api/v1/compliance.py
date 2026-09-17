# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.compliance import (AdvertisementLawKeyword, ComplianceRule,
                                   ComplianceScanResult, ComplianceViolation)
from app.schemas.compliance import (AdvertisementLawKeywordCreate,
                                    AdvertisementLawKeywordResponse,
                                    AdvertisementLawKeywordUpdate,
                                    BatchDeleteRequest, ComplianceRuleCreate,
                                    ComplianceRuleResponse,
                                    ComplianceRuleUpdate,
                                    ComplianceScanResultCreate,
                                    ComplianceScanResultResponse)

router = APIRouter()


@router.get("/rules")
def list_rules(
        rule_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """list_rules。

    参数说明：
    :param rule_type: 参数 rule_type
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(ComplianceRule).filter(ComplianceRule.is_active)
    if rule_type:
        q = q.filter(ComplianceRule.rule_type == rule_type)

    total = q.count()
    items = q.order_by(
        ComplianceRule.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size})


@router.get("/rules/{rule_id}", response_model=ComplianceRuleResponse)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    """get_rule。

    参数说明：
    :param rule_id: 参数 rule_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.id == rule_id,
        ComplianceRule.is_active).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.post("/rules", response_model=ComplianceRuleResponse)
def create_rule(
        req: ComplianceRuleCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_rule。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    keywords_json = json.dumps(req.keywords)
    rule = ComplianceRule(id=str(uuid.uuid4()),
                          keywords=keywords_json,
                          **{k: v for k,
                              v in req.model_dump().items() if k != "keywords"})
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=ComplianceRuleResponse)
def update_rule(
        rule_id: str,
        req: ComplianceRuleUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_rule。

    参数说明：
    :param rule_id: 参数 rule_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    update_data = req.model_dump(exclude_unset=True)
    if "keywords" in update_data:
        update_data["keywords"] = json.dumps(update_data["keywords"])

    for k, v in update_data.items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(
        rule_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_rule。

    参数说明：
    :param rule_id: 参数 rule_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule.is_active = False
    db.commit()
    return success_response(message="规则已禁用")


@router.post("/scan", response_model=ComplianceScanResultResponse)
def scan_content(
        req: ComplianceScanResultCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """scan_content。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    scan_result = ComplianceScanResult(
        id=str(uuid.uuid4()),
        scan_status="completed",
        total_issues=0,
        high_severity_count=0,
        medium_severity_count=0,
        low_severity_count=0,
        **req.model_dump(),
    )
    rules = db.query(ComplianceRule).filter(ComplianceRule.is_active).all()
    violations = []
    suggestions = []
    for rule in rules:
        keywords = json.loads(
            rule.keywords) if isinstance(
            rule.keywords,
            str) else rule.keywords
        for keyword in keywords:
            if keyword in req.content_text:
                violations.append({"rule_id": rule.id,
                                   "rule_name": rule.rule_name,
                                   "rule_type": rule.rule_type,
                                   "severity": rule.severity,
                                   "matched_text": keyword,
                                   "context": req.content_text[max(0,
                                                                   req.content_text.find(keyword) - 50): req.content_text.find(keyword) + 50],
                                   })
                if rule.severity == "high":
                    scan_result.high_severity_count += 1
                elif rule.severity == "medium":
                    scan_result.medium_severity_count += 1
                else:
                    scan_result.low_severity_count += 1

    scan_result.total_issues = len(violations)
    scan_result.scan_details = violations
    scan_result.scanned_at = datetime.now(timezone.utc)
    db.add(scan_result)
    db.commit()
    for violation in violations:
        ad_keyword = (
            db.query(AdvertisementLawKeyword) .filter(
                AdvertisementLawKeyword.keyword == violation["matched_text"],
                AdvertisementLawKeyword.is_active) .first())
        suggestion = ad_keyword.alternative if ad_keyword else f"建议替换'{violation['matched_text']}'"
        violation_rec = ComplianceViolation(
            id=str(
                uuid.uuid4()),
            scan_result_id=scan_result.id,
            suggestion=suggestion,
            **violation)
        db.add(violation_rec)

    db.commit()
    db.refresh(scan_result)
    return scan_result


@router.get("/scan-results")
def list_scan_results(
        content_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """list_scan_results。

    参数说明：
    :param content_type: 参数 content_type
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(ComplianceScanResult)
    if content_type:
        q = q.filter(ComplianceScanResult.content_type == content_type)

    total = q.count()
    items = q.order_by(
        ComplianceScanResult.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size})

@router.get("/scan-results/{result_id}",
            response_model=ComplianceScanResultResponse)
def get_scan_result(result_id: str, db: Session = Depends(get_db)):
    """get_scan_result。

    参数说明：
    :param result_id: 参数 result_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    result = db.query(ComplianceScanResult).filter(
        ComplianceScanResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="扫描结果不存在")
    return result


@router.get("/violations")
def list_violations(
    scan_result_id: Optional[str] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """list_violations。

    参数说明：
    :param scan_result_id: 参数 scan_result_id
    :param severity: 参数 severity
    :param is_resolved: 参数 is_resolved
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(ComplianceViolation)
    if scan_result_id:
        q = q.filter(ComplianceViolation.scan_result_id == scan_result_id)
    if severity:
        q = q.filter(ComplianceViolation.severity == severity)
    if is_resolved is not None:
        q = q.filter(ComplianceViolation.is_resolved == is_resolved)

    total = q.count()
    items = q.order_by(
        ComplianceViolation.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size})


@router.put("/violations/{violation_id}/resolve")
def resolve_violation(
        violation_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """resolve_violation。

    参数说明：
    :param violation_id: 参数 violation_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    violation = db.query(ComplianceViolation).filter(
        ComplianceViolation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="违规记录不存在")

    violation.is_resolved = True
    violation.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(message="已标记为已解决")


@router.get("/ad-keywords")
def list_ad_keywords(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """list_ad_keywords。

    参数说明：
    :param category: 参数 category
    :param severity: 参数 severity
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(AdvertisementLawKeyword).filter(
        AdvertisementLawKeyword.is_active)

    if category:
        q = q.filter(AdvertisementLawKeyword.category == category)
    if severity:
        q = q.filter(AdvertisementLawKeyword.severity == severity)

    total = q.count()
    items = q.order_by(
        AdvertisementLawKeyword.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size})


@router.get("/ad-keywords/{keyword_id}",
            response_model=AdvertisementLawKeywordResponse)
def get_ad_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """get_ad_keyword。

    参数说明：
    :param keyword_id: 参数 keyword_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    keyword = (
        db.query(AdvertisementLawKeyword) .filter(
            AdvertisementLawKeyword.id == keyword_id,
            AdvertisementLawKeyword.is_active) .first())
    if not keyword:
        raise HTTPException(status_code=404, detail="广告法关键词不存在")
    return keyword


@router.post("/ad-keywords", response_model=AdvertisementLawKeywordResponse)
def create_ad_keyword(
        req: AdvertisementLawKeywordCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_ad_keyword。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    existing = db.query(AdvertisementLawKeyword).filter(
        AdvertisementLawKeyword.keyword == req.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="关键词已存在")

    keyword = AdvertisementLawKeyword(id=str(uuid.uuid4()), **req.model_dump())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.put("/ad-keywords/{keyword_id}",
            response_model=AdvertisementLawKeywordResponse)
def update_ad_keyword(
        keyword_id: str,
        req: AdvertisementLawKeywordUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_ad_keyword。

    参数说明：
    :param keyword_id: 参数 keyword_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    keyword = db.query(AdvertisementLawKeyword).filter(
        AdvertisementLawKeyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="广告法关键词不存在")

    if req.keyword and req.keyword != keyword.keyword:
        existing = (
            db.query(AdvertisementLawKeyword) .filter(
                AdvertisementLawKeyword.keyword == req.keyword,
                AdvertisementLawKeyword.id != keyword_id) .first())
        if existing:
            raise HTTPException(status_code=400, detail="关键词已存在")

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(keyword, k, v)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/ad-keywords/{keyword_id}")
def delete_ad_keyword(
        keyword_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_ad_keyword。

    参数说明：
    :param keyword_id: 参数 keyword_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    keyword = db.query(AdvertisementLawKeyword).filter(
        AdvertisementLawKeyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="广告法关键词不存在")

    keyword.is_active = False
    db.commit()
    return success_response(message="关键词已禁用")


@router.post("/ad-keywords/batch-delete")
def batch_delete_ad_keywords(
        req: BatchDeleteRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_delete_ad_keywords。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not req.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的关键词")

    updated = (
        db.query(AdvertisementLawKeyword)
        .filter(AdvertisementLawKeyword.id.in_(req.ids))
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()
    return success_response(data={"message": f"成功禁用 {updated} 个关键词", "updated_count": updated})
