"""外贸 AI 技能引擎 — 统一入口。"""

from app.services.foreign_trade.skill_registry import SkillRegistry, SkillResult, skill_registry

__all__ = ["SkillRegistry", "SkillResult", "skill_registry"]
