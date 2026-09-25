# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""获客引擎领域 — FIX-31: 首个完整领域模块迁移

包揽所有获客相关功能：
- 零成本邮箱验证（MX + SMTP）
- 网站邮箱抓取
- 邮件发送（Resend + SMTP）
- 线索管理（ProspectLead + 去重）
- 邮件外展（状态机 + 序列）
- 异步搜索

W1 · P0-3 收敛说明（2026-09-25）：
- 原 ``app/domains/lead/routes.py`` 定义的 ``/lead/*`` 路由**从未被挂载**
  （``register_routes()`` 只扫 ``api/v1/routes`` + ``api/v1`` 顶层，不扫 ``domains/``），
  对外实为 404；且其构造签名与 ``LeadSearchTask`` 真实 API 不符、缺 ``to_dict()``。
- 该文件已**归档**（移动，非删除），路径见交付说明；获客的**唯一入口**为
  ``app/api/v1/routes/lead_generation.py``（``/api/v1/lead-generation/*``）。
- 此处保留一个空领域路由占位，保证 ``DOMAIN_REGISTRY`` → ``LeadDomain.get_facade()``
  （``GET /api/v1/domains``）仍能正常返回领域元数据。
"""

from fastapi import APIRouter

from app.domains.base import DomainModule

# 空路由占位（不再对外暴露 /lead/*；真实入口见 lead_generation 路由）
_lead_facade_router = APIRouter()


class LeadDomain(DomainModule):
    """获客引擎领域模块。

    对外契约（W1 收敛后）指向 ``/api/v1/lead-generation/*``：
    - POST /lead-generation/search          - 搜索潜在客户（含落库）
    - POST /lead-generation/search-async    - 异步搜索
    - GET  /lead-generation/task/{task_id}  - 任务进度
    - GET  /lead-generation/verify-email    - 验证邮箱
    """
    name = "lead"
    label = "获客引擎"

    @property
    def router(self):
        """返回领域路由占位（不再挂载 /lead/*）。"""
        return _lead_facade_router


__all__ = ["LeadDomain"]
