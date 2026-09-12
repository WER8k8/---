"""租户能力开关（轮17-7）。

tenant_capability_toggles：按租户 × 能力类型 × 能力实例 显式启用/停用。
默认 enabled=False，必须显式启用（最小权限原则）。能力类型示例：
skill/mcp/plugin/data_source。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.registry import TenantCapabilityToggle

CAPABILITY_TYPES = ("skill", "mcp", "plugin", "data_source")


class TenantToggleService:
    """租户能力开关管理。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def is_enabled(self, tenant_id: str, capability_type: str, capability_id: str) -> bool:
        """查询某租户某能力是否已启用（默认 False）。"""
        row = self.db.query(TenantCapabilityToggle).get(
            (tenant_id, capability_type, capability_id)
        )
        return bool(row and row.enabled)

    def set_enabled(
        self,
        tenant_id: str,
        capability_type: str,
        capability_id: str,
        enabled: bool,
    ) -> TenantCapabilityToggle:
        if capability_type not in CAPABILITY_TYPES:
            raise ValueError(
                f"capability_type 非法: {capability_type!r}（允许: {list(CAPABILITY_TYPES)}）"
            )
        row = self.db.query(TenantCapabilityToggle).get(
            (tenant_id, capability_type, capability_id)
        )
        if row:
            row.enabled = enabled
            self.db.commit()
            self.db.refresh(row)
            return row
        row = TenantCapabilityToggle(
            tenant_id=tenant_id,
            capability_type=capability_type,
            capability_id=capability_id,
            enabled=enabled,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_for(
        self, tenant_id: str, capability_type: str | None = None
    ) -> list[dict[str, Any]]:
        q = self.db.query(TenantCapabilityToggle).filter(
            TenantCapabilityToggle.tenant_id == tenant_id
        )
        if capability_type:
            q = q.filter(TenantCapabilityToggle.capability_type == capability_type)
        return [
            {
                "tenant_id": str(r.tenant_id),
                "capability_type": r.capability_type,
                "capability_id": r.capability_id,
                "enabled": r.enabled,
                "updated_at": r.updated_at,
            }
            for r in q.all()
        ]


def build_tenant_toggle_service(db: Session) -> TenantToggleService:
    """build_tenant_toggle_service。
    :param db: 会话。
    :return: 服务实例。
    """
    return TenantToggleService(db)