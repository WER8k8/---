# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""能力注册表持久化模型（总纲 §4.6-4 / §5.2.4 / §8；迁移 083）。

替代 agent_hub_service 进程内内存 list，使 Skill/MCP/Plugin/数据源
具备持久化、版本化、发布门禁与租户能力开关。字段对齐：
- skills：GoodJob manifest（triggers/keywords/modules/tool_refs/source_type/license）
  + Trade AI BaseSkill（config_schema/default_config/permissions）；
- skill_versions：Trade AI BaseSkill input/output schema + Canary 发布门禁痕迹；
- mcp_servers/mcp_tools：MCP 服务与工具，权限精确到 r/w/e/d/publish（默认 NO ACCESS）；
- plugins/plugin_versions：插件与版本 manifest；
- data_source_providers：数据源合规评审清单（§5.2.4）；裁决权归 Policy Engine；
- tenant_capability_toggles：租户战争apuability 开关（默认关闭，必须显式启用）。

命名规范：类名前缀 Registry/Mcp 以避免与 evolution.py 的 SkillVersion 冲突。
"""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import UUID_TYPE, Base

SKILL_STATUSES = ("draft", "testing", "active", "disabled", "rollback")
MCP_TOOL_PERMISSIONS = ("read", "write", "execute", "delete", "publish", "none")
DATA_CLASSES = ("public_corporate", "personal_contact")
LICENSE_BASIS = ("official_api", "licensed_service", "scraping")
REVIEW_STATUSES = ("pending", "approved", "rejected")

# 083.2（轮19）：mcp_servers 对齐 GoodJob integration-sdk ConnectorManifest
MCP_SERVER_STAGES = ("planned", "available")
MCP_AUTHENTICATIONS = ("none", "oauth2", "api_token")
MCP_CONNECTOR_DRIVERS = (
    "native_mcp",
    "microsoft_graph",
    "google_workspace",
    "google_drive",
    "erpnext",
    "easypost",
    "wecom",
)

# Trade AI BaseSkill 运行态（区别于 skills.status 发布态）
RUN_STATUSES = ("pending", "running", "success", "failed", "skipped")


def _utcnow() -> datetime:
    """_utcnow。
    :return: 返回当前 UTC 时间。
    """
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    """_new_uuid。
    :return: 返回新 UUID 字符串。
    """
    return str(uuid.uuid4())


def _loads(value: str | None, default=None):
    """JSON 文本安全解析；非法或空返回 default。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def _dumps(value) -> str | None:
    """序列化为 JSON 文本；None 返回 None。"""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


class RegistrySkill(Base):
    __tablename__ = "skills"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    display_name = Column(String(200), nullable=True)
    category = Column(String(60), nullable=True, index=True)
    description = Column(Text, nullable=True)
    current_version = Column(String(40), nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    # 轮18 083.1：运行字段（对齐 BaseSkill + GoodJob skill.json 缺口）
    priority = Column(Integer, nullable=False, default=50)
    timeout = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    retry_delay = Column(Integer, nullable=False, default=0)
    # GoodJob manifest 规范
    triggers_json = Column(Text, nullable=True)
    keywords_json = Column(Text, nullable=True)
    modules_json = Column(Text, nullable=True)
    tool_refs_json = Column(Text, nullable=True)
    source_type = Column(String(30), nullable=False, default="builtin")
    license = Column(String(120), nullable=True)
    # Trade AI BaseSkill 契约
    config_schema_json = Column(Text, nullable=True)
    default_config_json = Column(Text, nullable=True)
    permissions_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="ix_skills_tenant_name"),
        CheckConstraint(
            "status IN ({})".format(
                ", ".join(f"'{s}'" for s in SKILL_STATUSES)
            ),
            name="ck_skills_status",
        ),
    )

    @property
    def triggers(self) -> list:
        """triggers。
        :return: 触发词列表。
        """
        return _loads(self.triggers_json, default=[]) or []

    @property
    def keywords(self) -> list:
        """keywords。
        :return: 关键词列表。
        """
        return _loads(self.keywords_json, default=[]) or []

    @property
    def modules(self) -> list:
        """modules。
        :return: 模块引用列表。
        """
        return _loads(self.modules_json, default=[]) or []

    @property
    def tool_refs(self) -> list:
        """tool_refs。
        :return: 工具引用列表。
        """
        return _loads(self.tool_refs_json, default=[]) or []

    @property
    def config_schema(self):
        """config_schema。
        :return: 配置 schema。
        """
        return _loads(self.config_schema_json)

    @property
    def default_config(self):
        """default_config。
        :return: 默认配置。
        """
        return _loads(self.default_config_json, default={}) or {}

    @property
    def permissions(self):
        """permissions。
        :return: 权限声明。
        """
        return _loads(self.permissions_json, default={}) or {}


class RegistrySkillVersion(Base):
    __tablename__ = "skill_versions"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    skill_id = Column(UUID_TYPE, ForeignKey("skills.id"), nullable=False, index=True)
    version = Column(String(40), nullable=False)
    implementation_type = Column(String(20), nullable=False, default="prompt")
    implementation_json = Column(Text, nullable=True)
    input_schema_json = Column(Text, nullable=True)
    output_schema_json = Column(Text, nullable=True)
    tool_refs_json = Column(Text, nullable=True)  # 轮18 083.1：版本级工具绑定（Array-of-String）
    validators_json = Column(Text, nullable=True)
    examples_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    canary_percent = Column(Integer, nullable=False, default=0)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("skill_id", "version", name="uq_skill_versions_skill_version"),
    )

    @property
    def input_schema(self):
        """input_schema。
        :return: 输入 schema。
        """
        return _loads(self.input_schema_json)

    @property
    def output_schema(self):
        """output_schema。
        :return: 输出 schema。
        """
        return _loads(self.output_schema_json)

    @property
    def validators(self):
        """validators。
        :return: 校验器声明。
        """
        return _loads(self.validators_json, default={}) or {}

    @property
    def tool_refs(self) -> list:
        """tool_refs。
        :return: 版本级工具引用列表。
        """
        return _loads(self.tool_refs_json, default=[]) or []


class McpServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    endpoint = Column(String(500), nullable=True)
    protocol = Column(String(30), nullable=True)
    credential_vault_ref = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="disabled")
    last_health_at = Column(DateTime(timezone=True), nullable=True)
    # ---- 083.2（轮19）：connector-manifest 对齐（STRICT CHECK 仅迁移层 PG）----
    stage = Column(String(20), nullable=False, default="planned")
    driver = Column(String(40), nullable=True)
    approved_hosts_json = Column(Text, nullable=True)
    allowed_ports_json = Column(Text, nullable=True)
    allow_insecure_loopback = Column(Boolean, nullable=False, default=False)
    authentication = Column(String(20), nullable=False, default="none")
    oauth_json = Column(Text, nullable=True)
    credential_fields_json = Column(Text, nullable=True)
    max_tools = Column(Integer, nullable=False, default=200)
    manifest_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="ix_mcp_servers_tenant_name"),
    )


class McpTool(Base):
    __tablename__ = "mcp_tools"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    server_id = Column(UUID_TYPE, ForeignKey("mcp_servers.id"), nullable=False)
    name = Column(String(120), nullable=False)
    input_schema_json = Column(Text, nullable=True)
    permission = Column(String(20), nullable=False, default="none")
    enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("server_id", "name", name="uq_mcp_tools_server_name"),
        CheckConstraint(
            "permission IN ({})".format(
                ", ".join(f"'{p}'" for p in MCP_TOOL_PERMISSIONS)
            ),
            name="ck_mcp_tools_permission",
        ),
    )

    @property
    def input_schema(self):
        """input_schema。
        :return: 输入 schema。
        """
        return _loads(self.input_schema_json)


class RegistryPlugin(Base):
    __tablename__ = "plugins"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True)
    name = Column(String(120), nullable=False)
    current_version = Column(String(40), nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    manifest_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="ix_plugins_tenant_name"),
    )

    @property
    def manifest(self):
        """manifest。
        :return: manifest 对象。
        """
        return _loads(self.manifest_json, default={}) or {}


class RegistryPluginVersion(Base):
    __tablename__ = "plugin_versions"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    plugin_id = Column(UUID_TYPE, ForeignKey("plugins.id"), nullable=False)
    version = Column(String(40), nullable=False)
    manifest_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("plugin_id", "version", name="uq_plugin_versions_plugin_version"),
    )

    @property
    def manifest(self):
        """manifest。
        :return: manifest 对象。
        """
        return _loads(self.manifest_json, default={}) or {}


class DataSourceProvider(Base):
    __tablename__ = "data_source_providers"

    id = Column(UUID_TYPE, primary_key=True, default=_new_uuid)
    name = Column(String(120), nullable=False, unique=True)
    data_class = Column(String(30), nullable=False)
    license_basis = Column(String(30), nullable=False)
    tos_verified = Column(Boolean, nullable=False, default=False)
    gdpr_category = Column(String(30), nullable=True)
    review_status = Column(String(20), nullable=False, default="pending")
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    __table_args__ = (
        CheckConstraint(
            "data_class IN ({})".format(", ".join(f"'{d}'" for d in DATA_CLASSES)),
            name="ck_dsp_data_class",
        ),
        CheckConstraint(
            "license_basis IN ({})".format(", ".join(f"'{l}'" for l in LICENSE_BASIS)),
            name="ck_dsp_license_basis",
        ),
        CheckConstraint(
            "review_status IN ({})".format(", ".join(f"'{r}'" for r in REVIEW_STATUSES)),
            name="ck_dsp_review_status",
        ),
    )


class TenantCapabilityToggle(Base):
    __tablename__ = "tenant_capability_toggles"

    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), primary_key=True)
    capability_type = Column(String(30), primary_key=True)
    capability_id = Column(String(36), primary_key=True)
    enabled = Column(Boolean, nullable=False, default=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )