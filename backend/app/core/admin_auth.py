"""超级管理员 RBAC 权限鉴权"""

from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.cache import delete_pattern, get_cache, redis_client, set_cache
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.admin import AdminMenu, AdminRole, RolePermission
from app.models.user import User


async def get_current_super_admin(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """超级管理员鉴权依赖 — 仅 super_admin 角色可访问"""
    if user is None or user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )

    # Redis 会话校验（防止 token 泄露后被吊销的会话仍可使用）
    token = _extract_token(request)
    if token and redis_client:
        jti = _get_token_jti(token)
        if jti:
            blacklisted = redis_client.get(f"admin_session_revoked:{user.id}:{jti}")
            if blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="会话已失效，请重新登录",
                )

    return user


async def get_user_permission_codes(
    user: User, db: Session
) -> List[str]:
    """获取用户的所有权限码（带 Redis 缓存）"""
    cache_key = f"perm:{user.id}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

    codes = _load_permission_codes(user, db)
    if redis_client:
        set_cache(cache_key, codes)

    return codes


def _load_permission_codes(user: User, db: Session) -> List[str]:
    """从数据库加载用户权限码"""
    if user.role == "super_admin":
        return ["*:*"]

    codes = []
    if user.role_id:
        role = db.query(AdminRole).filter(AdminRole.id == user.role_id).first()
        if role:
            permissions = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == role.id)
                .all()
            )
            from app.models.admin import AdminPermission
            perm_ids = [p.permission_id for p in permissions]
            perms = (
                db.query(AdminPermission)
                .filter(AdminPermission.id.in_(perm_ids))
                .all()
            )
            codes = [p.code for p in perms]

    return codes


def require_super_admin():
    """FastAPI 依赖: 仅超级管理员"""
    return Depends(get_current_super_admin)


def check_permission_code(role: str, code: str) -> bool:
    """H-04: 权限桥接函数 — 检查角色是否有某个权限码。

    用于连接两套权限系统：
    - Role 枚举 (permissions.py)
    - AdminRole 数据库 (本模块)

    角色为 super_admin 时始终返回 True。
    其他角色：仅当该角色在 ROLE_PERMISSIONS 中持有对应
    资源+操作时返回 True（与 has_permission 一致）。

    注：完整数据库权限检查需 User 对象 + DB session，
    请使用 require_permission_code 依赖注入。
    """
    if role == "super_admin":
        return True
    # 通过枚举权限表做轻量检查
    from app.core.permissions import has_permission as _enum_has
    resource, _, action = code.partition(":")
    if not resource or not action:
        return False
    return _enum_has(role, resource, action)


def require_permission_code(required_code: str):
    """FastAPI 依赖工厂: 校验特定权限码"""
    async def checker(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        """checker。

        参数说明：
        :param request: 参数 request
        :param user: 参数 user
        :param db: 参数 db
        :return: 返回处理结果。
        """
        codes = await get_user_permission_codes(user, db)
        if "*:*" in codes:
            return user
        if required_code not in codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {required_code}",
            )
        return user

    return Depends(checker)


def require_any_permission(required_codes: List[str]):
    """FastAPI 依赖工厂: 满足任意一个权限码即可"""
    async def checker(
        request: Request,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        """checker。

        参数说明：
        :param request: 参数 request
        :param user: 参数 user
        :param db: 参数 db
        :return: 返回处理结果。
        """
        codes = await get_user_permission_codes(user, db)
        if "*:*" in codes:
            return user
        if not any(c in codes for c in required_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少以下任一权限: {', '.join(required_codes)}",
            )
        return user

    return Depends(checker)


def invalidate_user_permission_cache(user_id: str) -> None:
    """清除用户权限缓存"""
    delete_pattern(f"perm:{user_id}")
    delete_pattern(f"menu:{user_id}:*")


def _extract_token(request: Request) -> Optional[str]:
    """_extract_token。

    参数说明：
    :param request: 参数 request
    :return: 返回处理结果。
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def _get_token_jti(token: str) -> Optional[str]:
    """_get_token_jti。

    参数说明：
    :param token: 参数 token
    :return: 返回处理结果。
    """
    try:
        import jwt
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        return payload.get("jti")
    except Exception:
        return None


def build_menu_tree(
    user: User, db: Session, parent_id: Optional[str] = None
) -> List[dict]:
    """构建用户可见的菜单树"""
    cache_key = f"menu:{user.id}:{parent_id or 'root'}"
    cached = get_cache(cache_key)
    if isinstance(cached, list):
        return cached

    # 获取用户权限码
    codes = _load_permission_codes(user, db)
    has_all = "*:*" in codes
    # 查询菜单
    menus = (
        db.query(AdminMenu)
        .filter(
            AdminMenu.parent_id == parent_id,
            AdminMenu.visible == True,
        )
        .order_by(AdminMenu.sort_order)
        .all()
    )
    tree = []
    for menu in menus:
        # 权限过滤
        if menu.permission_code and not has_all:
            if menu.permission_code not in codes:
                continue

        node = {
            "id": str(menu.id),
            "title": menu.title,
            "icon": menu.icon,
            "path": menu.path,
            "permission_code": menu.permission_code,
            "sort_order": menu.sort_order,
            "meta": {},
        }
        if menu.meta_json:
            import json
            try:
                node["meta"] = json.loads(menu.meta_json)
            except Exception:
                pass

        # 递归子菜单
        children = build_menu_tree(user, db, menu.id)
        if children:
            node["children"] = children

        tree.append(node)

    # 修复：set_cache 内部已做 json.dumps，此处不得二次序列化，
    # 否则缓存命中时取回字符串，导致 /admin-bff/menu/routes 500
    set_cache(cache_key, tree)
    return tree
