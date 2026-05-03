from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    SALES = "sales"
    VIEWER = "viewer"


ROLE_PERMISSIONS = {
    Role.ADMIN: {
        "products": ["create", "read", "update", "delete", "publish"],
        "cases": ["create", "read", "update", "delete", "publish"],
        "content": ["create", "read", "update", "delete", "publish"],
        "inquiries": ["read", "update", "delete", "export"],
        "seo": ["read", "update", "batch", "ai_optimize", "optimize"],  # 添加optimize权限
        "analytics": ["read"],
        "users": ["create", "read", "update", "delete"],
        "settings": ["read", "update"],
        "ab_test": ["create", "read", "update", "delete"],
    },
    Role.EDITOR: {
        "products": ["create", "read", "update", "publish"],
        "cases": ["create", "read", "update", "publish"],
        "content": ["create", "read", "update", "publish"],
        "inquiries": ["read"],
        "seo": ["read", "update", "ai_optimize"],
        "analytics": ["read"],
        "users": [],
        "settings": [],
        "ab_test": ["create", "read", "update"],
    },
    Role.SALES: {
        "products": ["read"],
        "cases": ["read"],
        "content": ["read"],
        "inquiries": ["read", "update", "export"],
        "seo": ["read"],
        "analytics": ["read"],
        "users": [],
        "settings": [],
    },
    Role.VIEWER: {
        "products": ["read"],
        "cases": ["read"],
        "content": ["read"],
        "inquiries": [],
        "seo": [],
        "analytics": [],
        "users": [],
        "settings": [],
    },
}


def has_permission(role: str, resource: str, action: str) -> bool:
    role_enum = Role(role) if role in [r.value for r in Role] else Role.VIEWER
    perms = ROLE_PERMISSIONS.get(role_enum, {})
    resource_perms = perms.get(resource, [])
    return action in resource_perms


def get_role_label(role: str) -> str:
    labels = {
        "admin": "管理员",
        "editor": "编辑",
        "sales": "销售",
        "viewer": "访客",
    }
    return labels.get(role, role)
