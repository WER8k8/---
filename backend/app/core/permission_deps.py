"""权限依赖模块 - 统一权限检查"""

from functools import wraps

from fastapi import Depends, HTTPException

from app.core.permissions import has_permission, is_super_admin
from app.core.security import get_current_user
from app.models.user import User


def require_permission(resource: str, action: str):
    """权限检查装饰器"""
    def decorator(func):
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
                **kwargs):
            """wrapper。

            参数说明：
            :param current_user: 参数 current_user
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            if not has_permission(current_user.role, resource, action):
                raise HTTPException(status_code=403, detail="权限不足")
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_super_admin():
    """超级管理员权限检查装饰器"""
    def decorator(func):
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
                **kwargs):
            """wrapper。

            参数说明：
            :param current_user: 参数 current_user
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            if not is_super_admin(current_user.role):
                raise HTTPException(status_code=403, detail="需要超级管理员权限")
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_admin():
    """管理员权限检查装饰器（包含超级管理员）"""
    def decorator(func):
        """decorator。

        参数说明：
        :param func: 参数 func
        :return: 返回处理结果。
        """
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
                **kwargs):
            """wrapper。

            参数说明：
            :param current_user: 参数 current_user
            :param *args: 参数 *args
            :param **kwargs: 参数 **kwargs
            :return: 返回处理结果。
            """
            if current_user.role not in ["super_admin", "admin"]:
                raise HTTPException(status_code=403, detail="需要管理员权限")
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


class PermissionChecker:
    """权限检查器类"""
    def __init__(self, resource: str, action: str):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param resource: 参数 resource
        :param action: 参数 action
        :return: 返回处理结果。
        """
        self.resource = resource
        self.action = action

    async def __call__(self, current_user: User = Depends(get_current_user)):
        """__call__。

        参数说明：
        :param self: 参数 self
        :param current_user: 参数 current_user
        :return: 返回处理结果。
        """
        if not has_permission(current_user.role, self.resource, self.action):
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
