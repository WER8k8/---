"""能力注册表服务包（轮17）。

统一入口导出各服务工厂，供 API 路由/编排层调用。
覆盖 083 迁移 8 张表（skills/skill_versions/mcp_servers/mcp_tools/plugins/
plugin_versions/data_source_providers/tenant_capability_toggles）。
"""

from app.services.registry.skill_service import (
    SkillService,
    SkillNotFoundError,
    SkillConflictError,
    IllegalTransitionError,
    build_skill_service,
)
from app.services.registry.mcp_service import (
    McpService,
    McpNotFoundError,
    McpConflictError,
    build_mcp_service,
)
from app.services.registry.plugin_service import (
    PluginService,
    PluginNotFoundError,
    PluginConflictError,
    build_plugin_service,
)
from app.services.registry.data_source_service import (
    DataSourceService,
    DataSourceNotFoundError,
    DataSourceConflictError,
    build_data_source_service,
)
from app.services.registry.tenant_toggle import TenantToggleService, build_tenant_toggle_service

__all__ = [
    "SkillService",
    "SkillNotFoundError",
    "SkillConflictError",
    "IllegalTransitionError",
    "build_skill_service",
    "McpService",
    "McpNotFoundError",
    "McpConflictError",
    "build_mcp_service",
    "PluginService",
    "PluginNotFoundError",
    "PluginConflictError",
    "build_plugin_service",
    "DataSourceService",
    "DataSourceNotFoundError",
    "DataSourceConflictError",
    "build_data_source_service",
    "TenantToggleService",
    "build_tenant_toggle_service",
]