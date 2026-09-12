"""编排层公共契约（适配器契约目录，见架构体检 P1 缺口与设计文档 §10.16）。"""

from app.orchestration.interfaces import (
    ChannelFrontendContract,
    DataSourceProvider,
    ErpConnector,
    ExecutorAdapter,
    McpToolProvider,
    SkillPackageSource,
    SlotArchetype,
)
from app.orchestration.registry import SlotRegistry

__all__ = [
    "ChannelFrontendContract",
    "DataSourceProvider",
    "ErpConnector",
    "ExecutorAdapter",
    "McpToolProvider",
    "SkillPackageSource",
    "SlotArchetype",
    "SlotRegistry",
]
