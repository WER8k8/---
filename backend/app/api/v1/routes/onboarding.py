"""租户入驻引导 API"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.response import success_response
from app.services.onboarding_service import (
    get_onboarding_status, complete_step, generate_sample_data,
    ONBOARDING_STEPS, ACHIEVEMENTS,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/onboarding", tags=["入驻引导"])


class CompleteStepBody(BaseModel):
    task_id: str


@router.get("/status")
async def onboarding_status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """获取入驻进度"""
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        return success_response({"progress": 100, "steps": [], "achievements": [], "is_complete": True})
    result = get_onboarding_status(db, tenant_id)
    return success_response(result)


@router.post("/complete-step")
async def complete_onboarding_step(body: CompleteStepBody, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """完成一个入驻任务"""
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        return success_response({"error": "no tenant"})
    result = complete_step(db, tenant_id, body.task_id)
    return success_response(result)


@router.post("/generate-sample")
async def gen_sample(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """生成示例数据"""
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        return success_response({"error": "no tenant"})
    result = generate_sample_data(db, tenant_id)
    return success_response(result)


@router.get("/achievements")
async def achievements(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """获取成就列表"""
    tenant_id = getattr(user, "tenant_id", None)
    from app.services.onboarding_service import _check_achievements
    status = get_onboarding_status(db, tenant_id) if tenant_id else {"achievements": []}
    return success_response(status.get("achievements", []))

