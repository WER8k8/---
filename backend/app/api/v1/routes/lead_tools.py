# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客工具集 API — FIX-38/39/40

CSV 导入导出、漏斗仪表板、ROI 计算器、Onboarding 引导
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from app.core.security import get_current_user
from app.core.response import success_response, error_response
from app.core.cache import async_cache_decorator

ROUTE_PREFIX = ""
router = APIRouter(prefix="/lead", tags=["获客引擎"])


# ============================================================
# FIX-38: CSV 导入导出
# ============================================================

@router.post("/import/csv")
async def import_leads_csv(
    file: UploadFile = File(...),
    skip_duplicates: bool = Query(True),
    current_user=Depends(get_current_user),
):
    """从 CSV 文件导入线索。"""
    if not file.filename or not file.filename.endswith(".csv"):
        return error_response(message="仅支持 CSV 文件", code=400)

    try:
        content = await file.read()
        from app.services.ubrain.lead_csv_service import LeadCSVService
        service = LeadCSVService()
        result = await service.import_csv(
            content,
            tenant_id=getattr(current_user, "tenant_id", ""),
            skip_duplicates=skip_duplicates,
        )
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"导入失败: {str(e)}", code=500)


@router.post("/import/csv/validate")
async def validate_csv(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """预验证 CSV 文件（不实际导入）。"""
    if not file.filename or not file.filename.endswith(".csv"):
        return error_response(message="仅支持 CSV 文件", code=400)

    try:
        content = await file.read()
        from app.services.ubrain.lead_csv_service import LeadCSVValidator
        result = LeadCSVValidator.validate_file(content)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"验证失败: {str(e)}", code=500)


@router.get("/export/csv")
async def export_leads_csv(
    status: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    current_user=Depends(get_current_user),
):
    """导出线索为 CSV 文件。"""
    try:
        from app.services.ubrain.lead_csv_service import LeadCSVService
        service = LeadCSVService()
        filters = {}
        if status:
            filters["status"] = status
        if source:
            filters["source"] = source
        if min_score is not None:
            filters["min_score"] = min_score

        csv_content = await service.export_csv(filters=filters)
        return StreamingResponse(
            io.BytesIO(csv_content),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=leads_export.csv",
            },
        )
    except Exception as e:
        return error_response(message=f"导出失败: {str(e)}", code=500)


# ============================================================
# FIX-39: 获客漏斗仪表板 + ROI 计算器
# ============================================================

@router.get("/funnel")
@async_cache_decorator(ttl=300)
async def get_lead_funnel(current_user=Depends(get_current_user)):
    """获取获客漏斗数据。"""
    try:
        from app.db.session import SessionLocal
        from app.models.prospect_lead import ProspectLead
        from app.models.email_outreach import EmailOutreach
        from datetime import datetime, timedelta
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 漏斗各阶段统计
            total_leads = db.query(ProspectLead).filter(
                ProspectLead.created_at >= month_start
            ).count()
            # 按状态统计
            from sqlalchemy import func
            status_counts = (
                db.query(ProspectLead.status, func.count(ProspectLead.id))
                .filter(ProspectLead.created_at >= month_start)
                .group_by(ProspectLead.status)
                .all()
            )
            status_map = {s: c for s, c in status_counts}
            # 邮件外展统计
            outreach_total = db.query(EmailOutreach).filter(
                EmailOutreach.created_at >= month_start
            ).count()
            outreach_sent = db.query(EmailOutreach).filter(
                EmailOutreach.created_at >= month_start,
                EmailOutreach.status.in_(["sent", "delivered", "opened", "clicked", "replied"]),
            ).count()
            outreach_opened = db.query(EmailOutreach).filter(
                EmailOutreach.created_at >= month_start,
                EmailOutreach.status.in_(["opened", "clicked", "replied"]),
            ).count()
            outreach_replied = db.query(EmailOutreach).filter(
                EmailOutreach.created_at >= month_start,
                EmailOutreach.status == "replied",
            ).count()
            funnel = {
                "period": "本月",
                "stages": [
                    {"name": "线索总数", "count": total_leads, "color": "#4a9b8c"},
                    {"name": "已验证", "count": status_map.get("verified", 0), "color": "#2563eb"},
                    {"name": "已联系", "count": status_map.get("contacted", 0), "color": "#f59e0b"},
                    {"name": "已回复", "count": status_map.get("responded", 0), "color": "#8b5cf6"},
                    {"name": "有兴趣", "count": status_map.get("interested", 0), "color": "#ec4899"},
                    {"name": "洽谈中", "count": status_map.get("negotiating", 0), "color": "#f97316"},
                    {"name": "已成交", "count": status_map.get("won", 0), "color": "#10b981"},
                ],
                "email_stats": {
                    "total_sent": outreach_sent,
                    "opened": outreach_opened,
                    "replied": outreach_replied,
                    "open_rate": round(outreach_opened / max(1, outreach_sent) * 100, 1),
                    "reply_rate": round(outreach_replied / max(1, outreach_sent) * 100, 1),
                },
                "conversion_rates": {
                    "lead_to_contacted": round(
                        status_map.get("contacted", 0) / max(1, total_leads) * 100, 1
                    ),
                    "contacted_to_interested": round(
                        status_map.get("interested", 0) / max(1, status_map.get("contacted", 1)) * 100, 1
                    ),
                    "interested_to_won": round(
                        status_map.get("won", 0) / max(1, status_map.get("interested", 1)) * 100, 1
                    ),
                    "overall": round(
                        status_map.get("won", 0) / max(1, total_leads) * 100, 1
                    ),
                },
            }
            return success_response(data=funnel)
        finally:
            db.close()
    except Exception as e:
        return error_response(message=f"获取漏斗失败: {str(e)}", code=500)


@router.get("/roi")
@async_cache_decorator(ttl=600)
async def get_roi_calculator(current_user=Depends(get_current_user)):
    """获客 ROI 计算器。"""
    return success_response(data={
        "calculator": {
            "title": "获客 ROI 计算器",
            "description": "基于实际数据计算获客投入产出比",
            "formula": "ROI = (成交金额 - 获客成本) / 获客成本 × 100%",
            "default_values": {
                "avg_deal_value": 5000,       # 平均成交金额（美元）
                "lead_to_deal_rate": 5,        # 线索到成交转化率（%）
                "monthly_plan_cost": 79,       # 月费（Growth套餐）
                "credit_pack_cost": 0,         # 额外积分支出
            },
            "scenarios": [
                {
                    "name": "保守估计",
                    "leads_per_month": 50,
                    "deal_rate": 3,
                    "avg_deal": 3000,
                    "monthly_cost": 29,
                    "roi": round((50 * 0.03 * 3000 - 29) / 29 * 100, 0),
                },
                {
                    "name": "正常估计",
                    "leads_per_month": 200,
                    "deal_rate": 5,
                    "avg_deal": 5000,
                    "monthly_cost": 79,
                    "roi": round((200 * 0.05 * 5000 - 79) / 79 * 100, 0),
                },
                {
                    "name": "乐观估计",
                    "leads_per_month": 500,
                    "deal_rate": 8,
                    "avg_deal": 8000,
                    "monthly_cost": 199,
                    "roi": round((500 * 0.08 * 8000 - 199) / 199 * 100, 0),
                },
            ],
        },
    })


# ============================================================
# FIX-40: Onboarding 引导 + Aha Moment
# ============================================================

@router.get("/onboarding")
@async_cache_decorator(ttl=86400)
async def get_onboarding_guide(current_user=Depends(get_current_user)):
    """获取新手引导流程。"""
    return success_response(data={
        "title": "3步上手，10分钟感受价值",
        "steps": [
            {
                "step": 1,
                "title": "选择行业模板",
                "time": "0-2分钟",
                "description": "从20+行业模板中选择最适合你的，AI自动生成专业出海官网",
                "action": "前往模板市场",
                "route": "/client/templates",
                "icon": "template",
            },
            {
                "step": 2,
                "title": "AI搜索第一批客户",
                "time": "2-5分钟",
                "description": "输入你的产品关键词，AI自动搜索潜在客户并验证邮箱",
                "action": "开始搜索",
                "route": "/client/lead-search",
                "icon": "search",
            },
            {
                "step": 3,
                "title": "发送第一封AI开发信",
                "time": "5-8分钟",
                "description": "选择AI生成的开发信模板，一键发送给潜在客户",
                "action": "发送邮件",
                "route": "/client/outreach",
                "icon": "mail",
            },
        ],
        "aha_moment": {
            "title": "Aha! 你做到了",
            "trigger": "当第一封邮件被打开时",
            "message": "恭喜！你的开发信已经被潜在客户打开。AI获客引擎正在为你工作，7x24小时不间断。",
            "next_steps": [
                "查看邮件追踪数据",
                "设置自动跟进序列",
                "邀请团队成员加入",
            ],
        },
        "quick_wins": [
            {
                "title": "完善公司信息",
                "description": "补充公司介绍和产品目录，AI会据此优化开发信内容",
                "impact": "提升回复率30%",
            },
            {
                "title": "设置邮件序列",
                "description": "配置3-5封自动跟进邮件，无需手动操作",
                "impact": "提升成交率50%",
            },
            {
                "title": "连接LinkedIn",
                "description": "导入LinkedIn人脉，AI自动匹配潜在客户",
                "impact": "扩展客户池3倍",
            },
        ],
    })