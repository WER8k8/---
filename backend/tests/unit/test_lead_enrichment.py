"""LeadEnrichmentService 单元测试。"""
import os
import pytest
from unittest.mock import AsyncMock, patch

from app.services.lead_enrichment import LeadEnrichmentService


@pytest.fixture
def service():
    return LeadEnrichmentService()


@pytest.mark.asyncio
async def test_enrich_no_api_keys_returns_skipped(service, monkeypatch):
    """无 API key 时返回 enrichment_status=skipped。"""
    monkeypatch.delenv("HUNTER_IO_API_KEY", raising=False)
    monkeypatch.delenv("LINKEDIN_API_KEY", raising=False)

    lead = {"email": "test@example.com", "company_name": "Acme"}
    result = await service.enrich(lead)

    assert result["enrichment_status"] == "skipped"
    assert "无任何数据源 API key" in result["enrichment_error"]
    assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_enrich_empty_email_returns_failed(service, monkeypatch):
    """email 为空时返回 failed。"""
    monkeypatch.delenv("HUNTER_IO_API_KEY", raising=False)
    monkeypatch.delenv("LINKEDIN_API_KEY", raising=False)

    lead = {"email": "", "company_name": "Acme"}
    result = await service.enrich(lead)

    assert result["enrichment_status"] == "failed"
    assert "email 为空" in result["enrichment_error"]


@pytest.mark.asyncio
async def test_enrich_with_hunter_key_calls_api(service, monkeypatch):
    """有 Hunter key 时调用 API 并返回 enriched。"""
    monkeypatch.setenv("HUNTER_IO_API_KEY", "test_key")
    monkeypatch.delenv("LINKEDIN_API_KEY", raising=False)

    mock_resp_data = {"data": {"result": "deliverable", "score": 95, "regexp": True, "gibberish": False, "disposable": False, "webmail": False}}

    class FakeResp:
        def json(self): return mock_resp_data
        def raise_for_status(self): pass

    class FakeClient:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, *a, **kw): return FakeResp()

    with patch("app.services.lead_enrichment.httpx.AsyncClient", FakeClient):
        lead = {"email": "test@example.com"}
        result = await service.enrich(lead)

    assert result["enrichment_status"] == "enriched"
    assert "hunter_io" in result["enrichment_sources"]
    assert result["email_verification"]["result"] == "deliverable"


@pytest.mark.asyncio
async def test_enrich_batch_processes_multiple(service, monkeypatch):
    """批量富化处理多条线索。"""
    monkeypatch.delenv("HUNTER_IO_API_KEY", raising=False)
    monkeypatch.delenv("LINKEDIN_API_KEY", raising=False)

    leads = [
        {"email": "a@example.com"},
        {"email": "b@example.com"},
    ]
    results = await service.enrich_batch(leads)

    assert len(results) == 2
    assert all(r["enrichment_status"] == "skipped" for r in results)
