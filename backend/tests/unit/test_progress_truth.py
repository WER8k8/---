# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""进度真源派生纯函数测试（修正设计稿 模块25）。

锁定语义：
- code_present：证据路径全部存在才 True；
- route_mounted：无路由要求 = True（不适用）；有要求则前缀必须命中；
- test_present：关键词命中测试文件名才 True；
- production_ready：证据布尔 AND，任何 None（未测）一律 False —— 无人工写入口。
"""
from __future__ import annotations

from scripts import progress_truth as pt


def _row(**over) -> dict:
    base = {
        "code_present": True,
        "route_mounted": True,
        "test_present": True,
        "test_passed": True,
        "runtime_verified": True,
        "data_verified": True,
    }
    base.update(over)
    return base


class TestCodePresent:
    def test_all_paths_must_exist(self, tmp_path):
        (tmp_path / "a.py").write_text("x", encoding="utf-8")
        assert pt.code_present_for(tmp_path, ["a.py"]) is True
        assert pt.code_present_for(tmp_path, ["a.py", "missing.py"]) is False


class TestRouteMounted:
    def test_no_requirements_is_true(self):
        assert pt.route_mounted_for(set(), []) is True

    def test_prefix_must_be_mounted(self):
        mounted = {"/api/v1/orchestration/plan", "/api/v1/health"}
        assert pt.route_mounted_for(mounted, ["/api/v1/orchestration"]) is True
        assert pt.route_mounted_for(mounted, ["/api/v1/missing"]) is False


class TestTestPresent:
    def test_keyword_hits_test_file(self, tmp_path):
        (tmp_path / "test_outbox.py").write_text("x", encoding="utf-8")
        assert pt.test_present_for(tmp_path, ["outbox"]) is True
        assert pt.test_present_for(tmp_path, ["quantum"]) is False
        assert pt.test_present_for(tmp_path, []) is False


class TestProductionReady:
    def test_all_true_and_suite_green(self):
        assert pt.production_ready(_row()) is True

    def test_any_none_is_false(self):
        assert pt.production_ready(_row(test_passed=None)) is False
        assert pt.production_ready(_row(runtime_verified=None)) is False

    def test_failed_suite_is_false(self):
        assert pt.production_ready(_row(test_passed=False)) is False
