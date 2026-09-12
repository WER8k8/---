"""全局搜索 API — 跨模块搜索

PII 加密说明：email 字段已加密，不支持 contains 模糊搜索。
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.field_crypto import decrypt_field
from app.core.response import success_response
from app.models.admin import AdminMenu, AdminPermission
from app.models.user import OperationLog, User

router = APIRouter()


def _try_decrypt(value: str) -> str:
    """尝试解密，兼容历史明文数据。"""
    if not value:
        return value
    try:
        return decrypt_field(value)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("解密字段失败，返回原始值: %s", e)
        return value


@router.get("")
def global_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """全局搜索：菜单、用户、权限、操作日志"""
    if not q or len(q.strip()) < 1:
        return success_response(data={"menus": [], "users": [], "results": []})

    q_like = f"%{q.strip()}%"
    results = []
    # 搜索菜单
    menus = db.query(AdminMenu).filter(
        or_(
            AdminMenu.title.contains(q),
            AdminMenu.path.contains(q),
        ),
        AdminMenu.visible == True,
    ).limit(5).all()
    for m in menus:
        results.append({
            "type": "menu",
            "title": m.title,
            "subtitle": m.path or "",
            "url": m.path or "/admin",
            "icon": "📋",
        })

    # 搜索用户（加密 email 不支持 contains，仅按用户名匹配）
    users = db.query(User).filter(
        User.username.contains(q),
    ).limit(5).all()
    for u in users:
        results.append({
            "type": "user",
            "title": u.username,
            "subtitle": f"{u.role} · {_try_decrypt(u.email)}",
            "url": f"/admin/permissions/users",
            "icon": "👤",
        })

    # 搜索权限
    perms = db.query(AdminPermission).filter(
        or_(
            AdminPermission.code.contains(q),
            AdminPermission.name.contains(q),
        )
    ).limit(5).all()
    for p in perms:
        results.append({
            "type": "permission",
            "title": p.name,
            "subtitle": p.code,
            "url": "/admin/permissions/roles",
            "icon": "🔑",
        })

    return success_response(data=results[:20])
