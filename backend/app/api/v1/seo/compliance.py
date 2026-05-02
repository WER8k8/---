"""合规检查API路由 - 广告法检测"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.security import require_admin
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
from app.models.compliance import ComplianceRule, ComplianceScanResult, ComplianceViolation, AdvertisementLawKeyword
from app.services.compliance_scanner import compliance_scanner, init_default_keywords

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/scan", summary="扫描文本合规性")
def scan_content(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """扫描文本内容中的广告法违规内容"""
    text = data.get("text", "")
    title = data.get("title", "")
    
    if not text and not title:
        raise HTTPException(status_code=400, detail="请提供要扫描的文本或标题")
    
    result = compliance_scanner.validate_content(title, text)
    
    # 保存扫描结果
    scan_result = ComplianceScanResult(
        id=str(uuid4()),
        content_id=data.get("content_id", str(uuid4())),
        content_type=data.get("content_type", "article"),
        content_title=title[:255] if title else None,
        content_text=text[:5000] if text else None,
        scan_status="completed",
        total_issues=result["total_issues"],
        high_severity_count=result["high_severity_count"],
        medium_severity_count=result["medium_severity_count"],
        low_severity_count=result["low_severity_count"],
        scan_details=result["violations"],
        suggestions=result["suggestions"],
        scanned_at=datetime.utcnow()
    )
    db.add(scan_result)
    db.commit()
    
    # 保存违规记录
    for violation in result["violations"]:
        violation_record = ComplianceViolation(
            id=str(uuid4()),
            scan_result_id=scan_result.id,
            rule_id="ad_law_keyword",
            rule_name=violation["category"],
            rule_type="ad_law",
            severity=violation["severity"],
            matched_text=violation["matched_text"],
            context=violation["context"],
            suggestion=violation.get("alternative", "")
        )
        db.add(violation_record)
    
    db.commit()
    
    return {"success": True, "scan_id": scan_result.id, **result}


@router.post("/scan-batch", summary="批量扫描内容")
def batch_scan(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """批量扫描多个内容的合规性"""
    items = data.get("items", [])
    
    if not items or len(items) > 50:
        raise HTTPException(status_code=400, detail="批量扫描最多支持50个内容")
    
    results = []
    for item in items:
        title = item.get("title", "")
        text = item.get("text", "")
        content_id = item.get("content_id", str(uuid4()))
        content_type = item.get("content_type", "article")
        
        result = compliance_scanner.validate_content(title, text)
        result["content_id"] = content_id
        result["content_type"] = content_type
        results.append(result)
    
    return {"success": True, "results": results, "total_items": len(results)}


@router.get("/scan-result/{scan_id}", summary="获取扫描结果")
def get_scan_result(
    scan_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取指定扫描结果的详细信息"""
    scan_result = db.query(ComplianceScanResult).filter(ComplianceScanResult.id == scan_id).first()
    
    if not scan_result:
        raise HTTPException(status_code=404, detail="扫描结果不存在")
    
    return {
        "success": True,
        "data": {
            "id": scan_result.id,
            "content_id": scan_result.content_id,
            "content_type": scan_result.content_type,
            "content_title": scan_result.content_title,
            "scan_status": scan_result.scan_status,
            "total_issues": scan_result.total_issues,
            "high_severity_count": scan_result.high_severity_count,
            "medium_severity_count": scan_result.medium_severity_count,
            "low_severity_count": scan_result.low_severity_count,
            "scan_details": scan_result.scan_details,
            "suggestions": scan_result.suggestions,
            "scanned_at": scan_result.scanned_at.isoformat() if scan_result.scanned_at else None,
            "created_at": scan_result.created_at.isoformat() if scan_result.created_at else None
        }
    }


@router.get("/scan-history", summary="获取扫描历史")
def get_scan_history(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    limit: int = 20,
    offset: int = 0
):
    """获取扫描历史记录"""
    results = db.query(ComplianceScanResult)\
        .order_by(ComplianceScanResult.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "content_id": r.content_id,
                "content_type": r.content_type,
                "content_title": r.content_title,
                "scan_status": r.scan_status,
                "total_issues": r.total_issues,
                "high_severity_count": r.high_severity_count,
                "medium_severity_count": r.medium_severity_count,
                "low_severity_count": r.low_severity_count,
                "scanned_at": r.scanned_at.isoformat() if r.scanned_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ],
        "total": db.query(ComplianceScanResult).count()
    }


@router.get("/keywords", summary="获取违禁词列表")
def get_keywords(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    category: str = None,
    severity: str = None
):
    """获取广告法违禁词列表"""
    query = db.query(AdvertisementLawKeyword).filter(AdvertisementLawKeyword.is_active == True)
    
    if category:
        query = query.filter(AdvertisementLawKeyword.category == category)
    
    if severity:
        query = query.filter(AdvertisementLawKeyword.severity == severity)
    
    keywords = query.all()
    
    return {
        "success": True,
        "data": [
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "category": kw.category,
                "severity": kw.severity,
                "description": kw.description,
                "alternative": kw.alternative
            }
            for kw in keywords
        ]
    }


@router.get("/keywords/categories", summary="获取违禁词分类")
def get_keyword_categories(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """获取违禁词分类列表"""
    categories = db.query(AdvertisementLawKeyword.category).distinct().all()
    
    return {
        "success": True,
        "data": [cat[0] for cat in categories]
    }


@router.post("/keywords", summary="添加违禁词", dependencies=[Depends(require_admin)])
def add_keyword(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """添加新的广告法违禁词"""
    keyword = data.get("keyword")
    category = data.get("category")
    severity = data.get("severity", "medium")
    
    if not keyword or not category:
        raise HTTPException(status_code=400, detail="请提供关键词和分类")
    
    # 检查是否已存在
    existing = db.query(AdvertisementLawKeyword).filter(AdvertisementLawKeyword.keyword == keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="该关键词已存在")
    
    new_keyword = AdvertisementLawKeyword(
        id=str(uuid4()),
        keyword=keyword,
        category=category,
        severity=severity,
        description=data.get("description"),
        alternative=data.get("alternative")
    )
    
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    
    # 刷新缓存
    compliance_scanner.refresh_keywords()
    
    return {
        "success": True,
        "message": "添加成功",
        "data": {
            "id": new_keyword.id,
            "keyword": new_keyword.keyword,
            "category": new_keyword.category,
            "severity": new_keyword.severity
        }
    }


@router.put("/keywords/{keyword_id}", summary="更新违禁词", dependencies=[Depends(require_admin)])
def update_keyword(
    keyword_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """更新违禁词信息"""
    keyword = db.query(AdvertisementLawKeyword).filter(AdvertisementLawKeyword.id == keyword_id).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    if "keyword" in data:
        keyword.keyword = data["keyword"]
    if "category" in data:
        keyword.category = data["category"]
    if "severity" in data:
        keyword.severity = data["severity"]
    if "description" in data:
        keyword.description = data["description"]
    if "alternative" in data:
        keyword.alternative = data["alternative"]
    
    db.commit()
    db.refresh(keyword)
    
    # 刷新缓存
    compliance_scanner.refresh_keywords()
    
    return {"success": True, "message": "更新成功"}


@router.delete("/keywords/{keyword_id}", summary="删除违禁词", dependencies=[Depends(require_admin)])
def delete_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """删除违禁词"""
    keyword = db.query(AdvertisementLawKeyword).filter(AdvertisementLawKeyword.id == keyword_id).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    db.delete(keyword)
    db.commit()
    
    # 刷新缓存
    compliance_scanner.refresh_keywords()
    
    return {"success": True, "message": "删除成功"}


@router.post("/refresh-cache", summary="刷新违禁词缓存", dependencies=[Depends(require_admin)])
def refresh_cache(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """刷新违禁词缓存"""
    compliance_scanner.refresh_keywords()
    
    return {"success": True, "message": "缓存已刷新"}


@router.post("/init-defaults", summary="初始化默认违禁词", dependencies=[Depends(require_admin)])
def init_default_keywords_api(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """初始化默认广告法违禁词数据"""
    init_default_keywords(db)
    compliance_scanner.refresh_keywords()
    
    return {"success": True, "message": "默认违禁词已初始化"}
