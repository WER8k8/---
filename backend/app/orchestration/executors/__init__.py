# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""六插槽契约的适配器目录。

EXECUTOR 插槽 = 优丁 CRM 原生直驱（`native_crm_executor`），无外桥。
"""

from app.orchestration.executors.channel_frontend_adapter import ChannelFrontendAdapter
from app.orchestration.executors.data_source_enrich_adapter import DataSourceEnrichAdapter
from app.orchestration.executors.erp_gateway_adapter import ErpGatewayAdapter
from app.orchestration.executors.mcp_manifest_adapter import McpManifestAdapter
from app.orchestration.executors.native_crm_executor import (
    GoodJobExecutor,
    NativeCrmExecutor,
    build_native_crm_executor,
)
from app.orchestration.executors.skill_pack_source_adapter import SkillPackSourceAdapter

__all__ = [
    "ChannelFrontendAdapter",
    "DataSourceEnrichAdapter",
    "ErpGatewayAdapter",
    "NativeCrmExecutor",
    "GoodJobExecutor",
    "build_native_crm_executor",
    "McpManifestAdapter",
    "SkillPackSourceAdapter",
]

