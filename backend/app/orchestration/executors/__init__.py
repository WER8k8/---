"""六插槽契约的真实适配器实现目录（见 §10.16/§10.19）。"""

from app.orchestration.executors.channel_frontend_adapter import ChannelFrontendAdapter
from app.orchestration.executors.data_source_enrich_adapter import DataSourceEnrichAdapter
from app.orchestration.executors.erp_gateway_adapter import ErpGatewayAdapter
from app.orchestration.executors.goodjob_executor import GoodJobExecutor
from app.orchestration.executors.mcp_manifest_adapter import McpManifestAdapter
from app.orchestration.executors.skill_pack_source_adapter import SkillPackSourceAdapter

__all__ = [
    "ChannelFrontendAdapter",
    "DataSourceEnrichAdapter",
    "ErpGatewayAdapter",
    "GoodJobExecutor",
    "McpManifestAdapter",
    "SkillPackSourceAdapter",
]
