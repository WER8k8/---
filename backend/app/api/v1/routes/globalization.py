"""全球化与多语言路由 — 对接真实数据库"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.globalization import (
    GlossaryTermCreate, GlossaryTermUpdate,
    TranslationTaskCreate,
)
from app.services.globalization_service import GlobalizationService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/globalization"
ROUTE_TAGS = ["全球化多语言"]

router = APIRouter()
svc = GlobalizationService()


# ========== 概览 ==========

@router.get("/")
def get_globalization_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取全球化多语言概览（实时统计数据）"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    overview = svc.get_overview(db)
    return success_response(data=overview)


# ========== 术语库 ==========

@router.get("/glossary")
def list_glossary(
    page: int = 1,
    page_size: int = 20,
    search: str = Query(None),
    category: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取术语库列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    items, total = svc.list_glossary(db, page, page_size, search, category, status)
    return success_response(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/glossary")
def create_glossary_term(
    body: GlossaryTermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加术语"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    term = svc.create_glossary_term(db, body.model_dump())
    return success_response(data=term, message="术语已添加")


@router.put("/glossary/{term_id}")
def update_glossary_term(
    term_id: str,
    body: GlossaryTermUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新术语"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    term = svc.update_glossary_term(db, term_id, body.model_dump(exclude_none=True))
    if not term:
        return error_response(404, "术语不存在")
    return success_response(data=term, message="术语已更新")


@router.delete("/glossary/{term_id}")
def delete_glossary_term(
    term_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除术语"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    if svc.delete_glossary_term(db, term_id):
        return success_response(message="术语已删除")
    return error_response(404, "术语不存在")


@router.get("/glossary/stats")
def glossary_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """术语库统计"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(data=svc.get_glossary_stats(db))


# ========== 翻译引擎 ==========

@router.get("/translator")
def translator_status(
    current_user: User = Depends(get_current_user),
):
    """翻译引擎状态"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(data={
        "engine": "langchain-rag",
        "model": "qwen-coder-plus",
        "supported_langs": [
            {"code": "zh", "name": "中文"},
            {"code": "en", "name": "English"},
            {"code": "ja", "name": "日本語"},
            {"code": "ko", "name": "한국어"},
            {"code": "ar", "name": "العربية"},
            {"code": "th", "name": "ไทย"},
            {"code": "vi", "name": "Tiếng Việt"},
            {"code": "ru", "name": "Русский"},
            {"code": "es", "name": "Español"},
        ],
    })


# ========== 翻译任务 ==========

@router.get("/tasks")
def list_tasks(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """翻译任务列表"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    items, total = svc.list_tasks(db, page, page_size)
    return success_response(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/tasks")
def create_task(
    body: TranslationTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建翻译任务"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    task = svc.create_task(db, body.model_dump())
    return success_response(data=task, message="翻译任务已创建")


# ========== 翻译记录 ==========

@router.get("/records")
def list_records(
    task_id: str = Query(None),
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """翻译记录"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    items = svc.list_records(db, task_id, limit)
    return success_response(data={"items": items, "total": len(items)})


# ========== 文化适配 ==========

@router.get("/culture-adapt")
def culture_adapt_status(
    current_user: User = Depends(get_current_user),
):
    """文化适配配置"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    return success_response(data={
        "rtl_enabled": True,
        "currency_adaptation": True,
        "date_format_adaptation": True,
        "regions": [
            {"code": "US", "name": "美国", "flag": "🇺🇸"},
            {"code": "DE", "name": "德国", "flag": "🇩🇪"},
            {"code": "FR", "name": "法国", "flag": "🇫🇷"},
            {"code": "ES", "name": "西班牙", "flag": "🇪🇸"},
            {"code": "IT", "name": "意大利", "flag": "🇮🇹"},
            {"code": "NL", "name": "荷兰", "flag": "🇳🇱"},
            {"code": "PT", "name": "葡萄牙", "flag": "🇵🇹"},
            {"code": "RU", "name": "俄罗斯", "flag": "🇷🇺"},
            {"code": "TR", "name": "土耳其", "flag": "🇹🇷"},
            {"code": "SA", "name": "沙特", "flag": "🇸🇦"},
            {"code": "AE", "name": "阿联酋", "flag": "🇦🇪"},
            {"code": "JP", "name": "日本", "flag": "🇯🇵"},
            {"code": "KR", "name": "韩国", "flag": "🇰🇷"},
            {"code": "EU", "name": "欧盟", "flag": "🇪🇺"},
            # 南亚
            {"code": "IN", "name": "印度", "flag": "🇮🇳"},
            {"code": "ID", "name": "印尼", "flag": "🇮🇩"},
            {"code": "PH", "name": "菲律宾", "flag": "🇵🇭"},
            {"code": "BD", "name": "孟加拉", "flag": "🇧🇩"},
            {"code": "MM", "name": "缅甸", "flag": "🇲🇲"},
            {"code": "KH", "name": "柬埔寨", "flag": "🇰🇭"},
            # 中东欧
            {"code": "PL", "name": "波兰", "flag": "🇵🇱"},
            {"code": "CZ", "name": "捷克", "flag": "🇨🇿"},
            {"code": "UA", "name": "乌克兰", "flag": "🇺🇦"},
            # 北欧
            {"code": "SE", "name": "瑞典", "flag": "🇸🇪"},
            # 非洲
            {"code": "KE", "name": "肯尼亚", "flag": "🇰🇪"},
            {"code": "NG", "name": "尼日利亚", "flag": "🇳🇬"},
            {"code": "ZA", "name": "南非", "flag": "🇿🇦"},
            {"code": "ET", "name": "埃塞俄比亚", "flag": "🇪🇹"},
        ],
    })
