"""获客引擎领域 API 路由 — FIX-31

统一管理所有获客相关端点：
- 线索搜索、验证、抓取、发送
- 线索管理 CRUD
- 邮件外展任务管理
- 异步搜索进度查询
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.security import get_current_user
from app.core.response import success_response, error_response
from app.core.cache import async_cache_decorator

router = APIRouter(prefix="/lead", tags=["获客引擎"])


# ============================================================
# 线索搜索
# ============================================================

@router.post("/search")
async def search_leads(
    keyword: str,
    source: str = Query("web", description="数据源: web, linkedin, custom"),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """搜索潜在客户线索。

    异步执行搜索任务，返回 task_id 用于轮询进度。
    """
    try:
        from app.services.ubrain.lead_search_task import LeadSearchTask
        task = LeadSearchTask(
            keyword=keyword,
            source=source,
            limit=limit,
            user_id=current_user.id,
        )
        task_id = await task.start()
        return success_response(data={
            "task_id": task_id,
            "status": "pending",
            "message": f"搜索任务已启动: {keyword}",
        })
    except Exception as e:
        return error_response(message=f"搜索启动失败: {str(e)}", code=500)


@router.get("/search/{task_id}/progress")
async def get_search_progress(
    task_id: str,
    current_user=Depends(get_current_user),
):
    """查询异步搜索进度。"""
    try:
        from app.services.ubrain.lead_search_task import LeadSearchTask
        progress = await LeadSearchTask.get_progress(task_id)
        return success_response(data=progress)
    except Exception as e:
        return error_response(message=f"查询进度失败: {str(e)}", code=500)


# ============================================================
# 邮箱验证
# ============================================================

@router.post("/verify-email")
async def verify_email(
    email: str,
    current_user=Depends(get_current_user),
):
    """零成本邮箱验证（MX记录 + SMTP RCPT TO检查）。"""
    try:
        from app.services.ubrain.email_verification_service import (
            EmailVerificationService,
        )
        service = EmailVerificationService()
        result = await service.verify(email)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"邮箱验证失败: {str(e)}", code=500)


@router.post("/verify-emails/batch")
async def verify_emails_batch(
    emails: list[str],
    current_user=Depends(get_current_user),
):
    """批量邮箱验证。"""
    try:
        from app.services.ubrain.email_verification_service import (
            EmailVerificationService,
        )
        service = EmailVerificationService()
        results = []
        for email in emails[:50]:  # 限制批量50个
            result = await service.verify(email)
            results.append(result)
        return success_response(data={
            "total": len(emails),
            "verified": len(results),
            "results": results,
        })
    except Exception as e:
        return error_response(message=f"批量验证失败: {str(e)}", code=500)


# ============================================================
# 网站邮箱抓取
# ============================================================

@router.post("/scrape-emails")
async def scrape_website_emails(
    url: str,
    max_depth: int = Query(2, ge=1, le=5),
    current_user=Depends(get_current_user),
):
    """从目标网站抓取邮箱地址（Contact/About页面）。"""
    try:
        from app.services.ubrain.website_email_scraper import WebsiteEmailScraper
        scraper = WebsiteEmailScraper()
        results = await scraper.scrape(url, max_depth=max_depth)
        return success_response(data={
            "url": url,
            "emails_found": len(results),
            "results": results,
        })
    except Exception as e:
        return error_response(message=f"邮箱抓取失败: {str(e)}", code=500)


# ============================================================
# 邮件发送
# ============================================================

@router.post("/send")
async def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """发送邮件（Resend免费额度 + SMTP回退）。"""
    try:
        from app.services.ubrain.email_send_service import EmailSendService
        service = EmailSendService()
        result = await service.send(
            to_email=to_email,
            subject=subject,
            body=body,
            from_name=from_name,
            reply_to=reply_to,
        )
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"邮件发送失败: {str(e)}", code=500)


# ============================================================
# 线索管理
# ============================================================

@router.get("/prospects")
@async_cache_decorator(ttl=60)
async def list_prospects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    source: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """查询线索列表。"""
    try:
        from app.db.session import SessionLocal
        from app.models.prospect_lead import ProspectLead
        db = SessionLocal()
        try:
            query = db.query(ProspectLead)
            if status:
                query = query.filter(ProspectLead.status == status)
            if source:
                query = query.filter(ProspectLead.source == source)
            total = query.count()
            items = (
                query.order_by(ProspectLead.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return success_response(data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [item.to_dict() for item in items],
            })
        finally:
            db.close()
    except Exception as e:
        return error_response(message=f"查询线索失败: {str(e)}", code=500)


@router.get("/prospects/{prospect_id}")
async def get_prospect(
    prospect_id: str,
    current_user=Depends(get_current_user),
):
    """获取单个线索详情。"""
    try:
        from app.db.session import SessionLocal
        from app.models.prospect_lead import ProspectLead
        db = SessionLocal()
        try:
            prospect = db.query(ProspectLead).filter(
                ProspectLead.id == prospect_id
            ).first()
            if not prospect:
                raise HTTPException(status_code=404, detail="线索不存在")
            return success_response(data=prospect.to_dict())
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}", code=500)


# ============================================================
# 邮件外展
# ============================================================

@router.post("/outreach")
async def create_outreach(
    prospect_id: str,
    template_id: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """创建邮件外展任务（状态机管理）。"""
    try:
        from app.db.session import SessionLocal
        from app.models.email_outreach import EmailOutreach
        from app.services.ubrain.email_outreach_service import EmailOutreachService
        import uuid
        db = SessionLocal()
        try:
            outreach = EmailOutreach(
                id=str(uuid.uuid4()),
                prospect_id=prospect_id,
                template_id=template_id,
                subject=subject,
                body=body,
                status="draft",
                user_id=current_user.id,
            )
            db.add(outreach)
            db.commit()
            db.refresh(outreach)
            # 异步发送
            service = EmailOutreachService()
            await service.queue_send(outreach.id)
            return success_response(data=outreach.to_dict())
        finally:
            db.close()
    except Exception as e:
        return error_response(message=f"创建外展失败: {str(e)}", code=500)


@router.get("/outreach")
async def list_outreach(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """查询邮件外展任务列表。"""
    try:
        from app.db.session import SessionLocal
        from app.models.email_outreach import EmailOutreach
        db = SessionLocal()
        try:
            query = db.query(EmailOutreach)
            if status:
                query = query.filter(EmailOutreach.status == status)
            total = query.count()
            items = (
                query.order_by(EmailOutreach.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return success_response(data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [item.to_dict() for item in items],
            })
        finally:
            db.close()
    except Exception as e:
        return error_response(message=f"查询外展失败: {str(e)}", code=500)


# ============================================================
# 获客能力概览
# ============================================================

@router.get("/capabilities")
@async_cache_decorator(ttl=300)
async def get_capabilities(current_user=Depends(get_current_user)):
    """获取获客引擎能力矩阵（零成本模式）。"""
    return success_response(data={
        "email_verification": {
            "method": "MX + SMTP RCPT TO",
            "cost": "$0",
            "daily_limit": 100,
            "accuracy": "85%+",
        },
        "email_scraping": {
            "method": "Contact/About page parsing",
            "cost": "$0",
            "max_depth": 5,
        },
        "email_sending": {
            "provider": "Resend (free tier) + SMTP fallback",
            "cost": "$0 (100/day free)",
            "features": ["DKIM", "SPF", "DMARC", "tracking pixel"],
        },
        "lead_dedup": {
            "method": "4-tier deduplication engine",
            "tiers": ["email exact", "LinkedIn URL", "domain+company fuzzy", "phone"],
        },
        "outreach": {
            "method": "12-state email state machine",
            "features": ["idempotency", "drip sequences", "bounce handling"],
        },
    })