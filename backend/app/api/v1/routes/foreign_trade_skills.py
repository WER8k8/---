"""外贸 AI 技能 API 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import success_response, error_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/skills", tags=["外贸AI技能"])


def _ensure_skills_loaded():
    """确保所有技能已注册（懒加载）。"""
    from app.services.foreign_trade import skill_registry
    if not skill_registry.list_all():
        # 触发 import 以注册技能
        import app.services.foreign_trade.prospect_skill  # noqa: F401
        import app.services.foreign_trade.cold_email_skill  # noqa: F401
        import app.services.foreign_trade.customer_research_skill  # noqa: F401
        import app.services.foreign_trade.competitor_profile_skill  # noqa: F401
        import app.services.foreign_trade.sales_enablement_skill  # noqa: F401
        import app.services.foreign_trade.seo_audit_skill  # noqa: F401
        import app.services.foreign_trade.copywriting_skill  # noqa: F401


@router.get("/")
def list_skills(
    current_user: User = Depends(get_current_user),
):
    """列出所有已注册的外贸 AI 技能。"""
    _ensure_skills_loaded()
    from app.services.foreign_trade import skill_registry
    skills = skill_registry.list_all()
    return success_response(data={"skills": skills, "total": len(skills)})


@router.post("/{skill_name}")
async def execute_skill(
    skill_name: str,
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行指定的外贸 AI 技能。"""
    _ensure_skills_loaded()
    from app.services.foreign_trade import skill_registry
    skill = skill_registry.get(skill_name)
    if not skill:
        return error_response(404, f"技能 '{skill_name}' 不存在")

    # 参数校验
    for field_name, field_meta in skill.input_schema.items():
        if field_meta.get("required") and field_name not in req:
            return error_response(400, f"缺少必填参数: {field_name}")

    # 填充默认值
    for field_name, field_meta in skill.input_schema.items():
        if field_name not in req and "default" in field_meta:
            req[field_name] = field_meta["default"]

    result = await skill_registry.execute(skill_name, req)
    if result.success:
        return success_response(
            data={
                "skill": skill_name,
                "result": result.data,
                "model_used": result.model_used,
            },
            message=f"技能 '{skill.display_name}' 执行成功",
        )
    else:
        return error_response(500, result.error or "技能执行失败")
