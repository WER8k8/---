"""AI 进化引擎 — 闭环自进化系统。

流程：
  数据收集 → 经验沉淀 → Skill优化 → SOP优化 → 灰度发布 → 效果验证

模块：
- engine: 核心进化引擎，编排完整闭环
- experience_store: 经验库存储（PostgreSQL JSONB）
- version_control: Skill/SOP 语义化版本管理
- canary: 灰度发布（按租户/百分比分流 + 人工审批）
"""

from app.services.evolution.engine import EvolutionEngine
from app.services.evolution.experience_store import ExperienceStore
from app.services.evolution.version_control import VersionControl
from app.services.evolution.canary import CanaryRelease

__all__ = [
    "EvolutionEngine",
    "ExperienceStore",
    "VersionControl",
    "CanaryRelease",
]
