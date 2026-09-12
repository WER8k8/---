"""六插槽注册表：缺项显式报红，不做静默降级。"""

from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType
from typing import Any, Mapping

from app.orchestration.interfaces import SlotArchetype, archetype_of


class SlotRegistry:
    """按插槽原型登记唯一适配器；调度方只依赖本目录，不散落具体实现。"""

    def __init__(self, adapters: Iterable[Any] = ()) -> None:
        self._adapters: dict[SlotArchetype, Any] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: Any) -> None:
        archetype = archetype_of(adapter)
        if archetype is None:
            raise TypeError("对象未实现任何六插槽契约，拒绝接入")
        self._adapters[archetype] = adapter

    def slot_adapter(self, archetype: SlotArchetype) -> Any:
        try:
            return self._adapters[archetype]
        except KeyError as exc:
            raise RuntimeError(f"插槽未注册适配器: {archetype.value}") from exc

    def registered_slots(self) -> tuple[SlotArchetype, ...]:
        return tuple(self._adapters)

    def require_all_slots(self) -> Mapping[SlotArchetype, Any]:
        missing = [slot for slot in SlotArchetype if slot not in self._adapters]
        if missing:
            names = ", ".join(slot.value for slot in missing)
            raise RuntimeError(f"六插槽存在缺口: {names}")
        return MappingProxyType(dict(self._adapters))


__all__ = ["SlotRegistry"]
