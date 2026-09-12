"""Permissions 权限矩阵（轮17-8）。

能力资源访问权限精确到五级：read / write / execute / delete / publish。
- 默认 NO ACCESS（none）；
- 判定：请求的 action ∈ 已授予的权限位；
- 未授予即拒绝（默认拒绝策略）。
MCP 工具的 permission 字段直接存储该五级之一 + none（对齐 mcp_tools 表）。
"""

from __future__ import annotations

from functools import total_ordering

# 权限位从低到高；高权限隐含持有部分低权限是"语义"而非自动继承——
# 判定时要求请求动作显式存在于已授权集合。
PERMISSIONS = ("read", "write", "execute", "delete", "publish")
NO_PERMISSION = "none"

# 动作 → 所需最小权限位（请求动作到授权的映射）
ACTION_NEEDS: dict[str, str] = {
    "view": "read",
    "list": "read",
    "invoke": "execute",
    "call": "execute",
    "create": "write",
    "update": "write",
    "delete": "delete",
    "publish": "publish",
    "rollback": "publish",
}


@total_ordering
class Permission:
    """单权限位对象（支持比较，便于排序/降级判定）。"""

    __slots__ = ("name", "_rank")

    def __init__(self, name: str) -> None:
        normalized = (name or "").strip().lower()
        if normalized not in PERMISSIONS and normalized != NO_PERMISSION:
            raise ValueError(
                f"非法权限: {name!r}（允许: {list(PERMISSIONS) + [NO_PERMISSION]}）"
            )
        self.name = normalized
        self._rank = PERMISSIONS.index(normalized) if normalized in PERMISSIONS else -1

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Permission):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other.strip().lower()
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Permission):
            return self._rank < other._rank
        if isinstance(other, str):
            return self._rank < PERMISSIONS.index(other.strip().lower())
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"Permission({self.name})"


def granted() -> set[str]:
    """返回 granted() 初始空授权集。"""
    return set()


def build_granted(*perms: str) -> set[str]:
    """把传入的权限名字符串加入授权集。"""
    out: set[str] = set()
    for p in perms:
        perm = Permission(p)
        if perm.name != NO_PERMISSION:
            out.add(perm.name)
    return out


def can(grants: set[str] | None, action: str) -> bool:
    """判定某动作是否被授权集覆盖。

    action 先映射到权限位，若权限位不存在则拒绝；授权集中含该权限位即允许。
    """
    grants = grants or set()
    needed = ACTION_NEEDS.get((action or "").strip().lower())
    if needed is None:
        return False
    return needed in grants


def describe(grants: set[str] | None, action: str) -> str:
    """返回"允许/拒绝"的人类可读判定说明（含需要的权限位）。"""
    needed = ACTION_NEEDS.get((action or "").strip().lower())
    if needed is None:
        return f"未知动作 {action!r}，默认拒绝"
    return "允许" if can(grants, action) else f"拒绝（需要 {needed} 权限）"


__all__ = [
    "PERMISSIONS",
    "NO_PERMISSION",
    "ACTION_NEEDS",
    "Permission",
    "can",
    "granted",
    "build_granted",
    "describe",
]