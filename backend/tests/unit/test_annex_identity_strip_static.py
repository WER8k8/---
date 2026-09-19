# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""静态校验：附属产品身份/管理台已剥（P0-ANNEX-STRIP）· 仓库相对路径."""
from __future__ import annotations

from pathlib import Path

_WT = Path(__file__).resolve().parents[3]
WS = _WT.parent.parent


def test_goodjob_strip_markers():
    t = (WS / "_external/goodjob-crm/backend/src/server.ts").read_text(encoding="utf-8", errors="ignore")
    assert "P0-ANNEX-STRIP" in t
    assert "annex_login_retired" in t
    assert "annex_console_retired" in t
    assert "/api/auth/annex-ticket" in t
    assert "/api/uj-bridge" in t


def test_tradeai_strip_module_and_auth_guard():
    core = (WS / "_external/trade-ai-agent/backend/app/core/annex_identity.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    assert "annex_login_retired" in core
    assert "annex_console_retired" in core
    auth = (WS / "_external/trade-ai-agent/backend/app/api/v1/auth.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    assert "ensure_annex_product_identity_disabled" in auth
    main_py = (WS / "_external/trade-ai-agent/backend/app/main.py").read_text(encoding="utf-8", errors="ignore")
    assert "annex_identity_middleware" in main_py


def test_uj_work_mode_still_present():
    p = _WT / "backend/app/services/hermes/annex_work_mode.py"
    assert p.is_file()
    assert "GOLDEN_PATH_A" in p.read_text(encoding="utf-8", errors="ignore")
