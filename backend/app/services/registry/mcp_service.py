"""MCP 注册表服务（轮17-3；轮19 扩展 connector-manifest 字段）。

替代 agent_hub_service 的进程内 _custom_mcp_servers 列表，改为 083
mcp_servers/mcp_tools 表持久化。工具权限精确到 read/write/execute/delete/
publish（默认 NO ACCESS = none）；新增工具默认 disabled，必须显式启用。
健康状态由调用方 probe 后回写 last_health_at。

轮19（083.2）：register_server 支持 GoodJob integration-sdk
ConnectorManifest 对齐字段（stage/driver/approved_hosts/allowed_ports/
allow_insecure_loopback/authentication/oauth/credential_fields/max_tools/
manifest_hash），校验规则镜像 manifest 的关键红线；manifest_hash 为 UJ 侧
规范化 JSON 的 sha256（显式传入优先，供跨系统对账）。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.registry import (
    MCP_AUTHENTICATIONS,
    MCP_CONNECTOR_DRIVERS,
    MCP_SERVER_STAGES,
    MCP_TOOL_PERMISSIONS,
    McpServer,
    McpTool,
)
from app.services.registry.common import ensure_in, into_json, parse_json, valid_name


class McpNotFoundError(Exception):
    """指定 MCP server/tool 不存在。"""


class McpConflictError(Exception):
    """MCP server/tool 唯一键冲突。"""


def _canonical_json(value: Any) -> str:
    """规范化 JSON：键递归排序、无空白（镜像 GoodJob canonicalJson 形态）。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _compute_manifest_hash(
    *,
    stage: str,
    driver: str | None,
    endpoint: str | None,
    approved_hosts: list[str] | None,
    allowed_ports: list[int] | None,
    allow_insecure_loopback: bool,
    authentication: str,
    oauth: dict | None,
    credential_fields: list[dict] | None,
    max_tools: int,
) -> str:
    payload = {
        "schema_version": "1.0",
        "stage": stage,
        "driver": driver,
        "endpoint": endpoint,
        "approved_hosts": approved_hosts or [],
        "allowed_ports": allowed_ports or [],
        "allow_insecure_loopback": allow_insecure_loopback,
        "authentication": authentication,
        "oauth": oauth,
        "credential_fields": credential_fields,
        "max_tools": max_tools,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_manifest_fields(
    *,
    stage: str,
    driver: str | None,
    endpoint: str | None,
    approved_hosts: list[str] | None,
    allowed_ports: list[int] | None,
    allow_insecure_loopback: bool,
    authentication: str,
    oauth: dict | None,
    credential_fields: list[dict] | None,
    max_tools: int,
) -> None:
    """ConnectorManifest 关键红线校验（镜像 integration-sdk 语义， ValueError）。"""
    ensure_in(stage, MCP_SERVER_STAGES, "stage")
    ensure_in(authentication, MCP_AUTHENTICATIONS, "authentication")
    if driver is not None:
        ensure_in(driver, MCP_CONNECTOR_DRIVERS, "driver")
    if not isinstance(max_tools, int) or not (1 <= max_tools <= 200):
        raise ValueError(f"max_tools 必须在 1-200 之间: {max_tools!r}")
    if approved_hosts is not None:
        if not isinstance(approved_hosts, list) or len(approved_hosts) > 20:
            raise ValueError("approved_hosts 必须是不超过 20 项的字符串列表")
        for host in approved_hosts:
            if not isinstance(host, str) or not host or "*" in host:
                raise ValueError(f"approved_hosts 含非法主机名: {host!r}（不允许通配符）")
    if allowed_ports is not None:
        if (
            not isinstance(allowed_ports, list)
            or not (1 <= len(allowed_ports) <= 10)
            or len(set(allowed_ports)) != len(allowed_ports)
            or any(not isinstance(p, int) or not (1 <= p <= 65535) for p in allowed_ports)
        ):
            raise ValueError("allowed_ports 必须是 1-65535 的不重复整数列表（≤10 项）")
    if stage == "planned" and (endpoint or driver or oauth or credential_fields):
        raise ValueError("planned 阶段不能携带运行配置（endpoint/driver/oauth/credential_fields）")
    if authentication == "none" and (oauth is not None or credential_fields is not None):
        raise ValueError("authentication=none 时不能提供 oauth/credential_fields")
    if authentication == "oauth2" and oauth is None:
        raise ValueError("authentication=oauth2 必须提供 oauth 配置")
    if authentication == "api_token":
        if not isinstance(credential_fields, list) or not (1 <= len(credential_fields) <= 8):
            raise ValueError("authentication=api_token 必须声明 1-8 个凭据字段")
        keys = [f.get("key") for f in credential_fields if isinstance(f, dict)]
        if len(keys) != len(credential_fields) or len(set(keys)) != len(keys):
            raise ValueError("credential_fields.key 缺失或重复")


class McpService:
    """MCP 服务注册与工具权限管理。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------- 查询
    def get_server(self, server_id: str) -> McpServer | None:
        return self.db.query(McpServer).filter(McpServer.id == server_id).first()

    def get_server_by_name(self, name: str, tenant_id: str | None = None) -> McpServer | None:
        q = self.db.query(McpServer).filter(McpServer.name == name)
        if tenant_id is not None:
            q = q.filter(McpServer.tenant_id == tenant_id)
        return q.first()

    def list_servers(
        self, *, tenant_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        q = self.db.query(McpServer)
        if tenant_id is not None:
            q = q.filter(McpServer.tenant_id == tenant_id)
        if status:
            q = q.filter(McpServer.status == status)
        rows = q.order_by(McpServer.created_at.desc()).all()
        out = []
        for s in rows:
            d = self._server_to_dict(s)
            d["tools"] = self._list_tools_for(s.id, enabled_only=False)
            out.append(d)
        return out

    def list_tools(self, server_id: str, *, enabled_only: bool = True) -> list[dict[str, Any]]:
        return self._list_tools_for(server_id, enabled_only=enabled_only)

    def _list_tools_for(self, server_id: str, *, enabled_only: bool) -> list[dict[str, Any]]:
        q = self.db.query(McpTool).filter(McpTool.server_id == server_id)
        if enabled_only:
            q = q.filter(McpTool.enabled.is_(True))
        return [self._tool_to_dict(t) for t in q.order_by(McpTool.name).all()]

    # ------------------------------------------------------------- 写入
    def register_server(
        self,
        *,
        name: str,
        endpoint: str | None = None,
        protocol: str | None = None,
        credential_vault_ref: str | None = None,
        tenant_id: str | None = None,
        status: str = "disabled",
        stage: str | None = None,
        driver: str | None = None,
        approved_hosts: list[str] | None = None,
        allowed_ports: list[int] | None = None,
        allow_insecure_loopback: bool = False,
        authentication: str = "none",
        oauth: dict | None = None,
        credential_fields: list[dict] | None = None,
        max_tools: int = 200,
        manifest_hash: str | None = None,
    ) -> McpServer:
        if not valid_name(name):
            raise ValueError(f"非法 MCP server 名: {name!r}")
        if self.get_server_by_name(name, tenant_id):
            raise McpConflictError(f"tenant={tenant_id} 已存在 MCP server: {name}")
        # 轮20：vault 引用格式红线（明文密钥禁止入库，必须走 vault://credential/<id>）
        if credential_vault_ref is not None:
            _prefix = "vault://credential/"
            if not credential_vault_ref.startswith(_prefix) or len(credential_vault_ref) <= len(_prefix):
                raise ValueError(
                    f"非法 credential_vault_ref: {credential_vault_ref!r}（必须为 {_prefix}<id>，"
                    "密钥明文禁止入库）"
                )
        # stage 缺省推导：带 endpoint 视为 available，否则 planned（镜像 manifest 默认）
        resolved_stage = stage or ("available" if endpoint else "planned")
        hosts = [h.lower() for h in approved_hosts] if approved_hosts else approved_hosts
        _validate_manifest_fields(
            stage=resolved_stage,
            driver=driver,
            endpoint=endpoint,
            approved_hosts=hosts,
            allowed_ports=allowed_ports,
            allow_insecure_loopback=allow_insecure_loopback,
            authentication=authentication,
            oauth=oauth,
            credential_fields=credential_fields,
            max_tools=max_tools,
        )
        server = McpServer(
            tenant_id=tenant_id,
            name=name,
            endpoint=endpoint,
            protocol=protocol,
            credential_vault_ref=credential_vault_ref,
            status=status,
            stage=resolved_stage,
            driver=driver,
            approved_hosts_json=into_json(hosts),
            allowed_ports_json=into_json(allowed_ports),
            allow_insecure_loopback=allow_insecure_loopback,
            authentication=authentication,
            oauth_json=into_json(oauth),
            credential_fields_json=into_json(credential_fields),
            max_tools=max_tools,
            manifest_hash=manifest_hash
            or _compute_manifest_hash(
                stage=resolved_stage,
                driver=driver,
                endpoint=endpoint,
                approved_hosts=hosts,
                allowed_ports=allowed_ports,
                allow_insecure_loopback=allow_insecure_loopback,
                authentication=authentication,
                oauth=oauth,
                credential_fields=credential_fields,
                max_tools=max_tools,
            ),
        )
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def register_tool(
        self,
        server_id: str,
        *,
        name: str,
        input_schema: dict | None = None,
        permission: str = "none",
        enabled: bool = False,
    ) -> McpTool:
        server = self.get_server(server_id)
        if not server:
            raise McpNotFoundError(server_id)
        if not valid_name(name):
            raise ValueError(f"非法 tool 名: {name!r}")
        ensure_in(permission, MCP_TOOL_PERMISSIONS, "permission")
        existing = (
            self.db.query(McpTool)
            .filter(McpTool.server_id == server_id, McpTool.name == name)
            .first()
        )
        if existing:
            raise McpConflictError(f"server={server_id} 已存在 tool: {name}")
        tool = McpTool(
            server_id=server_id,
            name=name,
            input_schema_json=into_json(input_schema),
            permission=permission,
            enabled=enabled,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def set_tool_permission(self, tool_id: str, permission: str) -> McpTool:
        tool = self.db.query(McpTool).filter(McpTool.id == tool_id).first()
        if not tool:
            raise McpNotFoundError(tool_id)
        ensure_in(permission, MCP_TOOL_PERMISSIONS, "permission")
        tool.permission = permission
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def set_tool_enabled(self, tool_id: str, enabled: bool) -> McpTool:
        tool = self.db.query(McpTool).filter(McpTool.id == tool_id).first()
        if not tool:
            raise McpNotFoundError(tool_id)
        tool.enabled = enabled
        self.db.commit()
        self.db.refresh(tool)
        return tool

    def set_server_status(self, server_id: str, status: str) -> McpServer:
        server = self.get_server(server_id)
        if not server:
            raise McpNotFoundError(server_id)
        server.status = status
        server.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(server)
        return server

    def mark_health(self, server_id: str, *, healthy: bool) -> McpServer:
        server = self.get_server(server_id)
        if not server:
            raise McpNotFoundError(server_id)
        server.last_health_at = datetime.now(timezone.utc)
        if healthy and server.status != "enabled":
            server.status = "enabled"
        self.db.commit()
        self.db.refresh(server)
        return server

    # ------------------------------------------------------------ 序列化
    def _server_to_dict(self, s: McpServer) -> dict[str, Any]:
        return {
            "id": str(s.id),
            "tenant_id": str(s.tenant_id) if s.tenant_id else None,
            "name": s.name,
            "endpoint": s.endpoint,
            "protocol": s.protocol,
            "credential_vault_ref": s.credential_vault_ref,
            "status": s.status,
            "last_health_at": s.last_health_at,
            "stage": s.stage,
            "driver": s.driver,
            "approved_hosts": parse_json(s.approved_hosts_json, []),
            "allowed_ports": parse_json(s.allowed_ports_json, []),
            "allow_insecure_loopback": s.allow_insecure_loopback,
            "authentication": s.authentication,
            "oauth": parse_json(s.oauth_json),
            "credential_fields": parse_json(s.credential_fields_json),
            "max_tools": s.max_tools,
            "manifest_hash": s.manifest_hash,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }

    def _tool_to_dict(self, t: McpTool) -> dict[str, Any]:
        return {
            "id": str(t.id),
            "server_id": str(t.server_id),
            "name": t.name,
            "input_schema": t.input_schema,
            "permission": t.permission,
            "enabled": t.enabled,
            "created_at": t.created_at,
        }


def build_mcp_service(db: Session) -> McpService:
    """build_mcp_service。
    :param db: 会话。
    :return: McpService 实例。
    """
    return McpService(db)