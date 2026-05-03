import json
import re
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.security import get_current_user, optional_auth
from app.services.seo_analyzer import SeoAnalyzer
from app.services.site_audit import SiteAuditEngine
from app.models.seo import SiteAudit
from app.models.user import User
from datetime import datetime, timezone


router = APIRouter()


PRIVATE_NETWORKS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("::1/128"),
    ip_network("fc00::/7"),
]

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "metadata.google.internal"}


def validate_audit_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="仅支持 http/https 协议的URL")
    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="不允许审计内部地址")
    try:
        ip = ip_address(hostname)
        for net in PRIVATE_NETWORKS:
            if ip in net:
                raise HTTPException(status_code=400, detail="不允许审计内网地址")
    except ValueError:
        if re.search(r'(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.)', hostname):
            raise HTTPException(status_code=400, detail="不允许审计内网地址")
    return url


class AuditRunRequest(BaseModel):
    url: str = Field(..., description="要审计的页面URL")
    audit_type: str = Field(default="full", pattern="^(quick|full)$")


@router.get("/dashboard")
def get_seo_dashboard(db: Session = Depends(get_db)):
    """获取SEO仪表盘数据 - 带5分钟缓存"""
    from app.services.cache_service import cache_service
    
    cache_key = "seo:dashboard:summary"
    cached_data = cache_service.get_json(cache_key)
    
    if cached_data:
        return cached_data
    
    analyzer = SeoAnalyzer(db)
    result = analyzer.get_dashboard()
    
    # 缓存5分钟
    cache_service.set_json(cache_key, result, expire=300)
    
    return result


@router.get("/keyword-ranking/{keyword_id}")
def get_keyword_ranking(keyword_id: str, db: Session = Depends(get_db)):
    analyzer = SeoAnalyzer(db)
    return analyzer.analyze_keyword_rankings(keyword_id)


@router.get("/keyword-groups")
def get_keyword_groups(db: Session = Depends(get_db)):
    analyzer = SeoAnalyzer(db)
    return analyzer.get_keyword_groups()


@router.get("/seo-pages-summary")
def get_seo_pages_summary(db: Session = Depends(get_db)):
    analyzer = SeoAnalyzer(db)
    return analyzer.get_seo_pages_summary()


@router.post("/run-audit")
async def run_audit(req: AuditRunRequest, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    validate_audit_url(req.url)
    engine = SiteAuditEngine()
    result = await engine.run_audit(url=req.url, audit_type=req.audit_type)

    now = datetime.now(timezone.utc)
    report_data = json.dumps({
        "url": req.url,
        "issues": result.get("issues", []),
        "recommendations": result.get("recommendations", []),
    }, ensure_ascii=False, default=str)

    audit_record = SiteAudit(
        status="completed",
        audit_type=req.audit_type,
        score=result.get("score", 0),
        total_issues=result.get("total_issues", 0),
        critical_issues=result.get("critical_issues", 0),
        warning_issues=result.get("warning_issues", 0),
        report_data=report_data,
        completed_at=now,
    )
    db.add(audit_record)
    db.commit()
    db.refresh(audit_record)

    return {
        "id": str(audit_record.id),
        "url": req.url,
        "status": "completed",
        "score": result.get("score", 0),
        "total_issues": result.get("total_issues", 0),
        "critical_issues": result.get("critical_issues", 0),
        "warning_issues": result.get("warning_issues", 0),
        "dimension_scores": result.get("dimension_scores", {}),
        "issues": result.get("issues", []),
        "recommendations": result.get("recommendations", []),
    }
