# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""回归锁：ContentMaster 悬空 platforms 关系不得复活（模块4 STEP0）。

背景：`ContentMaster.platforms` **从未**在 ORM 中定义（无 relationship、无关联表），
但 `routes/content_master.py` / `routes/unified_publish.py` 曾用
`joinedload/selectinload(ContentMaster.platforms)` 预加载它 —— 在**构造期**即抛
`AttributeError: type object 'ContentMaster' has no attribute 'platforms'`，
三处调用全在活端点上，均会 500。本模块4 STEP0 已删除这三处悬空预加载。

本锁断言「**当前事实**」：
1. `hasattr(ContentMaster, "platforms") is False`（关系确实不存在）；
2. `backend/app/` 源码里不再出现 `ContentMaster.platforms` 字面量（0 命中）。

⚠ 语义提示：若将来**真的**定义了 `ContentMaster.platforms` 关系（并配套迁移 +
契约更新），本锁应随**契约更新**（改为断言新语义），而不是反过来把 bug 锁死。
本锁锁定的是「未定义却引用」这一缺陷，而非「永远不得定义」。
"""
from __future__ import annotations

from pathlib import Path

from app.models.content_master import ContentMaster

_BACKEND = Path(__file__).resolve().parents[2]  # backend/
_APP_DIR = _BACKEND / "app"
_LITERAL = "ContentMaster.platforms"


def _iter_source_files():
    for path in _APP_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        yield path


def test_content_master_has_no_platforms_relation() -> None:
    """当前事实：ContentMaster 未定义 platforms 关系（悬空引用已删除）。"""
    assert hasattr(ContentMaster, "platforms") is False


def test_no_source_literal_content_master_platforms() -> None:
    """源码级扫描：backend/app 下不再出现 `ContentMaster.platforms` 字面量（0 命中）。"""
    hits: list[str] = []
    for path in _iter_source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _LITERAL in text:
            hits.append(str(path.relative_to(_BACKEND)))
    assert hits == [], f"仍存在悬空引用 {_LITERAL}: {hits}"
