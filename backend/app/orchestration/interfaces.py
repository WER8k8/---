# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""通用能力插槽契约 · Universal Capability Slot Contract.

设计出处：uj-annex-integration-design §10.16；对应架构体检 P1 缺口
（orchestration/interfaces.py 适配器契约目录）。

任何外部开源项目接入本系统，必须归入且仅归入一个插槽原型：

    EXECUTOR     执行器适配器 —— 吃任务包（五字段），产结果回真相层
    MCP_TOOL     MCP 工具提供方 —— 注册进 mcp_servers（083.2 连接器清单）
    SKILL        技能包 —— SKILL.md 标准，走安装流水线（§10.13）
    DATA_SOURCE  数据源提供方 —— 采集/富化单向投喂获客环
    CHANNEL      渠道面前端 —— 只做呈现+采集，不持状态（§10.15.1）
    ERP_BACKEND  ERP 连接器 —— 第三方仓库 ERP 双向对接：订单出、库存/履约进

红线：不存在 ORCHESTRATION 插槽（调度主权归 Hermes，D3）；GPL/AGPL 家族
禁止进程内嵌入；每个插槽交付必须带首个调用方；接入一律过四闸门
（静态检查 → 契约测试 → 083 注册+人审 → toggle 默认 off + 灰度）。

仅依赖标准库，可在无 pydantic/fastapi 的环境 import。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class SlotArchetype(str, Enum):
    EXECUTOR = "executor"
    MCP_TOOL = "mcp_tool"
    SKILL = "skill"
    DATA_SOURCE = "data_source"
    CHANNEL = "channel"
    ERP_BACKEND = "erp_backend"


@dataclass(frozen=True)
class TaskPackage:
    """Hermes 签发的任务包，五字段为调度契约铁律，缺一即拒绝派发。"""

    tenant_id: str
    idempotency_key: str
    lease_ttl: int
    checkpoint: str
    budget: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    idempotency_key: str
    result_ref: str | None = None
    metrics: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None


class ExecutorAdapter(ABC):
    """EXECUTOR 插槽：执行器不自持任务状态——租约到期未续即视为失败，由 Hermes 重派。"""

    archetype = SlotArchetype.EXECUTOR

    @abstractmethod
    def submit(self, package: TaskPackage) -> str:
        """接受任务包并返回受理句柄；同 idempotency_key 重复提交必须幂等。"""

    @abstractmethod
    def poll(self, idempotency_key: str) -> ExecutionResult | None:
        """按幂等键查询执行结果；未完成返回 None，不得阻塞。"""


class McpToolProvider(ABC):
    """MCP_TOOL 插槽：以 083.2 连接器清单字段自描述，工具上架走 mcp_servers 注册表。"""

    archetype = SlotArchetype.MCP_TOOL

    @abstractmethod
    def manifest(self) -> Mapping[str, Any]:
        """返回连接器清单：endpoint / transport / auth / scopes / 版本 / 健康检查。"""


class SkillPackageSource(ABC):
    """SKILL 插槽：技能内容必须是 SKILL.md 标准包（§10.13 安装流水线的进口）。"""

    archetype = SlotArchetype.SKILL

    @abstractmethod
    def fetch_skill_package(self, ref: str) -> Mapping[str, Any]:
        """按引用返回 {'skill_md': str, 'version': str, 'license': str}。"""


class DataSourceProvider(ABC):
    """DATA_SOURCE 插槽：富化结果单向写入租户档案，注册走 data_source 注册表（含审核闸）。"""

    archetype = SlotArchetype.DATA_SOURCE

    @abstractmethod
    def enrich(self, tenant_id: str, subject: Mapping[str, Any]) -> Mapping[str, Any]:
        """对目标主体（域名/公司/邮箱）返回结构化富化结果，必须可按租户隔离。"""


class ChannelFrontendContract(ABC):
    """CHANNEL 插槽：前端面只做呈现+采集——写路径必须经 Repository 收口（RLS），不持本地状态。"""

    archetype = SlotArchetype.CHANNEL

    @abstractmethod
    def frontend_manifest(self) -> Mapping[str, Any]:
        """返回渠道清单：平台 / 认证方式（映射既有 JWT）/ 写端点（须为既有 API）。"""


class ErpConnector(ABC):
    """ERP_BACKEND 插槽：第三方仓库 ERP（旺店通/聚水潭/金蝶等）双向对接.

    真相边界——派单点是分界线：订单派单前 UJ 独占真相，派单后履约真相在
    ERP、UJ 只持履约投影；库存真相永远在 ERP，UJ 侧只持展示快照缓存。
    订单仍由 UJ order 表出（复用既有五件套），ERP 不回写订单主数据。
    """

    archetype = SlotArchetype.ERP_BACKEND

    @abstractmethod
    def push_order(self, tenant_id: str, order_payload: Mapping[str, Any]) -> str:
        """推送订单至 ERP，返回外部单号 external_ref；同单重推必须幂等。"""

    @abstractmethod
    def pull_inventory(self, tenant_id: str, skus: tuple[str, ...]) -> Mapping[str, Any]:
        """按 SKU 拉库存快照（available/reserved），仅作展示与预留，不作真相。"""

    @abstractmethod
    def pull_fulfillment_status(self, tenant_id: str, external_refs: tuple[str, ...]) -> Mapping[str, Any]:
        """拉履约状态（发货/签收）回写 UJ 订单 fulfillment 投影字段。"""


@dataclass(frozen=True)
class NavSlotDescriptor:
    """导航入口描述符：单一生成源 —— 一份描述符生成四处注册.

    四处 = navRouteRegistry 路由表 + 超管侧栏菜单 + Lab/送检显隐 + 能力守卫表。
    新项目接入（如 TradeAI/GoodJob/未来热门项目）只声明本描述符，导航注册
    由生成器统一产出，禁止再手写四处（防漏注册导致的菜单 404 或显隐错乱）。
    """

    nav_key: str
    route_path: str
    label: str
    group: str = "super-admin-tools"
    capability_id: str = ""
    lab_only: bool = True
    order: int = 100
    embed_url_env: str | None = None


class NavCapable(ABC):
    """带导航入口的接入件实现此契约；与插槽原型正交（任何原型都可带导航）。"""

    @abstractmethod
    def nav_descriptor(self) -> NavSlotDescriptor:
        """返回该接入件的导航描述符；同 group 内按 order 排序渲染。"""


@dataclass(frozen=True)
class SlotIntakeCheck:
    """四闸门之第一闸的静态检查结论，任一项不过即终止接入。"""

    license_ok: bool
    egress_ok: bool
    resource_ok: bool
    notes: str = ""


def archetype_of(slot: Any) -> SlotArchetype | None:
    """判定候选接入件归属的插槽原型；不属于任何插槽（如想当调度者）返回 None，即拒绝接入。"""
    if isinstance(slot, ExecutorAdapter):
        return SlotArchetype.EXECUTOR
    if isinstance(slot, McpToolProvider):
        return SlotArchetype.MCP_TOOL
    if isinstance(slot, SkillPackageSource):
        return SlotArchetype.SKILL
    if isinstance(slot, DataSourceProvider):
        return SlotArchetype.DATA_SOURCE
    if isinstance(slot, ChannelFrontendContract):
        return SlotArchetype.CHANNEL
    if isinstance(slot, ErpConnector):
        return SlotArchetype.ERP_BACKEND
    return None


__all__ = [
    "SlotArchetype",
    "TaskPackage",
    "ExecutionResult",
    "SlotIntakeCheck",
    "ExecutorAdapter",
    "McpToolProvider",
    "SkillPackageSource",
    "DataSourceProvider",
    "ChannelFrontendContract",
    "ErpConnector",
    "NavSlotDescriptor",
    "NavCapable",
    "archetype_of",
]
