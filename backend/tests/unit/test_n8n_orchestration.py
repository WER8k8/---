"""§12 n8n 编排引擎测试：注册表 + 内建工作流激活 + 触发器离线验证。

不依赖真实 n8n 服务，用 monkeypatch 替换 httpx 客户端，验证触发逻辑。
"""

from __future__ import annotations

import pytest


class TestWorkflowRegistry:
    def test_register_and_get(self):
        from app.services.n8n.workflow_registry import WorkflowRecord, get_workflow_registry

        registry = get_workflow_registry()
        reg = registry.register(WorkflowRecord(
            workflow_id="test_wf", name="test", endpoint="http://n8n.local/hook",
        ))
        try:
            assert registry.get("test_wf") is reg
            assert reg in registry.list_enabled()
        finally:
            registry.unregister("test_wf")

    def test_set_enabled(self):
        from app.services.n8n.workflow_registry import WorkflowRecord, get_workflow_registry

        registry = get_workflow_registry()
        registry.register(WorkflowRecord(workflow_id="enb", name="e", endpoint="http://n8n.local/e", enabled=False))
        try:
            # 未启用时 enb 不在 list_enabled 里
            assert all(w.workflow_id != "enb" for w in registry.list_enabled())
            registry.set_enabled("enb", True)
            assert any(w.workflow_id == "enb" for w in registry.list_enabled())
        finally:
            registry.unregister("enb")


class TestBuiltinActivation:
    def test_site_built_defaults_enabled_in_dev_when_endpoint_set(self, monkeypatch):
        """§12：dev 环境 + 配了 webhook 未显式禁用 → 内建工作流应默认 enabled。"""
        from app.services.n8n import workflow_registry as wr

        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("N8N_SITE_BUILT_WEBHOOK_URL", "http://n8n.local/webhook/sb")
        monkeypatch.delenv("N8N_SITE_BUILT_ENABLED", raising=False)

        registry = wr.WorkflowRegistry.get_instance()
        # 幂等注册
        registry.unregister("site_built_notify")
        wr.ensure_builtin_workflows()
        rec = registry.get("site_built_notify")
        assert rec is not None
        assert rec.enabled is True
        assert rec.endpoint == "http://n8n.local/webhook/sb"

    def test_produce_no_endpoint_means_disabled(self, monkeypatch):
        """没配 webhook 时，即使 dev 也不应激活（避免误触不存在的端点）。"""
        from app.services.n8n import workflow_registry as wr

        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("N8N_SITE_BUILT_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("N8N_SITE_BUILT_ENABLED", raising=False)

        registry = wr.WorkflowRegistry.get_instance()
        registry.unregister("site_built_notify")
        wr.ensure_builtin_workflows()
        rec = registry.get("site_built_notify")
        assert rec is not None
        assert rec.enabled is False


class TestN8nTrigger:
    def test_trigger_success(self, monkeypatch):
        from app.services.n8n.trigger import N8nTriggerService
        from app.services.n8n.workflow_registry import WorkflowRecord, get_workflow_registry

        registry = get_workflow_registry()
        registry.register(WorkflowRecord(
            workflow_id="ok_wf", name="ok", endpoint="http://n8n.local/hook", enabled=True,
        ))
        try:
            fake = _FakeHttpx()
            fake.responses = [
                _FakeResponse(200, b'{"ok": true}'),
            ]
            monkeypatch.setattr("app.services.n8n.trigger.httpx.AsyncClient", lambda *a, **k: fake)
            service = N8nTriggerService()
            import asyncio
            result = asyncio.run(service.trigger("ok_wf", {"x": 1}))
            assert result["success"] is True
            assert result["status_code"] == 200
        finally:
            registry.unregister("ok_wf")

    def test_trigger_unregistered_raises(self):
        from app.services.n8n.trigger import N8nTriggerService
        import asyncio
        service = N8nTriggerService()
        with pytest.raises(ValueError):
            asyncio.run(service.trigger("never_registered", {}))

    def test_trigger_disabled_raises(self):
        from app.services.n8n.trigger import N8nTriggerService
        from app.services.n8n.workflow_registry import WorkflowRecord, get_workflow_registry

        registry = get_workflow_registry()
        registry.register(WorkflowRecord(
            workflow_id="off_wf", name="off", endpoint="http://n8n.local/hook", enabled=False,
        ))
        try:
            service = N8nTriggerService()
            import asyncio
            with pytest.raises(ValueError):
                asyncio.run(service.trigger("off_wf", {}))
        finally:
            registry.unregister("off_wf")


class _FakeResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        import json as _json
        return _json.loads(self.content)


class _FakeHttpx:
    """模拟 httpx.AsyncClient 上下文。"""
    responses = None

    def __init__(self, *a, **k):
        self._k = k

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, *a, **k):
        return self.responses.pop(0)
