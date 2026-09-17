"""PC-01~PC-05 回归锁（09-13 全平台对齐）。

四把锁各自对应一个真实踩过的坑：
  1. 误路由：平台名解析到别人的发布器键 → 串号真发 / 永远发不出去
  2. 穷举：目录里存在的平台必须有「键或适配器」落点，否则排序与发布双双漏台
  3. 鉴权分类：不能把「没配凭证」「网络抖动」误判成 cookie 过期
  4. 巡检 dry_run：只出报告，绝不改库
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.content import Platform, PlatformAccount
from app.services.publish_capability_registry import (
    LIVE_PUBLISHER_KEYS,
    STUB_PUBLISHER_KEYS,
)
from app.services.publish_dispatch_service import (
    _NAME_ADAPTER_IMPORTS,
    _publisher_key,
)
from app.services.publish_service import PUBLISHER_MAP
from app.services.geo.platform_rank_registry import all_platform_rank_profiles
from app.services.platform_catalog import all_catalog_rows
from app.services.platform_session_patrol_service import (
    classify_publish_failure,
    patrol_platform_sessions,
)


def _plat(name: str, ptype: str = "article") -> Platform:
    return Platform(id=f"p-{name}", name=name, platform_type=ptype, region="cn")


# ---------------------------------------------------------------------------
# 1) 误路由锁
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "platform_name,forbidden_key,expected_key",
    [
        # 微信视频号 曾被解析成 wechat（= 微信公众号发布器），会串号真发
        ("微信视频号", "wechat", "wechat_channels"),
        # 头条号 曾借 douyin 键，而 douyin 在 STUB 集合里，
        # 于是有真适配器的头条号被判「未接入」，图文永远发不出去
        ("头条号", "douyin", "toutiao"),
        # 大鱼号 曾冒名 douyin
        ("大鱼号", "douyin", "dayuhao"),
    ],
)
def test_publisher_key_no_cross_platform_routing(
    platform_name: str, forbidden_key: str, expected_key: str
):
    key = _publisher_key(_plat(platform_name))
    assert key != forbidden_key, platform_name
    assert key == expected_key, platform_name


def test_toutiao_is_live_publisher_not_stub():
    """头条号解析出的键必须可真发，不能落回 stub 集合。"""
    key = _publisher_key(_plat("头条号"))
    assert key in LIVE_PUBLISHER_KEYS, key
    assert key not in STUB_PUBLISHER_KEYS, key


# ---------------------------------------------------------------------------
# 2) 穷举锁
# ---------------------------------------------------------------------------


# 这三个海外 B2B 走 b2b_global 适配器，不在 PUBLISHER_MAP 里，属已知口径
_B2B_ADAPTER_ONLY_KEYS = {"alibaba", "made_in_china", "globalsources"}


def test_every_catalog_platform_has_a_landing_point():
    """目录内每个平台三选一：live 键 / 已登记键（含 Unimplemented）/ 有真适配器。

    解析不出键且没有适配器的平台，发布链路会静默漏台，故视为缺陷。
    """
    gaps: list[str] = []
    for name, ptype, _region, _content in all_catalog_rows():
        plat = Platform(id=f"p-{name}", name=name, platform_type=ptype, region="cn")
        key = _publisher_key(plat)
        has_adapter = name in _NAME_ADAPTER_IMPORTS
        known_key = (
            key in PUBLISHER_MAP
            or key in _B2B_ADAPTER_ONLY_KEYS
            or key in LIVE_PUBLISHER_KEYS
        )
        if not (has_adapter or known_key):
            gaps.append(f"{name} -> {key or '(无键)'}")
    assert gaps == [], f"以下平台无发布落点：{gaps}"


def test_rank_registry_covers_whole_catalog():
    """PC-03：排名档案不得漏台，漏了的 geo_weight 会回落 0.5、rank_priority 回落 99。"""
    registered = {p.name for p in all_platform_rank_profiles()}
    missing = [row[0] for row in all_catalog_rows() if row[0] not in registered]
    assert missing == [], f"缺少排名档案的平台：{missing}"


def test_rank_priority_is_unique_across_profiles():
    """同优先级会让排序结果不稳定；档案内 rank_priority 不得重复。"""
    seen: dict[int, str] = {}
    dup: list[str] = []
    for profile in all_platform_rank_profiles():
        prio = int(profile.rank_priority)
        if prio in seen:
            dup.append(f"{seen[prio]} / {profile.name} @{prio}")
        seen[prio] = profile.name
    assert dup == [], f"rank_priority 重复：{dup}"


# ---------------------------------------------------------------------------
# 3) 鉴权失败分类锁
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "RuntimeError: 登录已失效，请重新登录",
        "invalid session abc",
        "401 Unauthorized",
        "token expired",
    ],
)
def test_auth_failures_classified_as_auth(text: str):
    assert classify_publish_failure(text) == "auth"


@pytest.mark.parametrize(
    "text",
    [
        # 未配凭证 / 未实现：与 cookie 过期无关
        "PLATFORM_NOT_CONFIGURED: 缺少 alibaba_access_token",
        "PLATFORM_NOT_IMPLEMENTED 尚未接入",
        "gate_blocked: 双线未就绪",
        # 网络与限流：重绑 cookie 解决不了
        "Connection timeout after 30s",
        "HTTP 429 too many requests",
        "unauthorized request blocked by rate limit",
    ],
)
def test_non_auth_failures_must_not_mark_session_expired(text: str):
    assert classify_publish_failure(text) is None


def test_empty_or_none_error_is_not_auth():
    assert classify_publish_failure(None) is None
    assert classify_publish_failure("   ") is None


# ---------------------------------------------------------------------------
# 4) 巡检：dry_run 不改库
# ---------------------------------------------------------------------------


class _ChainQuery:
    def __init__(self, rows):
        self._rows = rows

    def join(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def limit(self, _n):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    """只满足 patrol_platform_sessions 用到的 query/commit 两个接口。"""

    def __init__(self, rows):
        self._rows = rows
        self.commits = 0

    def query(self, *a, **k):
        return _ChainQuery(self._rows)

    def commit(self):
        self.commits += 1


def _expired_token_account():
    now = datetime.now(timezone.utc)
    plat = Platform(id="p1", name="知乎", platform_type="article", region="cn")
    acc = PlatformAccount(
        id="a1",
        platform_id="p1",
        tenant_id="t1",
        account_name="zhihu-main",
        login_status="logged_in",
        is_active=True,
        cookie_data="dummy-cookie-should-never-be-returned",
        token_expire_at=now - timedelta(days=1),
    )
    return acc, plat


def test_patrol_dry_run_does_not_mutate_or_commit():
    acc, plat = _expired_token_account()
    db = _FakeSession([(acc, plat)])
    report = patrol_platform_sessions(db, cookie_stale_days=14, dry_run=True)
    assert report["expired_candidates"] == 1
    assert report["expired_marked"] == 0
    assert acc.login_status == "logged_in"
    assert db.commits == 0


def test_patrol_marks_expired_and_never_leaks_cookie():
    acc, plat = _expired_token_account()
    db = _FakeSession([(acc, plat)])
    report = patrol_platform_sessions(db, cookie_stale_days=14, dry_run=False)
    assert acc.login_status == "expired"
    assert report["expired_marked"] == 1
    assert db.commits == 1
    finding = report["findings"][0]
    assert finding["has_cookie"] is True
    blob = str(report)
    assert "dummy-cookie-should-never-be-returned" not in blob


def test_patrol_skips_account_without_any_signal():
    """未到期的 token + 刚更新过的 cookie：不该被摘下来。"""
    now = datetime.now(timezone.utc)
    plat = Platform(id="p2", name="小红书", platform_type="article", region="cn")
    acc = PlatformAccount(
        id="a2",
        platform_id="p2",
        tenant_id="t1",
        account_name="xhs",
        login_status="logged_in",
        is_active=True,
        cookie_data="fresh",
        last_login_at=now - timedelta(days=1),
        token_expire_at=now + timedelta(days=30),
    )
    db = _FakeSession([(acc, plat)])
    report = patrol_platform_sessions(db, cookie_stale_days=14, dry_run=False)
    assert report["expired_candidates"] == 0
    assert acc.login_status == "logged_in"
