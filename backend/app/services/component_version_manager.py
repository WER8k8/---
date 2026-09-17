# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""组件版本管理 + 热更新回滚引擎。

支持：
- 组件版本注册与追踪
- 热更新（importlib.reload）
- 回滚到上一版本
- 版本快照（JSON 持久化）
"""
from __future__ import annotations

import importlib
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "data" / "component_versions.json"


@dataclass
class ComponentVersion:
    module: str
    version: str
    loaded_at: float = field(default_factory=time.time)
    hash: str = ""
    status: str = "active"


class ComponentVersionManager:
    _versions: dict[str, list[ComponentVersion]] = {}

    @classmethod
    def register(cls, module: str, version: str, hash: str = "") -> ComponentVersion:
        cv = ComponentVersion(module=module, version=version, hash=hash)
        cls._versions.setdefault(module, []).append(cv)
        cls._persist()
        logger.info("Registered %s@%s", module, version)
        return cv

    @classmethod
    def current(cls, module: str) -> ComponentVersion | None:
        return cls._versions.get(module, [None])[-1] or None

    @classmethod
    def history(cls, module: str) -> list[ComponentVersion]:
        return list(cls._versions.get(module, []))

    @classmethod
    def hot_reload(cls, module: str) -> bool:
        mod = sys.modules.get(module)
        if not mod:
            logger.warning("Module %s not loaded", module)
            return False
        try:
            importlib.reload(mod)
            logger.info("Hot-reloaded %s", module)
            return True
        except Exception as e:
            logger.error("Hot-reload failed for %s: %s", module, e)
            return False

    @classmethod
    def rollback(cls, module: str, target_version: str | None = None) -> bool:
        versions = cls._versions.get(module, [])
        if len(versions) < 2:
            logger.warning("No rollback target for %s", module)
            return False
        target = target_version or versions[-2].version
        prev = next((v for v in reversed(versions) if v.version == target), None)
        if not prev:
            logger.warning("Version %s not found for %s", target, module)
            return False
        if cls.hot_reload(module):
            prev.status = "rolled-back"
            cls._persist()
            logger.info("Rolled back %s to %s", module, target)
            return True
        return False

    @classmethod
    def list_all(cls) -> dict[str, ComponentVersion | None]:
        return {m: cls.current(m) for m in cls._versions}

    @classmethod
    def _persist(cls):
        _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {m: [asdict(v) for v in vs] for m, vs in cls._versions.items()}
        _SNAPSHOT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def load_snapshot(cls):
        if not _SNAPSHOT_PATH.exists():
            return
        data = json.loads(_SNAPSHOT_PATH.read_text())
        for m, vs in data.items():
            cls._versions[m] = [ComponentVersion(**v) for v in vs]
