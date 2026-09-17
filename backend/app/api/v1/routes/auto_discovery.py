# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""API 路由自动发现 — FIX-30: 按业务域分包 + 自动注册

提供路由自动发现机制，扫描 routes/ 目录，自动注册所有 router 实例。

用法:
  from app.api.v1.routes.auto_discovery import auto_register_routes
  auto_register_routes(router, prefix="/v1")

约定:
  - 每个 .py 文件导出 `router: APIRouter` 实例
  - router 自带 prefix 和 tags（在模块内定义）
  - 跳过以 `_` 开头的文件
  - 跳过 `__init__.py` 和 `auto_discovery.py`

业务域分包:
  routes/
  ├── auth/           # 认证域
  ├── content/        # 内容域
  ├── commerce/       # 商业域
  ├── ai/             # AI 域
  ├── public/         # 公开 API
  ├── admin/          # 管理 API
  └── ...             # 其他域
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

log = logging.getLogger(__name__)

# 业务域映射：文件前缀 → 业务域标签
_DOMAIN_TAGS: dict[str, str] = {
    "auth": "认证",
    "user": "用户",
    "tenant": "租户",
    "product": "产品",
    "content": "内容",
    "inquiry": "询盘",
    "seo": "SEO",
    "analytics": "分析",
    "ai": "AI",
    "agent": "Agent",
    "lead": "获客",
    "email": "邮件",
    "payment": "支付",
    "order": "订单",
    "quote": "报价",
    "chat": "聊天",
    "forum": "社区",
    "media": "媒体",
    "public": "公开",
    "admin": "管理",
    "system": "系统",
    "health": "健康",
    "client": "租户端",
    "agent_portal": "代理端",
    "platform": "平台",
    "bff": "BFF",
    "ubrain": "UBrain",
    "hermes": "Hermes",
    "paperclip": "Paperclip",
    "wangcai": "旺财",
    "building": "建材百科",
    "foreign": "外贸",
    "cross": "跨境",
    "gdpr": "GDPR",
    "compliance": "合规",
    "news": "资讯",
    "case": "案例",
    "file": "文件",
    "domain": "域名",
    "ssl": "SSL",
    "edge": "Edge CDN",
    "logistics": "物流",
    "social": "社交",
    "referral": "推荐",
    "growth": "增长",
    "churn": "流失",
    "notification": "通知",
    "license": "许可",
    "skill": "技能",
    "token": "Token",
    "ops": "运维",
    "founder": "创始",
    "trade": "贸易",
    "hub": "Hub",
    "integration": "集成",
    "finance": "财务",
    "invoice": "发票",
    "review": "评论",
    "mobile": "移动端",
    "cognitive": "认知",
    "developer": "开发者",
    "knowledge": "知识库",
    "rank": "排名",
    "baidu": "百度",
    "feishu": "飞书",
    "international": "国际化",
    "globalization": "全球化",
    "attribution": "归因",
    "recycle": "回收站",
    "tech": "技术雷达",
    "faq": "FAQ",
    "onboarding": "新手引导",
    "channel": "渠道",
    "nurture": "培育",
    "interaction": "互动",
    "dashboard": "仪表盘",
    "factory": "工厂",
    "diagnosis": "诊断",
    "matrix": "矩阵",
    "setting": "设置",
    "usage": "用量",
    "generate": "生成",
    "template": "模板",
    "publish": "发布",
    "daily": "日报",
    "report": "报告",
    "video": "视频",
    "im": "IM",
    "perf": "性能",
    "config": "配置",
    "metro": "元数据",
    "recommend": "推荐",
    "session": "会话",
    "visitor": "访客",
    "geo": "GEO",
    "ab": "AB测试",
    "tree": "Agent树",
    "hub": "Hub",
    "super": "超级Agent",
    "learning": "学习",
    "marketplace": "市场",
    "commercial": "商业OS",
    "aitoearn": "AI赚",
    "intel": "情报",
    "egress": "出口",
    "tool": "工具",
    "unified": "统一发布",
    "ledger": "账本",
    "job": "任务",
    "search": "搜索",
}


def _resolve_domain_tag(filename: str) -> str:
    """根据文件名推断业务域标签。"""
    name = filename.lower().replace("_", " ")
    for prefix, tag in _DOMAIN_TAGS.items():
        if name.startswith(prefix):
            return tag
    return "通用"


def discover_routes(
    package_path: str = "app.api.v1.routes",
    skip_prefix: str = "_",
    exclude_modules: set[str] | None = None,
) -> list[APIRouter]:
    """自动发现路由模块。

    扫描 package_path 下的所有 .py 文件，导入 router 实例。

    Args:
        package_path: Python 包路径
        skip_prefix: 跳过以此前缀开头的文件
        exclude_modules: 排除的模块名集合（用于避免重复注册已手动导入的路由）

    Returns:
        router 实例列表
    """
    routers: list[APIRouter] = []
    exclude = exclude_modules or set()
    try:
        package = importlib.import_module(package_path)
        package_dir = Path(package.__file__).parent if package.__file__ else None
        if not package_dir:
            return routers

        for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
            # 跳过私有模块
            if module_name.startswith(skip_prefix):
                continue
            if module_name in ("auto_discovery",):
                continue
            if module_name in exclude:
                continue

            full_module = f"{package_path}.{module_name}"
            try:
                module = importlib.import_module(full_module)
                if hasattr(module, "router"):
                    router_instance = getattr(module, "router")
                    if isinstance(router_instance, APIRouter):
                        domain_tag = _resolve_domain_tag(module_name)
                        routers.append(router_instance)
                        log.debug("自动发现路由: %s → %s", full_module, domain_tag)
            except (ImportError, ModuleNotFoundError, Exception) as e:
                log.warning("跳过路由模块 %s: %s", full_module, e)

    except Exception as e:
        log.error("路由自动发现失败: %s", e)

    return routers


def auto_register_routes(
    parent_router: APIRouter,
    package_path: str = "app.api.v1.routes",
    exclude_modules: set[str] | None = None,
) -> int:
    """自动注册所有发现的路由。"""
    try:
        package = importlib.import_module(package_path)
    except ImportError as e:
        log.error("无法导入路由包 %s: %s", package_path, e)
        return 0

    package_dir = Path(package.__file__).parent
    exclude = exclude_modules or set()
    count = 0

    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name.startswith("_") or module_name in ("auto_discovery",) or module_name in exclude:
            continue

        full_module = f"{package_path}.{module_name}"
        try:
            module = importlib.import_module(full_module)
            if hasattr(module, "router"):
                router_instance = getattr(module, "router")
                if isinstance(router_instance, APIRouter):
                    # 读取注入的 prefix 和 tags
                    prefix = getattr(module, "ROUTE_PREFIX", f"/{module_name.replace('_', '-')}")
                    if prefix == "/":
                        prefix = ""
                    
                    tags = getattr(module, "ROUTE_TAGS", None)
                    if tags is None:
                        tags = [_resolve_domain_tag(module_name)]
                    
                    # 挂载路由
                    parent_router.include_router(
                        router_instance, 
                        prefix=prefix, 
                        tags=tags
                    )
                    count += 1
                    log.debug("自动挂载路由: %s (prefix=%s)", full_module, prefix)
        except Exception as e:
            log.warning("跳过路由模块 %s: %s", full_module, e)

    log.info("自动注册 %d 个路由模块", count)
    return count
    return count