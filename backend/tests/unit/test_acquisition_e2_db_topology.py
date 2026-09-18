# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E-2 读写分离助手 + 生产门禁实跑。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from app.api.v1.routes import acquisition as acq_api
from app.core.db_sessions import db_topology, mark_write, read_engine_configured


class _User:
    id = "u1"
    username = "tester"


def _user() -> _User:
    return _User()


def test_db_topology_honest():
    topo = db_topology()
    assert "plain_summary" in topo
    assert "primary_configured" in topo
    assert "read_configured" in topo
    assert isinstance(read_engine_configured(), bool)
    if not read_engine_configured():
        assert "未配置" in topo["plain_summary"] or "主库" in topo["plain_summary"]
    api = acq_api.acquisition_db_topology(current_user=_user())
    assert api["plain_summary"]


def test_mark_write_sets_info():
    class _S:
        info = {}

    s = _S()
    mark_write(s)
    assert s.info.get("write") is True


def test_production_gates_script_runs():
    backend = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(backend))
    from scripts.verify_acquisition_production_gates import check_production_gates

    os.environ.setdefault("LIBRETRANSLATE_URL", "http://127.0.0.1:8098")
    out = check_production_gates()
    assert "checks" in out
    assert out["total"] >= 5
    assert "plain_summary" in out
    # 不因本机端口状态而 assert ready；只保证报告诚实字段
    ids = {c["id"] for c in out["checks"]}
    assert {"translate", "human_gate", "wallet_block"}.issubset(ids)
