# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""领域模块注册中心 — FIX-31: 模块单体架构

架构原则：
- 每个领域（domain）是自包含的模块，拥有自己的 models、routes、services、schemas
- 领域间通过明确的接口（facade）通信，不直接导入对方的内部实现
- 共享内核（core/）提供通用基础设施（缓存、安全、配置等）
- 路由通过 auto_discovery 自动注册，无需手动导入

领域目录结构（以 lead 为例）：
  domains/
  ├── __init__.py          # 注册中心，导出所有领域
  ├── base.py              # 领域基类
  ├── lead/                # 获客引擎领域
  │   ├── __init__.py      # 导出领域 facade
  │   ├── models.py        # 领域数据模型
  │   ├── routes.py        # 领域 API 路由
  │   ├── services.py      # 领域业务逻辑
  │   └── schemas.py       # 领域 Pydantic schemas
  ├── auth/               # 认证授权领域
  ├── tenant/             # 租户管理领域
  ├── product/            # 产品管理领域
  ├── content/            # 内容管理领域
  ├── inquiry/            # 询盘管理领域
  ├── seo/                # SEO 优化领域
  ├── ai/                 # AI 智能领域
  ├── payment/            # 支付财务领域
  ├── system/             # 系统管理领域
  └── public/             # 公开 API 领域
"""

from app.domains.base import DomainModule

# 领域注册表 — 所有领域模块在此注册
DOMAIN_REGISTRY: dict[str, type[DomainModule]] = {}

# 已迁移的领域
from app.domains.lead import LeadDomain

DOMAIN_REGISTRY["lead"] = LeadDomain

# 待迁移的领域（stub）
# from app.domains.auth import AuthDomain
# DOMAIN_REGISTRY["auth"] = AuthDomain
# from app.domains.tenant import TenantDomain
# DOMAIN_REGISTRY["tenant"] = TenantDomain
# ...


def get_domain(name: str) -> DomainModule | None:
    """获取领域模块实例。"""
    cls = DOMAIN_REGISTRY.get(name)
    return cls() if cls else None


def list_domains() -> list[str]:
    """列出所有已注册的领域。"""
    return list(DOMAIN_REGISTRY.keys())