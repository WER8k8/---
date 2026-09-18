# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes Executor Plugins Package.
Automatically imports and registers built-in executors.
"""
from .base import BaseExecutor, ExecutorContext, ExecutorRegistry

# Auto-import built-in executors to trigger ExecutorRegistry.register()
from . import accio_executor  # noqa: F401
from . import deerflow_executor  # noqa: F401
from . import trade_ai_agent_executor  # noqa: F401
from . import goodjob_crm_executor  # noqa: F401
# 业务链主干（2026-09-10）：建站 → 内容 → 分发 → 养号/egress
from . import site_builder_executor  # noqa: F401
from . import content_executor  # noqa: F401
from . import publish_executor  # noqa: F401
from . import nurture_executor  # noqa: F401
from . import egress_executor  # noqa: F401
# 业务链首批扩展（2026-09-11）：询盘 / 产品 / 物流
from . import inquiry_executor  # noqa: F401
from . import product_executor  # noqa: F401
from . import logistics_executor  # noqa: F401
# UBrain 统一助手执行器（2026-09-11 H.3）
from . import ubrain_executor  # noqa: F401
# 旺财贸易问答执行器（2026-09-11 H.5）
from . import wangcai_executor  # noqa: F401

# 业务链扩展（2026-09-11 E段/N段）：SEO / 拓客
from . import seo_executor  # noqa: F401
from . import lead_executor  # noqa: F401
from . import media_executor  # noqa: F401
from . import engagement_executor  # noqa: F401
from . import forum_executor  # noqa: F401
from . import research_executor  # noqa: F401
from . import order_executor  # noqa: F401
from . import browser_executor  # noqa: F401
from . import billing_executor  # noqa: F401
from . import ai_engine_executor  # noqa: F401
# 全量路由模块矩阵（串联率补齐 2026-09-18）
from . import module_matrix_executor  # noqa: F401
# 商业链深接（2026-09-18）
from . import commerce_ops_executor  # noqa: F401
from . import platform_ops_executor  # noqa: F401
from . import trade_ops_executor  # noqa: F401
from . import content_deep_executor  # noqa: F401
from . import outreach_loop_executor  # noqa: F401
from . import growth_probe_executor  # noqa: F401
from . import agent_ops_executor  # noqa: F401
from . import compliance_ops_executor  # noqa: F401
from . import portal_ops_executor  # noqa: F401
from . import data_ops_executor  # noqa: F401

__all__ = [
    "BaseExecutor",
    "ExecutorContext",
    "ExecutorRegistry",
]
