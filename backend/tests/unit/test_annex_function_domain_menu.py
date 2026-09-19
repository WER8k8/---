# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""功能域菜单无特权：GoodJob/TradeAI = 优丁业务菜单，非附属特权入口."""
from __future__ import annotations

from pathlib import Path

# backend/tests/unit/ → backend → worktree root
_WT = Path(__file__).resolve().parents[3]
ADMIN = _WT / "frontend" / "admin" / "src"
WS = _WT.parent  # 上线网站开发完成
EXTERNAL_GJ = WS / "_external" / "goodjob-crm"
EXTERNAL_TA = WS / "_external" / "trade-ai-agent"


def test_no_privileged_annex_group_in_client_menu():
    t = (ADMIN / "constants/proShellMenus.ts").read_text(encoding="utf-8", errors="ignore")
    assert "title: '附属执行台'" not in t
    assert "title: 'TradeAI 执行台'" not in t
    assert "title: 'GoodJob CRM'" not in t
    assert "title: '社媒拓客'" in t or "title: '外贸履约'" in t
    assert "社媒拓客" in t
    assert "外贸履约" in t


def test_platform_menu_has_no_annex_privilege_group():
    t = (ADMIN / "constants/platformShellMenu.ts").read_text(encoding="utf-8", errors="ignore")
    assert "title: '附属执行台'" not in t
    assert "title:'附属执行台'" not in t
    assert "社媒拓客" in t
    assert "外贸履约" in t
    assert "业务管理" in t


def test_annex_modules_meta_no_privilege():
    t = (ADMIN / "constants/annexModules.ts").read_text(encoding="utf-8", errors="ignore")
    assert "privileged: false" in t
    assert "label: '附属一" not in t and "label: '附属二" not in t
    assert "label: 'TradeAI 执行台'" not in t
    assert "label: 'GoodJob 执行台'" not in t
    assert "annexDomainsHaveNoPrivilege" in t
    assert "label: '社媒拓客'" in t and "label: '外贸履约'" in t


def test_workbench_registry_descriptions_no_privilege_brand():
    t = (ADMIN / "constants/workbenchCapabilityRegistry.ts").read_text(encoding="utf-8", errors="ignore")
    assert "附属一" not in t
    assert "附属二" not in t
    assert "privileged: false" in t
    assert "社媒拓客" in t and "外贸履约" in t


def test_work_mode_seamless_s7_no_privilege_menu():
    from app.services.hermes.annex_work_mode import SEAMLESS_BODY, seamless_gap_score

    ids = {s["id"] for s in SEAMLESS_BODY["standards"]}
    assert "S7" in ids
    assert SEAMLESS_BODY.get("menu_principle")
    domains = SEAMLESS_BODY["function_domains"]
    assert all(d["privileged"] is False for d in domains)
    labels = {d["label"] for d in domains}
    assert labels == {"社媒拓客", "外贸履约"}
    score = seamless_gap_score({i: True for i in ids})
    assert score["total"] == len(ids) and score["seamless"] is True


def test_identity_strip_markers_portable_paths():
    gj = (EXTERNAL_GJ / "backend/src/server.ts").read_text(encoding="utf-8", errors="ignore")
    assert "P0-ANNEX-STRIP" in gj and "annex_login_retired" in gj
    ta = (EXTERNAL_TA / "backend/app/core/annex_identity.py").read_text(encoding="utf-8", errors="ignore")
    assert "ensure_annex_product_identity_disabled" in ta
