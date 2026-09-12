"""租户 Hermes 插件安装 / 启用。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.hermes_plugin import HermesPluginInstall
from app.services.hermes.registry import DEFAULT_TENANT_PLUGIN_IDS, get_plugin


def list_tenant_installs(db: Session, tenant_id: str) -> list[HermesPluginInstall]:
    """list_tenant_installs。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    return (
        db.query(HermesPluginInstall)
        .filter(HermesPluginInstall.tenant_id == tenant_id)
        .order_by(HermesPluginInstall.installed_at.desc())
        .all()
    )


def is_plugin_enabled(db: Session, tenant_id: str, plugin_id: str) -> bool:
    """is_plugin_enabled。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param plugin_id: 参数 plugin_id
    :return: 返回处理结果。
    """
    row = (
        db.query(HermesPluginInstall)
        .filter(
            HermesPluginInstall.tenant_id == tenant_id,
            HermesPluginInstall.plugin_id == plugin_id,
        )
        .first()
    )
    if row is None:
        return plugin_id in DEFAULT_TENANT_PLUGIN_IDS
    return bool(row.enabled)


def install_plugin(
    db: Session,
    *,
    tenant_id: str,
    plugin_id: str,
    user_id: str | None = None,
    config: dict[str, Any] | None = None,
    enabled: bool = True,
) -> HermesPluginInstall:
    """install_plugin。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param plugin_id: 参数 plugin_id
    :param user_id: 参数 user_id
    :param config: 参数 config
    :param enabled: 参数 enabled
    :return: 返回处理结果。
    """
    spec = get_plugin(plugin_id)
    if not spec:
        raise ValueError("unknown_plugin")
    if spec.get("visibility") == "internal":
        raise ValueError("internal_plugin_not_installable")

    row = (
        db.query(HermesPluginInstall)
        .filter(
            HermesPluginInstall.tenant_id == tenant_id,
            HermesPluginInstall.plugin_id == plugin_id,
        )
        .first()
    )
    if row is None:
        row = HermesPluginInstall(
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            plugin_version=str(spec.get("version") or "1.0.0"),
            enabled=enabled,
            config_json=json.dumps(config or {}, ensure_ascii=False),
            installed_by=user_id,
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.plugin_version = str(spec.get("version") or row.plugin_version)
        if config is not None:
            row.config_json = json.dumps(config, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    return row


def set_plugin_enabled(
    db: Session,
    *,
    tenant_id: str,
    plugin_id: str,
    enabled: bool,
) -> HermesPluginInstall:
    """set_plugin_enabled。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param plugin_id: 参数 plugin_id
    :param enabled: 参数 enabled
    :return: 返回处理结果。
    """
    row = (
        db.query(HermesPluginInstall)
        .filter(
            HermesPluginInstall.tenant_id == tenant_id,
            HermesPluginInstall.plugin_id == plugin_id,
        )
        .first()
    )
    if row is None:
        return install_plugin(db, tenant_id=tenant_id, plugin_id=plugin_id, enabled=enabled)
    row.enabled = enabled
    db.commit()
    db.refresh(row)
    return row


def ensure_default_plugins(db: Session, tenant_id: str, user_id: str | None = None) -> int:
    """首次进入市场时写入默认包。"""
    existing = {r.plugin_id for r in list_tenant_installs(db, tenant_id)}
    added = 0
    for pid in DEFAULT_TENANT_PLUGIN_IDS:
        if pid in existing:
            continue
        try:
            install_plugin(db, tenant_id=tenant_id, plugin_id=pid, user_id=user_id)
            added += 1
        except ValueError:
            continue
    return added
