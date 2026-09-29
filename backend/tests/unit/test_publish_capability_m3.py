# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块 5 · M3 八标志位能力登记（契约 §5）配对反证测试。

负向（4）：
1. test_all_stub_platforms_are_not_admitted  —— 桩 56 键全不得计入
2. test_zero_admitted_at_baseline            —— 基线 0 平台计入（§5.2 现值结论）
3. test_register_unknown_platform_raises     —— 拒绝凭空造平台
4. test_register_unknown_dimension_raises    —— 八步之外不接受新维度

正向（4）：
5. test_register_flips_flags_and_admits      —— 八位全翻真 → admitted True
6. test_register_ignores_false               —— 传 False 不翻回
7. test_admitted_count_increments            —— 计数随翻真 +1
8. test_platform_admission_flags_shape       —— 返回八键全 bool

dry_run_publish（3）：
9.  test_dry_run_no_db_returns_error
10. test_dry_run_unknown_platform            —— 平台不在目录 → NOT_CONFIGURED
11. test_dry_run_missing_credential_blocked  —— fail-closed：无凭据 → credential_missing
"""
from __future__ import annotations

import pytest

from app.services import publish_capability_registry as R
from app.services.publish_service import PUBLISHER_MAP

# 桩键 = PUBLISHER_MAP 去掉 8 个真发类（LIVE_PUBLISHER_KEYS）
LIVE = set(R.LIVE_PUBLISHER_KEYS)
STUB_KEYS = [k for k in PUBLISHER_MAP if k not in LIVE]
assert len(STUB_KEYS) == 56, f"桩键数应为 56，实际 {len(STUB_KEYS)}"


# ── 负向 ─────────────────────────────────────────────────────────

def test_all_stub_platforms_are_not_admitted():
    for k in STUB_KEYS:
        assert R.platform_admitted(k) is False, f"桩平台 {k} 不得计入"


def test_zero_admitted_at_baseline():
    # §5.2 现值结论：Dry Run 全 False + 凭据全空 → 0 平台计入
    assert R.admitted_platform_count() == 0


def test_register_unknown_platform_raises():
    with pytest.raises(ValueError):
        R.register_platform_admission("totally_fake_platform", adapter=True)


def test_register_unknown_dimension_raises():
    with pytest.raises(ValueError):
        R.register_platform_admission("zhihu", fake_dimension=True)


# ── 正向 ─────────────────────────────────────────────────────────

def test_register_flips_flags_and_admits():
    saved = dict(R.platform_admission_flags("zhihu"))
    try:
        for step in R.ADMISSION_STEPS:
            R.register_platform_admission("zhihu", **{step: True})
        assert R.platform_admitted("zhihu") is True
        assert R.admitted_platform_count() >= 1
    finally:
        # 还原：本测试不留污染
        for s, v in saved.items():
            R.PLATFORM_ADMISSION["zhihu"][s] = v


def test_register_ignores_false():
    saved = dict(R.platform_admission_flags("zhihu"))
    try:
        R.register_platform_admission("zhihu", adapter=True)
        assert R.platform_admission_flags("zhihu")["adapter"] is True
        # 传 False 不翻回
        R.register_platform_admission("zhihu", adapter=False)
        assert R.platform_admission_flags("zhihu")["adapter"] is True
    finally:
        for s, v in saved.items():
            R.PLATFORM_ADMISSION["zhihu"][s] = v


def test_admitted_count_increments():
    base = R.admitted_platform_count()
    saved = {k: dict(v) for k, v in R.PLATFORM_ADMISSION.items() if k == "zhihu"}
    try:
        for step in R.ADMISSION_STEPS:
            R.register_platform_admission("zhihu", **{step: True})
        assert R.admitted_platform_count() == base + 1
    finally:
        for k, d in saved.items():
            for s, v in d.items():
                R.PLATFORM_ADMISSION[k][s] = v


def test_platform_admission_flags_shape():
    f = R.platform_admission_flags("unknown_platform_xyz")
    assert set(f.keys()) == set(R.ADMISSION_STEPS)
    assert all(v is False for v in f.values())


# ── dry_run_publish ──────────────────────────────────────────────

def test_dry_run_no_db_returns_error():
    out = R.dry_run_publish(None, tenant_id="t1", platform_id="zhihu",
                            content={"body": "x"})
    assert out["ok"] is False
    assert out["error_code"] == "no_session"


class _FakeCfg:
    id = "plat-id-1"
    name = "Zhihu"


class _FakeQ:
    def __init__(self, rows):
        self._rows = rows
        self._filters = []

    def filter(self, *a):
        return self

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeDb:
    def __init__(self, rows):
        self._rows = rows

    def query(self, *a, **kw):
        return _FakeQ(self._rows)


def test_dry_run_unknown_platform():
    out = R.dry_run_publish(_FakeDb([]), tenant_id="t1", platform_id="no-such",
                            content={"body": "x"})
    assert out["ok"] is False
    assert out["error_code"] == R.PLATFORM_NOT_CONFIGURED
    assert "不在目录" in out["blocked_reason"]


def test_dry_run_missing_credential_blocked():
    """fail-closed：平台在目录但租户无凭据 → credential_missing，不发网络。

    mock resolve_publish_credential 返回空 values。
    """
    from unittest.mock import patch

    with patch(
        "app.services.publish_service.PublishService.resolve_publish_credential",
        return_value={"source": "none", "values": {}, "account_id": None,
                      "credential_ref": None, "error_code": "credential_missing"},
    ):
        out = R.dry_run_publish(_FakeDb([_FakeCfg()]), tenant_id="t1",
                                platform_id="plat-id-1", content={"body": "x"})
    # 真库查不到该租户账号 → credential_missing（fail-closed）
    assert out["ok"] is False
    assert out["error_code"] in ("credential_missing",)
    assert out["credential_source"] == "none"
