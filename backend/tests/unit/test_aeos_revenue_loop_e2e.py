# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AEOS_REVENUE_LOOP_E2E harness 桥接测试（模块26.1 / Gate G15 工具）。

以 importlib 动态加载 scripts/qa 下的 E2E 脚本并真实执行：
- --commit 模式必须拒绝（演示链路不得冒充 G15）；
- 阶段注册表诚实：≥5 个外部依赖阶段明示 blocked_by；
- 全链事务内执行零 fail（pass + blocked，结束回滚不留脏数据）。
"""
from __future__ import annotations

import importlib.util
import pathlib

MODULE = None


def _load_module():
    global MODULE
    if MODULE is None:
        qa_dir = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "qa"
        script = next(qa_dir.glob("aeos_*.py"))
        spec = importlib.util.spec_from_file_location("aeos_e2e_module", script)
        MODULE = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(MODULE)
    return MODULE


def test_commit_mode_is_refused():
    m = _load_module()
    assert m.run(commit_mode=True) == 3, "演示链路不得冒充真实租户 G15"


def test_stage_registry_is_honest():
    m = _load_module()
    names = {s["name"] for s in m.STAGES}
    assert {"tenant_provision", "inquiry_qualification_metering",
            "billing_reserve_settle_reverse", "api_market_track7"} <= names
    blocked = [s for s in m.STAGES if s.get("requires_external")]
    assert len(blocked) >= 5, "外部依赖阶段必须显式登记 blocked_by"
    assert all(isinstance(s["requires_external"], str) and s["requires_external"]
               for s in blocked)


def test_full_transactional_loop_has_zero_fail():
    m = _load_module()
    exit_code = m.run()
    assert exit_code == 0, "E2E 全链存在 fail 阶段（blocked 允许，fail 不允许）"
