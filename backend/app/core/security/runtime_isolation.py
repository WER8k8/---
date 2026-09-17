# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""运行时租户隔离 — 应用层访问控制

作为租户隔离体系的最后一道防线，在应用运行时验证：
- 当前请求的 tenant_id 与目标资源的 tenant_id 是否匹配
- 防止因代码缺陷或逻辑错误导致的跨租户数据访问

使用场景:
  - Service 层方法中，操作资源前调用 assert_tenant_access
  - 作为防御性编程手段，在关键数据访问点进行校验
  - 与 RLS 形成互补：RLS 在数据库层兜底，此模块在应用层主动拦截

工作流程:
  1. 从请求上下文获取当前 tenant_id
  2. 从数据库加载目标资源
  3. 调用 assert_tenant_access(resource.tenant_id)
  4. 不匹配则立即抛出 TenantAccessDenied 异常
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request, status

from app.core.tenant_middleware import get_current_tenant

log = logging.getLogger(__name__)


class TenantAccessDenied(HTTPException):
    """租户访问拒绝异常。

    当检测到跨租户访问尝试时抛出，返回 403 Forbidden。
    """
    def __init__(
        self,
        resource_tenant_id: str = "",
        current_tenant_id: str = "",
        detail: str = "无权访问该资源",
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param resource_tenant_id: 参数 resource_tenant_id
        :param current_tenant_id: 参数 current_tenant_id
        :param detail: 参数 detail
        :return: 返回处理结果。
        """
        self.resource_tenant_id = resource_tenant_id
        self.current_tenant_id = current_tenant_id
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def assert_tenant_access(resource_tenant_id: str) -> None:
    """断言当前请求的 tenant_id 与资源的 tenant_id 匹配。

    从当前请求上下文中获取 tenant_id，与资源的 tenant_id 进行比对。
    不匹配则抛出 TenantAccessDenied 异常，阻止跨租户数据访问。

    Args:
        resource_tenant_id: 目标资源的 tenant_id

    Raises:
        TenantAccessDenied: 当前租户与资源租户不匹配

    Example:
        # 在 Service 层方法中:
        def get_product(product_id: str, request: Request):
            product = db.query(Product).get(product_id)
            assert_tenant_access(product.tenant_id)
            return product
    """
    from app.core.tenant_middleware import get_current_tenant
    from fastapi import Request as _Request
    # 从调用栈中获取 request 对象 —— 通过当前上下文
    current_tenant = _get_current_tenant_from_context()
    current_tenant_id = current_tenant.get("id", "") if current_tenant else ""
    # 平台级请求（无租户上下文）不进行限制
    if not current_tenant_id:
        return

    # 资源无 tenant_id（平台级资源）允许访问
    if not resource_tenant_id:
        return

    # 验证匹配
    if current_tenant_id != resource_tenant_id:
        log.warning(
            "[RuntimeIsolation] 跨租户访问被拒绝: current=%s, resource=%s",
            current_tenant_id,
            resource_tenant_id,
        )
        raise TenantAccessDenied(
            resource_tenant_id=resource_tenant_id,
            current_tenant_id=current_tenant_id,
            detail="无权访问该资源：租户隔离限制",
        )


def assert_tenant_access_with_request(
    request: Request,
    resource_tenant_id: str,
) -> None:
    """使用显式 request 对象断言租户访问权限。

    与 assert_tenant_access 功能相同，但接受显式 request 参数，
    适用于无法通过上下文获取 request 的场景（如后台任务、Celery worker）。

    Args:
        request: FastAPI 请求对象
        resource_tenant_id: 目标资源的 tenant_id

    Raises:
        TenantAccessDenied: 当前租户与资源租户不匹配

    Example:
        @router.get("/products/{id}")
        def get_product(id: str, request: Request, db: Session = Depends(get_db)):
            product = db.query(Product).get(id)
            assert_tenant_access_with_request(request, product.tenant_id)
            return product
    """
    current_tenant = get_current_tenant(request)
    current_tenant_id = current_tenant.get("id", "") if current_tenant else ""
    # 平台级请求（无租户上下文）不进行限制
    if not current_tenant_id:
        return

    # 资源无 tenant_id（平台级资源）允许访问
    if not resource_tenant_id:
        return

    # 验证匹配
    if current_tenant_id != resource_tenant_id:
        log.warning(
            "[RuntimeIsolation] 跨租户访问被拒绝: current=%s, resource=%s",
            current_tenant_id,
            resource_tenant_id,
        )
        raise TenantAccessDenied(
            resource_tenant_id=resource_tenant_id,
            current_tenant_id=current_tenant_id,
            detail="无权访问该资源：租户隔离限制",
        )


def verify_tenant_match(
    current_tenant_id: str,
    resource_tenant_id: str,
) -> bool:
    """验证两个 tenant_id 是否匹配（不抛异常版本）。

    用于需要自定义错误处理逻辑的场景。

    Args:
        current_tenant_id: 当前请求的租户 ID
        resource_tenant_id: 目标资源的租户 ID

    Returns:
        True 如果匹配或无需验证，False 如果不匹配

    Example:
        if not verify_tenant_match(current_id, resource_id):
            return error_response(403, "无权访问")
    """
    # 平台级请求不限制
    if not current_tenant_id:
        return True
    # 资源无 tenant_id 允许访问
    if not resource_tenant_id:
        return True
    return current_tenant_id == resource_tenant_id


def _get_current_tenant_from_context() -> Optional[dict]:
    """尝试从当前上下文中获取租户信息。

    优先从 request.state 获取（需要 request 对象在上下文中），
    否则返回 None。

    Returns:
        租户信息字典或 None
    """
    try:
        # 使用 FastAPI 的 Request 上下文
        from starlette.requests import Request as _StarletteRequest
        from contextvars import ContextVar
        # 尝试从 starlette 的上下文获取
        # 注意：这需要 request_context 在中间件中设置
        import contextvars
        request_var: Optional[contextvars.ContextVar] = contextvars.copy_context().get(
            "_request"
        )
        if request_var:
            request: Optional[_StarletteRequest] = request_var.get()
            if request:
                return getattr(request.state, "tenant", None)
    except Exception:
        pass
    return None


# 便捷别名 —— 与 assert_tenant_access 功能相同
check_tenant_access = assert_tenant_access
