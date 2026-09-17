"""真实租户隔离测试 — 针对代码库真实函数（非 mock 壳）

背景：文档《SaaS外贸全链路测试体系》§13 把多租户隔离列为上线前红线。
此前一轮测试（test_tenant_isolation.py）对着自建 mock FastAPI 写，测的是
"假应用天生返回 403"，真实后端的判定逻辑一点没覆盖。

本文件测的是**产品代码本身**的三个真实判定：
  - app/api/v1/routes/inquiries.py :: _check_inquiry_tenant_access
  - app/services/logistics_tracking_service.py :: get_order_for_user
  - app/models/enums.py :: OrderStatus / _ORDER_TRANSITIONS

实现说明：前两个函数所在模块的 import 链会拉起整棵 service 树
（osint/whois.py 用到 py3.12 的 datetime.UTC），因此这里用「读源码 + exec
单函数」的方式加载被测函数本体——**逻辑一行未改**，只是绕开无关 import，
让测试在任何 3.10+ 环境都能跑。get_order_for_user 依赖的
tenant_member_user_ids 以可控桩注入（该桩只决定"成员集合"，不碰越权判定本身）。

运行：  python -m pytest tests/integration/test_real_tenant_isolation.py -v
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

_BK = Path(__file__).resolve().parents[2]


class _Sentinel:
    """模型占位类：带 id 类属性，让 `Model.id == x` 这类过滤表达式可求值。"""
    id = None


def _load_real_func(relpath: str, func_name: str, extra_ns: dict | None = None):
    """从真实源文件提取单个顶层函数并 exec，绕开整棵 import 树。"""
    src = (_BK / relpath).read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        rf"^def {func_name}\(.*?\n(?=def |@router|@|\nclass |\Z)",
        src, re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"未能在 {relpath} 找到 def {func_name}")
    ns = {
        "Session": _Sentinel, "Order": _Sentinel(), "User": _Sentinel(),
        "Inquiry": _Sentinel(), "UUID": uuid.UUID, "Any": object, "Optional": object,
        "error_response": lambda c, msg: {"code": c, "message": msg},
    }
    if extra_ns:
        ns.update(extra_ns)
    exec(m.group(0), ns)  # noqa: S102 — 被测对象是仓库内产品代码
    return ns[func_name], ns


# ---------- 被测的真实产品函数 ----------

def _tenant_member_user_ids(db, user):
    """可控桩：None=平台视角；否则返回该用户可见的成员 user_id 集合。"""
    links = getattr(user, "user_tenant_links", None)
    if links is None:
        return None
    return {str(user.id), *(str(getattr(l, "user_id", "")) for l in links)}


# 先加载 _resolve_caller_tenant_id（真实实现），再注入给 _check_inquiry_tenant_access
_resolve_real, _resolve_ns = _load_real_func(
    "app/api/v1/routes/inquiries.py", "_resolve_caller_tenant_id")
_check_inquiry_tenant_access, _ = _load_real_func(
    "app/api/v1/routes/inquiries.py", "_check_inquiry_tenant_access",
    {"_resolve_caller_tenant_id": _resolve_real})
get_order_for_user, _ = _load_real_func(
    "app/services/logistics_tracking_service.py", "get_order_for_user",
    {"tenant_member_user_ids": _tenant_member_user_ids})

from app.models.enums import OrderStatus, _ORDER_TRANSITIONS  # noqa: E402


# ---------- 构造工具 ----------

def _user(role="tenant_admin", tenant_id="T-A", uid="u-a", links=()):
    """links=() 普通租户成员；links=None 平台视角（tenant_member_user_ids→None）"""
    return SimpleNamespace(id=uid, role=role, tenant_id=tenant_id,
                           user_tenant_links=links)


def _inquiry(tenant_id):
    return SimpleNamespace(id=str(uuid.uuid4()), tenant_id=tenant_id, status="pending")


def _order(buyer_id, merchant_id):
    return SimpleNamespace(id=uuid.uuid4(), buyer_id=buyer_id,
                           merchant_id=merchant_id, tracking_number=None)


def _link(uid):
    return SimpleNamespace(user_id=uid)


class _FakeQuery:
    """最小 db.query(Model).filter(...).first() 桩，仅服务 get_order_for_user。"""
    def __init__(self, result):
        self._result = result

    def __call__(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def first(self):
        return self._result


@pytest.fixture
def fake_db():
    return SimpleNamespace(query=None)


def _status_of(res):
    if res is None:
        return None
    if isinstance(res, dict):
        return res.get("code", res.get("status_code", res.get("status")))
    return getattr(res, "code", getattr(res, "status_code", None))


# ============ §13 数据隔离：_check_inquiry_tenant_access 真实判定 ============

class TestInquiryTenantAccess:
    def test_cross_tenant_blocked_403(self):
        res = _check_inquiry_tenant_access(_inquiry("T-A"), None,
                                           _user("tenant_admin", "T-B", "u-b"))
        assert _status_of(res) == 403

    def test_same_tenant_allowed(self):
        assert _check_inquiry_tenant_access(_inquiry("T-A"), None,
                                            _user("tenant_admin", "T-A", "u-a")) is None

    def test_super_admin_allowed(self):
        assert _check_inquiry_tenant_access(_inquiry("T-B"), None,
                                            _user("super_admin", None, "root")) is None

    def test_caller_without_tenant_blocked(self):
        """调用者无租户归属而询盘有租户 → 403（真实逻辑第二分支）"""
        res = _check_inquiry_tenant_access(_inquiry("T-A"), None,
                                           _user("editor", None, "u-x"))
        assert _status_of(res) == 403


# ============ §13 订单越权：get_order_for_user 真实判定 ============

class TestOrderCrossTenant:
    def test_platform_view_sees_order(self, fake_db):
        order = _order("b1", "m1")
        fake_db.query = _FakeQuery(order)
        assert get_order_for_user(fake_db, order.id,
                                  _user("super_admin", None, "root", links=None)) is order

    def test_unrelated_tenant_gets_none(self, fake_db):
        order = _order("b1", "m1")
        fake_db.query = _FakeQuery(order)
        assert get_order_for_user(fake_db, order.id,
                                  _user("tenant_admin", "T-X", "u-x", links=[])) is None

    def test_merchant_member_can_access(self, fake_db):
        order = _order("b1", "m1")
        fake_db.query = _FakeQuery(order)
        assert get_order_for_user(fake_db, order.id,
                                  _user("tenant_admin", "T-M", "u-m", links=[_link("m1")])) is order

    def test_missing_order_returns_none(self, fake_db):
        fake_db.query = _FakeQuery(None)
        assert get_order_for_user(fake_db, uuid.uuid4(),
                                  _user("tenant_admin", "T-A", "u-a", links=None)) is None


# ============ §7 询盘状态：白名单必须覆盖前端实际取值 ============

class TestInquiryStatusWhitelist:
    """回归护栏：前端 inquiries/index.vue 的按钮会向 PUT /inquiries/{id}/status
    发送 quoted / accepted（展示层还识别 new / processing）。历史上后端白名单
    缺这几个值，导致点击必 400。此测试钉死"前端发的值 ⊆ 后端白名单"。"""

    _FRONTEND_USED = {"pending", "new", "quoted", "accepted", "processing"}

    def _load_whitelist(self):
        src = (_BK / "app/api/v1/routes/inquiries.py").read_text(
            encoding="utf-8", errors="ignore")
        m = re.search(
            r"_VALID_INQUIRY_STATUSES\s*=\s*frozenset\(\{(.*?)\}\)", src, re.S)
        assert m, "未找到 _VALID_INQUIRY_STATUSES 定义"
        return {s.strip().strip('"\'') for s in m.group(1).split(",") if s.strip()}

    def test_frontend_status_values_all_allowed(self):
        wl = self._load_whitelist()
        missing = self._FRONTEND_USED - wl
        assert not missing, f"后端白名单缺前端取值: {missing}"

    def test_whitelist_is_nonempty_subset_of_lowercase(self):
        wl = self._load_whitelist()
        assert wl
        assert all(s == s.lower() for s in wl), "白名单含非小写值，与 .lower() 校验冲突"


# ============ §7/§9 订单状态机：真实枚举 + 流转白名单 ============

class TestOrderStateMachine:
    def test_whitelist_transitions_are_valid(self):
        for fr, to in _ORDER_TRANSITIONS:
            assert OrderStatus.is_valid_transition(fr, to)

    def test_illegal_transition_rejected(self):
        assert not OrderStatus.is_valid_transition("draft", "completed")
        assert not OrderStatus.is_valid_transition("completed", "draft")

    def test_all_referenced_states_exist(self):
        valid = {s.value for s in OrderStatus}
        for fr, to in _ORDER_TRANSITIONS:
            assert fr in valid and to in valid, f"白名单引用了不存在的状态 {fr}->{to}"

    def test_valid_next_statuses_matches_whitelist(self):
        nxt = OrderStatus.valid_next_statuses("pending")
        assert set(nxt) == {to for f, to in _ORDER_TRANSITIONS if f == "pending"}
