# -*- coding: utf-8 -*-
"""六插槽注册表完整性测试（EXECUTOR = 优丁 CRM 原生直驱）。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.orchestration import SlotRegistry
from app.orchestration.executors.channel_frontend_adapter import ChannelFrontendAdapter
from app.orchestration.executors.data_source_enrich_adapter import DataSourceEnrichAdapter
from app.orchestration.executors.erp_gateway_adapter import ErpGatewayAdapter
from app.orchestration.executors.mcp_manifest_adapter import McpManifestAdapter
from app.orchestration.executors.native_crm_executor import NativeCrmExecutor
from app.orchestration.executors.skill_pack_source_adapter import SkillPackSourceAdapter
from app.orchestration.interfaces import SlotArchetype


def _registry() -> SlotRegistry:
    return SlotRegistry(
        [
            NativeCrmExecutor(),
            McpManifestAdapter(MagicMock(), tenant_id="tenant-1"),
            SkillPackSourceAdapter(),
            DataSourceEnrichAdapter(MagicMock()),
            ChannelFrontendAdapter(),
            ErpGatewayAdapter(MagicMock()),
        ]
    )


def test_registry_has_all_six_slots():
    slots = _registry().require_all_slots()
    assert set(slots) == set(SlotArchetype)
    assert len(slots) == 6


def test_registry_returns_adapter_by_archetype():
    registry = _registry()
    assert isinstance(registry.slot_adapter(SlotArchetype.EXECUTOR), NativeCrmExecutor)
    assert isinstance(registry.slot_adapter(SlotArchetype.ERP_BACKEND), ErpGatewayAdapter)


def test_empty_registry_reports_missing_slots_not_silent():
    with pytest.raises(RuntimeError) as exc_info:
        SlotRegistry().require_all_slots()
    assert "六插槽存在缺口" in str(exc_info.value)
    assert "executor" in str(exc_info.value)


def test_registry_rejects_object_outside_slots():
    with pytest.raises(TypeError):
        SlotRegistry([object()])
