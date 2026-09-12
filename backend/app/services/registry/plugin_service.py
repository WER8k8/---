"""Plugin 注册表服务（轮17-4）。

plugins/plugin_versions 表持久化。Plugin 带 manifest（JSON 容器），版本化发布。
与 Skill 不同，Plugin 是更粗粒度的能力打包（§5.2.4/§A.3 对接 connector）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.registry import RegistryPlugin, RegistryPluginVersion, SKILL_STATUSES
from app.services.registry.common import ensure_in, into_json, valid_name
from app.services.registry.matrix import publish_transition


class PluginNotFoundError(Exception):
    """指定 plugin 不存在。"""


class PluginConflictError(Exception):
    """Plugin 唯一键冲突。"""


class PluginService:
    """Plugin 生命周期管理。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------- 查询
    def get(self, plugin_id: str) -> RegistryPlugin | None:
        return self.db.query(RegistryPlugin).filter(RegistryPlugin.id == plugin_id).first()

    def get_by_name(self, name: str, tenant_id: str | None = None) -> RegistryPlugin | None:
        q = self.db.query(RegistryPlugin).filter(RegistryPlugin.name == name)
        if tenant_id is not None:
            q = q.filter(RegistryPlugin.tenant_id == tenant_id)
        return q.first()

    def list_plugins(
        self, *, tenant_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        q = self.db.query(RegistryPlugin)
        if tenant_id is not None:
            q = q.filter(RegistryPlugin.tenant_id == tenant_id)
        if status:
            q = q.filter(RegistryPlugin.status == status)
        return [self._to_dict(p) for p in q.order_by(RegistryPlugin.created_at.desc()).all()]

    def list_versions(self, plugin_id: str) -> list[dict[str, Any]]:
        rows = (
            self.db.query(RegistryPluginVersion)
            .filter(RegistryPluginVersion.plugin_id == plugin_id)
            .order_by(RegistryPluginVersion.created_at.desc())
            .all()
        )
        return [self._version_to_dict(v) for v in rows]

    # ------------------------------------------------------------- 写入
    def register_plugin(
        self,
        *,
        name: str,
        manifest: dict | None = None,
        tenant_id: str | None = None,
        version: str = "1.0.0",
    ) -> RegistryPlugin:
        if not valid_name(name):
            raise ValueError(f"非法 plugin 名: {name!r}")
        if self.get_by_name(name, tenant_id):
            raise PluginConflictError(f"tenant={tenant_id} 已存在 plugin: {name}")
        plugin = RegistryPlugin(
            tenant_id=tenant_id,
            name=name,
            current_version=version,
            status="draft",
            manifest_json=into_json(manifest),
        )
        self.db.add(plugin)
        self.db.flush()
        self.db.add(
            RegistryPluginVersion(
                plugin_id=plugin.id,
                version=version,
                manifest_json=into_json(manifest),
                status="draft",
            )
        )
        self.db.commit()
        self.db.refresh(plugin)
        return plugin

    def create_version(self, plugin_id: str, *, version: str, manifest: dict | None) -> RegistryPluginVersion:
        plugin = self.get(plugin_id)
        if not plugin:
            raise PluginNotFoundError(plugin_id)
        existing = (
            self.db.query(RegistryPluginVersion)
            .filter(
                RegistryPluginVersion.plugin_id == plugin_id,
                RegistryPluginVersion.version == version,
            )
            .first()
        )
        if existing:
            raise PluginConflictError(f"plugin={plugin_id} 已存在版本 {version}")
        ver = RegistryPluginVersion(
            plugin_id=plugin_id,
            version=version,
            manifest_json=into_json(manifest),
            status="draft",
        )
        self.db.add(ver)
        plugin.current_version = version
        plugin.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(ver)
        return ver

    def set_publish_status(self, plugin_id: str, target: str) -> RegistryPlugin:
        plugin = self.get(plugin_id)
        if not plugin:
            raise PluginNotFoundError(plugin_id)
        ensure_in(target, SKILL_STATUSES, "status")
        if plugin.status == target:
            return plugin
        if not publish_transition(plugin.status, target):
            raise PluginConflictError(
                f"非法 Plugin 发布态跃迁: {plugin.status} -> {target}"
            )
        plugin.status = target
        self.db.query(RegistryPluginVersion).filter(
            RegistryPluginVersion.plugin_id == plugin_id,
            RegistryPluginVersion.version == plugin.current_version,
        ).update({"status": target})
        plugin.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(plugin)
        return plugin

    # ------------------------------------------------------------ 序列化
    def _to_dict(self, p: RegistryPlugin) -> dict[str, Any]:
        return {
            "id": str(p.id),
            "tenant_id": str(p.tenant_id) if p.tenant_id else None,
            "name": p.name,
            "current_version": p.current_version,
            "status": p.status,
            "manifest": p.manifest,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }

    def _version_to_dict(self, v: RegistryPluginVersion) -> dict[str, Any]:
        return {
            "id": str(v.id),
            "plugin_id": str(v.plugin_id),
            "version": v.version,
            "manifest": v.manifest,
            "status": v.status,
            "created_at": v.created_at,
        }


def build_plugin_service(db: Session) -> PluginService:
    """build_plugin_service。
    :param db: 会话。
    :return: PluginService 实例。
    """
    return PluginService(db)