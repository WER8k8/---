"""超级管理员种子数据初始化

在 init_db() 之后调用，插入默认角色/权限/菜单数据。
幂等操作——已存在的数据不会被重复插入。
"""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.admin import (AdminMenu, AdminPermission, AdminRole,
                               RolePermission)
from app.models.ai_config import CCSwitchConfig
from app.models.tenant import TenantPlan


def _uid(prefix: str) -> str:
    """生成合法 UUID 字符串。

    PostgreSQL 下 admin_roles / admin_permissions / admin_menus 等表的 id
    列为 UUID 类型，早期实现返回 `prefix-xxxxxxxxxxxx` 这类非 UUID 字符串，
    会在写入时触发 InvalidTextRepresentation 并被 main.py 静默吞掉，
    导致角色/权限/菜单种子数据全为空。此处统一返回标准 UUID 字符串。

    参数说明：
    :param prefix: 仅保留兼容性，不再参与生成结果
    :return: 标准 UUID 字符串
    """
    return str(uuid.uuid4())


# 固定命名空间，保证同一字面量 ID 每次运行都得到同一个 UUID（幂等）
_SEED_UUID_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _sid(raw: str) -> str:
    """把种子字面量 ID 归一为合法 UUID 字符串。

    若入参本身已是合法 UUID 则原样返回，否则用 uuid5 派生一个稳定 UUID，
    保证多次运行映射关系一致（角色、权限、菜单的父子引用不会错乱）。

    参数说明：
    :param raw: 原始字面量 ID
    :return: 合法 UUID 字符串
    """
    try:
        uuid.UUID(str(raw))
        return str(raw)
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid5(_SEED_UUID_NS, str(raw)))


def seed_super_admin(db: Session) -> dict:
    """运行所有种子数据，返回统计信息"""
    result = {
        "roles": _seed_roles(db),
        "permissions": _seed_permissions(db),
        "role_permissions": _seed_role_permissions(db),
        "menus": _seed_menus(db),
        "tenant_plans": _seed_tenant_plans(db),
        "egress_demo_purged": _purge_demo_egress_pool(db),
        "egress_suppliers": _seed_egress_suppliers(db),
    }
    db.commit()
    return result


def _seed_roles(db: Session) -> int:
    """_seed_roles。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    count = 0
    defaults = [
        ("role-super-admin-001", "super_admin", "超级管理员（系统内置）", True, 0),
        ("role-seo-admin-001", "seo_admin", "SEO管理员", True, 1),
        ("role-editor-001", "editor", "内容编辑", True, 2),
        ("role-viewer-001", "viewer", "只读访客", True, 3),
    ]
    for rid, name, desc, is_sys, order in defaults:
        exists = db.query(AdminRole).filter(AdminRole.id == _sid(rid)).first()
        if not exists:
            db.add(AdminRole(
                id=_sid(rid), name=name, description=desc,
                is_system=is_sys, sort_order=order,
            ))
            count += 1
    db.flush()
    return count


def _seed_permissions(db: Session) -> int:
    """_seed_permissions。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    count = 0
    perms = [
        # 大盘
        ("perm-dashboard", "dashboard:read", "首页大盘-查看", "dashboard"),
        ("perm-dashboard-ai", "dashboard:ai_stats", "AI产出统计-查看", "dashboard"),
        # 内容工厂
        ("perm-content-all", "content:*", "内容管理全部", "content"),
        ("perm-content-create", "content:create", "内容创建", "content"),
        # 分发与收录
        ("perm-publish-all", "publish:*", "分发收录全部", "publish"),
        ("perm-seo-all", "seo:*", "SEO全部功能", "seo"),
        # AI 运营
        ("perm-ai-read", "ai:read", "AI配置-查看", "ai"),
        ("perm-ai-write", "ai:write", "AI配置-编辑", "ai"),
        ("perm-ai-kb", "ai:knowledge_base", "知识库管理", "ai"),
        ("perm-ai-langchain", "ai:langchain", "LangChain控制台", "ai"),
        ("perm-ai-ccswitch", "ai:cc_switch", "CC Switch配置", "ai"),
        ("perm-ai-cost", "ai:cost", "AI成本分析", "ai"),
        # 数据分析
        ("perm-analytics-all", "analytics:*", "数据分析全部", "analytics"),
        ("perm-content-score", "content:score", "内容质量评分", "analytics"),
        # 告警
        ("perm-alerts-read", "alerts:read", "告警中心-查看", "alerts"),
        ("perm-alerts-write", "alerts:write", "告警规则-管理", "alerts"),
        # 系统管理
        ("perm-users-read", "users:read", "用户管理-查看", "system"),
        ("perm-users-write", "users:write", "用户管理-编辑", "system"),
        ("perm-roles-read", "roles:read", "角色管理-查看", "system"),
        ("perm-roles-write", "roles:write", "角色管理-编辑", "system"),
        ("perm-logs-read", "logs:read", "操作日志-查看", "system"),
        ("perm-config-read", "config:read", "系统配置-查看", "system"),
        ("perm-config-write", "config:write", "系统配置-编辑", "system"),
        ("perm-monitor-read", "monitor:read", "系统监控-查看", "system"),
        ("perm-monitor-write", "monitor:write", "系统监控-操作", "system"),
        ("perm-cache-manage", "cache:manage", "缓存管理", "system"),
        ("perm-data-export", "data:export", "数据导入导出", "system"),
        ("perm-search-global", "search:global", "全局搜索", "system"),
        ("perm-products-all", "products:*", "产品管理全部", "business"),
        # 业务
        ("perm-business", "business:all", "业务功能区-全部", "business"),
    ]
    for pid, code, name, group_name in perms:
        exists = db.query(AdminPermission).filter(AdminPermission.id == _sid(pid)).first()
        if not exists:
            db.add(AdminPermission(id=_sid(pid), code=code, name=name, group_name=group_name))
            count += 1
    db.flush()
    return count


def _seed_role_permissions(db: Session) -> int:
    """_seed_role_permissions。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    count = 0
    # super_admin 获得所有权限
    all_perms = db.query(AdminPermission).all()
    for perm in all_perms:
        rp_id = _sid(f"rp-sa-{perm.id}")
        exists = db.query(RolePermission).filter(RolePermission.id == rp_id).first()
        if not exists:
            db.add(RolePermission(id=rp_id, role_id=_sid("role-super-admin-001"), permission_id=perm.id))
            count += 1

    # seo_admin 获得 SEO + 内容 + 分析 相关权限
    seo_codes = [
        "dashboard:read", "dashboard:ai_stats",
        "seo:*", "content:*", "publish:*",
        "ai:read", "ai:knowledge_base", "ai:langchain", "ai:cost",
        "analytics:*", "content:score",
        "alerts:read",
        "logs:read", "config:read",
    ]
    seo_perms = db.query(AdminPermission).filter(AdminPermission.code.in_(seo_codes)).all()
    for perm in seo_perms:
        rp_id = _sid(f"rp-seo-{perm.id}")
        exists = db.query(RolePermission).filter(RolePermission.id == rp_id).first()
        if not exists:
            db.add(RolePermission(id=rp_id, role_id=_sid("role-seo-admin-001"), permission_id=perm.id))
            count += 1

    db.flush()
    return count


def _seed_menus(db: Session) -> int:
    """_seed_menus。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    count = 0
    # 按工作流驱动的菜单结构（使用频率 + 业务流程 组织）
    menus = [
        # === 首页大盘 (每次登录第一眼) ===
        (None, "menu-dashboard", "首页大盘", "dashboard", "/admin/dashboard", "dashboard:read", 0, {"badge": ""}),
        ("menu-dashboard", None, "业务概览", "chart", "/admin/dashboard", "dashboard:read", 0, {}),
        ("menu-dashboard", None, "告警中心", "bell", "/admin/dashboard/alerts", "alerts:read", 1, {"badge": "new"}),
        # === 内容工厂 (最常操作: 生成/编辑/发布) ===
        (None, "menu-content-factory", "内容工厂", "edit", "/admin/content-factory", "content:*", 10, {}),
        ("menu-content-factory", None, "AI 批量生成", "robot", "/admin/content-factory/generate", "content:create", 0, {"highlight": True}),
        ("menu-content-factory", None, "文章管理", "file-text", "/admin/business/content", "content:*", 1, {}),
        ("menu-content-factory", None, "模板管理", "layout", "/admin/content-factory/templates", "content:*", 2, {}),
        ("menu-content-factory", None, "产品管理", "shop", "/admin/business/products", "products:*", 3, {}),
        ("menu-content-factory", None, "新闻管理", "read", "/admin/business/news", "business:all", 4, {}),
        ("menu-content-factory", None, "案例中心", "picture", "/admin/business/cases", "business:all", 5, {}),
        ("menu-content-factory", None, "询盘管理", "mail", "/admin/business/inquiries", "business:all", 6, {}),
        # === 分发与收录 (核心 KPI: 发了多少、收了多少) ===
        (None, "menu-distribution", "分发与收录", "send", "/admin/distribution", "publish:*", 20, {}),
        ("menu-distribution", None, "平台账号", "key", "/admin/distribution/platforms", "publish:*", 0, {}),
        ("menu-distribution", None, "发布队列", "ordered-list", "/admin/distribution/publish", "publish:*", 1, {}),
        ("menu-distribution", None, "收录监控", "eye", "/admin/distribution/inclusion", "seo:*", 2, {}),
        ("menu-distribution", None, "SEO 矩阵", "table", "/seo-matrix/dashboard", "seo:*", 3, {"badge": "核心"}),
        # === AI 运营 (成本中心) ===
        (None, "menu-ai-ops", "AI 运营", "robot", "/admin/ai-ops", "ai:read", 30, {}),
        ("menu-ai-ops", None, "调用统计", "bar-chart", "/admin/ai-ops/stats", "ai:read", 0, {}),
        ("menu-ai-ops", None, "成本分析", "dollar", "/admin/ai/cost", "ai:cost", 1, {"highlight": True}),
        ("menu-ai-ops", None, "模型配置", "setting", "/admin/ai/models", "ai:write", 2, {}),
        ("menu-ai-ops", None, "LangChain 控制台", "code", "/admin/ai/langchain", "ai:langchain", 3, {}),
        ("menu-ai-ops", None, "CC Switch 中转", "swap", "/admin/ai/cc-switch", "ai:cc_switch", 4, {}),
        # === 数据分析 (老板视角) ===
        (None, "menu-analytics", "数据分析", "fund", "/admin/analytics", "analytics:*", 40, {}),
        ("menu-analytics", None, "SEO 效果", "rise", "/admin/analytics/seo", "seo:*", 0, {}),
        ("menu-analytics", None, "内容质量", "star", "/admin/analytics/quality", "content:score", 1, {}),
        ("menu-analytics", None, "竞品对比", "radar-chart", "/admin/analytics/competitor", "analytics:*", 2, {}),
        # === 系统管理 (低频操作) ===
        (None, "menu-system", "系统管理", "setting", "/admin/system", "users:read", 50, {}),
        ("menu-system", None, "用户与权限", "team", "/admin/permissions/users", "users:read", 0, {}),
        ("menu-system", None, "系统配置", "tool", "/admin/config/basic", "config:read", 1, {}),
        ("menu-system", None, "操作日志", "audit", "/admin/tools/logs", "logs:read", 2, {}),
        ("menu-system", None, "系统监控", "cloud-server", "/admin/tools/monitor", "monitor:read", 3, {}),
    ]
    for parent_title, menu_id, title, icon, path, perm_code, order, meta in menus:
        if parent_title is None:
            parent_id = None
        else:
            parent_id = _sid(parent_title)

        exists = db.query(AdminMenu).filter(
            AdminMenu.title == title,
            AdminMenu.parent_id == parent_id,
        ).first()
        if not exists:
            db.add(AdminMenu(
                id=_sid(menu_id) if menu_id else _uid("menu"),
                parent_id=parent_id,
                title=title,
                icon=icon,
                path=path,
                permission_code=perm_code,
                sort_order=order,
                visible=True,
                meta_json=json.dumps(meta, ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            count += 1

    db.flush()
    return count


def _seed_tenant_plans(db: Session) -> int:
    """初始化默认套餐数据（幂等）"""
    count = 0
    plans = [
        {
            "id": "plan-free-001",
            "name": "免费版",
            "code": "free",
            "price_monthly": 0,
            "price_yearly": 0,
            "max_users": 1,
            "max_sites": 1,
            "max_products": 10,
            "max_ai_quota": 100,
            "features": '["seo"]',
            "is_active": True,
        },
        {
            "id": "plan-basic-001",
            "name": "基础版",
            "code": "basic",
            "price_monthly": 29900,
            "price_yearly": 299000,
            "max_users": 3,
            "max_sites": 3,
            "max_products": 50,
            "max_ai_quota": 1000,
            "features": '["seo","analytics"]',
            "is_active": True,
        },
        {
            "id": "plan-pro-001",
            "name": "专业版",
            "code": "pro",
            "price_monthly": 69900,
            "price_yearly": 699000,
            "max_users": 10,
            "max_sites": 10,
            "max_products": 200,
            "max_ai_quota": 5000,
            "features": '["seo","analytics","globalization","international"]',
            "is_active": True,
        },
        {
            "id": "plan-enterprise-001",
            "name": "企业版",
            "code": "enterprise",
            "price_monthly": 199900,
            "price_yearly": 1999000,
            "max_users": 50,
            "max_sites": 50,
            "max_products": 1000,
            "max_ai_quota": 20000,
            "features": '["seo","analytics","globalization","international","content","ai"]',
            "is_active": True,
        },
        {
            "id": "plan-flagship-001",
            "name": "旗舰版",
            "code": "flagship",
            "price_monthly": 499900,
            "price_yearly": 4999000,
            "max_users": 999,
            "max_sites": 999,
            "max_products": 99999,
            "max_ai_quota": 100000,
            "features": '["seo","analytics","globalization","international","content","ai","white_label","api"]',
            "is_active": True,
        },
    ]
    for p in plans:
        p["id"] = _sid(p["id"])
        exists = db.query(TenantPlan).filter(TenantPlan.id == p["id"]).first()
        if not exists:
            db.add(TenantPlan(**p))
            count += 1
    db.flush()
    return count


def _purge_demo_egress_pool(db: Session) -> int:
    """启动时清除历史演示 IP，平台池只保留真实供应商录入。"""
    from app.services.egress.demo_guard import purge_demo_egress_endpoints
    return purge_demo_egress_endpoints(db)


def _seed_egress_suppliers(db: Session) -> int:
    """_seed_egress_suppliers。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    from app.services.egress_supplier_service import seed_default_suppliers
    return seed_default_suppliers(db)
