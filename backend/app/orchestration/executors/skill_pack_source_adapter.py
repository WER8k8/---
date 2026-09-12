"""SKILL 插槽适配器：读取磁盘 SKILL.md 标准包。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from app.orchestration.interfaces import SkillPackageSource, SlotArchetype
from app.services.registry.skill_pack_loader import discover_skill_packs, load_skill_body


class SkillNotFoundError(FileNotFoundError):
    """请求的技能包不存在；调用方不得把空包伪装成成功。"""


class SkillPackSourceAdapter(SkillPackageSource):
    """对既有技能包加载器做最薄封装。"""

    archetype = SlotArchetype.SKILL

    def __init__(self, dirs: Iterable[tuple[str, Path]] | None = None) -> None:
        self._dirs = list(dirs) if dirs is not None else None

    def fetch_skill_package(self, ref: str) -> Mapping[str, Any]:
        name = ref.strip()
        if not name:
            raise ValueError("技能包引用不能为空")

        entries = discover_skill_packs(self._dirs)
        entry = next((item for item in entries if item.name == name), None)
        if entry is None:
            raise SkillNotFoundError(f"未找到技能包: {name}")
        body = load_skill_body(name, self._dirs)
        if not body:
            raise SkillNotFoundError(f"技能包内容为空: {name}")

        return {
            "skill_md": body,
            "version": entry.version,
            "license": "unspecified",
        }


__all__ = ["SkillPackSourceAdapter", "SkillNotFoundError"]
