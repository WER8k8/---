"""MCP_TOOL 插槽适配器：读取租户隔离的已注册 MCP 清单。"""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.orchestration.interfaces import McpToolProvider, SlotArchetype
from app.services.registry.mcp_service import McpService


class McpManifestAdapter(McpToolProvider):
    """以现有 McpService 为唯一数据源，不新增连接器状态。"""

    archetype = SlotArchetype.MCP_TOOL

    def __init__(self, db: Session, tenant_id: str | None = None) -> None:
        self.tenant_id = tenant_id
        self._service = McpService(db)

    def manifest(self) -> Mapping[str, Any]:
        return {"servers": self._service.list_servers(tenant_id=self.tenant_id)}


__all__ = ["McpManifestAdapter"]
