"""四壳解析 — 角色 → shell / homePath（UAC 唯一源）"""

from __future__ import annotations

from app.models.user import User

SHELL_CLIENT = "client"
SHELL_PLATFORM = "platform"
SHELL_PARTNER = "partner"
SHELL_AGENT = "agent"
SHELL_OPS = "ops"

HOME_PATHS: dict[str, str] = {
    SHELL_CLIENT: "/client/dashboard",
    SHELL_PLATFORM: "/admin/dashboard",
    SHELL_PARTNER: "/partner/performance",
    SHELL_AGENT: "/agent/performance",
    SHELL_OPS: "/dashboard",
}


def resolve_shell(user: User) -> str:
    """resolve_shell。

    参数说明：
    :param user: 参数 user
    :return: 返回处理结果。
    """
    role = user.role or "viewer"
    if role in ("super_admin", "admin"):
        return SHELL_PLATFORM
    if role == "l2":
        return SHELL_PARTNER
    if role in ("sales", "l3", "agent"):
        return SHELL_AGENT
    if role in ("tenant_admin", "editor", "viewer"):
        return SHELL_CLIENT
    return SHELL_OPS


def resolve_home_path(shell: str) -> str:
    """resolve_home_path。

    参数说明：
    :param shell: 参数 shell
    :return: 返回处理结果。
    """
    return HOME_PATHS.get(shell, HOME_PATHS[SHELL_CLIENT])
