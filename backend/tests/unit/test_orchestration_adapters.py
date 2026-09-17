# -*- coding: utf-8 -*-
"""六插槽适配器契约测试（不连真实外部服务）。"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.orchestration.executors.channel_frontend_adapter import (
    INQUIRY_WRITE_ENDPOINT,
    ChannelFrontendAdapter,
)
from app.orchestration.executors.data_source_enrich_adapter import DataSourceEnrichAdapter
from app.orchestration.executors.erp_gateway_adapter import (
    ErpGatewayAdapter,
    OrderNotFoundError,
)
from app.orchestration.executors.mcp_manifest_adapter import McpManifestAdapter
from app.orchestration.executors.skill_pack_source_adapter import (
    SkillNotFoundError,
    SkillPackSourceAdapter,
)


def test_mcp_manifest_uses_tenant_isolated_service():
    db = MagicMock()
    servers = [{"name": "filesystem", "tools": []}]
    with patch(
        "app.orchestration.executors.mcp_manifest_adapter.McpService"
    ) as mock_service:
        mock_service.return_value.list_servers.return_value = servers
        manifest = McpManifestAdapter(db, tenant_id="tenant-1").manifest()

    mock_service.return_value.list_servers.assert_called_once_with(tenant_id="tenant-1")
    assert manifest == {"servers": servers}


def test_skill_source_returns_loaded_package():
    entry = SimpleNamespace(name="ai-seo", version="2.2.0")
    with (
        patch(
            "app.orchestration.executors.skill_pack_source_adapter.discover_skill_packs",
            return_value=[entry],
        ) as mock_discover,
        patch(
            "app.orchestration.executors.skill_pack_source_adapter.load_skill_body",
            return_value="# AI SEO",
        ) as mock_load,
    ):
        package = SkillPackSourceAdapter().fetch_skill_package("ai-seo")

    mock_discover.assert_called_once()
    mock_load.assert_called_once_with("ai-seo", None)
    assert package == {"skill_md": "# AI SEO", "version": "2.2.0", "license": "unspecified"}


def test_skill_source_missing_package_fails_explicitly():
    with patch(
        "app.orchestration.executors.skill_pack_source_adapter.discover_skill_packs",
        return_value=[],
    ):
        with pytest.raises(SkillNotFoundError):
            SkillPackSourceAdapter().fetch_skill_package("missing")


def test_skill_source_empty_ref_fails():
    with pytest.raises(ValueError):
        SkillPackSourceAdapter().fetch_skill_package("  ")


def test_data_source_calls_real_enrichment_service():
    service = MagicMock()

    async def enrich_lead(**kwargs):
        return {"found": True, "person": {"email": kwargs["email"]}}

    service.enrich_lead = enrich_lead
    result = DataSourceEnrichAdapter(service).enrich(
        "tenant-1", {"email": "buyer@example.com"}
    )

    assert result == {"found": True, "person": {"email": "buyer@example.com"}}


def test_data_source_requires_tenant():
    with pytest.raises(ValueError):
        DataSourceEnrichAdapter(MagicMock()).enrich(" ", {})


def test_data_source_requires_mapping_subject():
    with pytest.raises(ValueError):
        DataSourceEnrichAdapter(MagicMock()).enrich("tenant-1", [])


def test_channel_manifest_uses_existing_channel_status():
    channels = [
        SimpleNamespace(id="google", name="Google", status="real", reason="configured")
    ]
    with patch(
        "app.orchestration.executors.channel_frontend_adapter.get_all_channel_statuses",
        return_value=channels,
    ):
        manifest = ChannelFrontendAdapter().frontend_manifest()

    assert manifest["channels"] == [
        {"id": "google", "name": "Google", "status": "real", "reason": "configured"}
    ]
    assert manifest["inquiry_write_endpoint"] == INQUIRY_WRITE_ENDPOINT


def test_channel_write_endpoint_is_existing_public_api():
    assert INQUIRY_WRITE_ENDPOINT == "/api/v1/inquiries/public"


def test_channel_manifest_serializes_channel_dataclass():
    channels = [SimpleNamespace(id="x", name="X", status="mock", reason="demo")]
    with patch(
        "app.orchestration.executors.channel_frontend_adapter.get_all_channel_statuses",
        return_value=channels,
    ):
        manifest = ChannelFrontendAdapter().frontend_manifest()

    assert manifest["channels"] == [
        {"id": "x", "name": "X", "status": "mock", "reason": "demo"}
    ]


def _db_first(value):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = value
    return db


def test_erp_push_order_returns_existing_order_number():
    order = SimpleNamespace(order_number="ORD-123")
    adapter = ErpGatewayAdapter(_db_first(order))

    assert adapter.push_order("tenant-1", {"order_number": "ORD-123"}) == "ORD-123"


def test_erp_push_order_missing_order_fails():
    adapter = ErpGatewayAdapter(_db_first(None))

    with pytest.raises(OrderNotFoundError):
        adapter.push_order("tenant-1", {"order_number": "ORD-404"})


def test_erp_inventory_is_honestly_not_configured():
    result = ErpGatewayAdapter(MagicMock()).pull_inventory(
        "tenant-1", ("SKU-001",)
    )

    assert result["status"] == "not_configured"
    assert result["skus"] == ["SKU-001"]


def test_erp_fulfillment_reads_order_projection():
    order = SimpleNamespace(status="shipped", tracking_number="SF123")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = order
    result = ErpGatewayAdapter(db).pull_fulfillment_status(
        "tenant-1", ("ORD-123",)
    )

    assert result == {
        "items": [
            {
                "external_ref": "ORD-123",
                "status": "shipped",
                "tracking_number": "SF123",
            }
        ]
    }
