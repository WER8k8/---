# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199304817). All rights reserved.
"""批次14 回归锁 —— platform.py 14 个停用端点「死调用 → 诚实 501」守卫。

四道锁：

1. **通用 AST 守卫**：解析 `routes/platform.py`，抽出**所有** `service.<X>(...)` 调用
   （`service` 即 `PublishService` 实例），断言每个 `X ∈ dir(PublishService)`。
   未来任何人新增调用而方法不存在 → 直接红。
1b. **元测试（防 vacuous truth）**：喂合成坏源码（含 `service.totally_fake()` /
   `service.publish_content()`），断言守卫解析器检出的坏调用集合**非空**且包含这两个名字。
   否则当真实文件 `service.<X>()` 数为 0 时守卫会恒真、失去意义。
2. **功能守卫**：进程内 TestClient 逐一请求 **14 个**端点，断言 HTTP **501**（非 500 / 非 200）。
3. **形状一致性守卫**：断言 14 个 501 body **完全同形**——
   `{"code": 501, "message": <str>, "data": {"reason": "<xxx>_unsupported"}}`，
   防前端出现两套解析分支。
4. retry 端点断言「未发生 mutation + commit」（防任务卡死）；缺任务仍 404。

设计说明：最小 FastAPI() 挂 router（避免拉起 app.main 全量依赖），覆盖
get_db / get_current_user；不启动任何长驻服务。
"""
from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_ROUTE = BACKEND_ROOT / "app" / "api" / "v1" / "routes" / "platform.py"

# 已于模块5 M1 阶段二（2026-09-28）实装并从本集合移出：
#   publish_content / batch_publish / schedule_publish / get_publish_tasks /
#   _execute_publish_tasks —— 对应 5 个发布面端点已由 501 **回退为真实调用**。
# 已于模块5 M6（2026-09-28）实装并从本集合移出：
#   connect_platform / disconnect_platform / list_accounts / check_session /
#   get_publish_logs / get_publish_stats —— 凭据面 6 端点已回退为真实调用
#   （docs/模块5-凭据面收口契约-2026-09-28.md；配对反证见 test_platform_credential_face.py）。
# 本集合**只保留仍处于 501 的方法**：一旦其中任一被实装，本用例会立刻失败并提示
# 「501 应回退为真实实现」——这正是它作为门禁的职责（不要靠改断言绕过）。
HISTORIC_DEAD_METHODS = {
    # 平台侧会话能力（refresh / relogin / keepalive）—— 依赖 Browser Runtime，保持诚实 501
    "refresh_session", "auto_relogin", "keepalive_checker",
}

REAL_MEMBERS_EXPECTED = {"find_platform_config", "publish", "validate_platform_credentials"}

BASE = "/api/v1/platforms"
EXPECTED_TOP_KEYS = {"code", "message", "data"}


# ---------------- 守卫解析器（供锁①与元测试共用） ----------------

def _service_calls_from_source(src: str):
    """从任意源码字符串抽出 `service.<X>(...)` 调用 → [(attr, lineno), ...]。"""
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "service"
        ):
            hits.append((node.func.attr, node.lineno))
    return hits


def _service_calls():
    return _service_calls_from_source(PLATFORM_ROUTE.read_text(encoding="utf-8"))


def _detect_bad_service_calls(src: str, members: set):
    """返回源码中「调用了不存在成员」的 (attr, lineno) 列表。"""
    return [(a, ln) for a, ln in _service_calls_from_source(src) if a not in members]


def _client(db, user) -> TestClient:
    from app.api.v1.routes.platform import router
    from app.core.security import get_current_user
    from app.db.session import get_db

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def db_mock():
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = SimpleNamespace(
        id="task-1", status="failed", retry_count=0
    )
    return db


@pytest.fixture
def admin_user():
    return SimpleNamespace(id="u-admin", role="super_admin")


# ---------------- 锁①：通用 AST 守卫 + 元测试 ----------------

class TestGenericServiceCallGuard:
    def test_every_service_call_exists_on_publish_service(self):
        from app.services.publish_service import PublishService

        offenders = _detect_bad_service_calls(
            PLATFORM_ROUTE.read_text(encoding="utf-8"), set(dir(PublishService))
        )
        assert offenders == [], f"platform.py 调用了 PublishService 不存在的方法：{offenders}"

    def test_meta_guard_is_not_vacuous(self):
        """元测试：守卫解析器对合成坏源码必须检出非空且含两个已知坏名（防空真）。"""
        from app.services.publish_service import PublishService

        synthetic = textwrap.dedent(
            '''
            def _f(db):
                service = PublishService(db)
                service.publish(a=1)                  # 真方法，应不报
                service.publish_content(x=1)          # M1 阶段二已实装，应不报
                service.publish_content_legacy(x=1)   # 死方法，应报
                service.totally_fake(z=2)             # 死方法，应报
            '''
        )
        bad = _detect_bad_service_calls(synthetic, set(dir(PublishService)))
        assert bad, "守卫解析器对合成坏源码检出为空 → 守卫空转（vacuous truth）"
        names = {a for a, _ in bad}
        assert {"publish_content_legacy", "totally_fake"} <= names, bad
        assert "publish" not in names, "真方法不得被误报"
        assert "publish_content" not in names, "已实装方法不得被误报为死方法"

    def test_publish_service_real_members(self):
        from app.services.publish_service import PublishService

        assert REAL_MEMBERS_EXPECTED.issubset(set(dir(PublishService)))

    def test_historic_dead_methods_are_really_absent(self):
        from app.services.publish_service import PublishService

        members = set(dir(PublishService))
        still = sorted(m for m in HISTORIC_DEAD_METHODS if m in members)
        assert still == [], f"这些方法已真实存在，501 应回退为真实实现：{still}"


# ---------------- 锁②：14 端点 → 501（同形） ----------------

CASES = [
    # ⚠ 发布面 5 个端点已于 M1 阶段二（2026-09-28）**回退为真实调用**，不再返 501，
    #   故从本 501 集合移出：/publish、/publish/batch、/publish/schedule、
    #   /publish/tasks、/publish/tasks/{id}/retry。
    #   其真实行为由 tests/unit/test_publish_service_m1.py（配对反证）覆盖。
    # ⚠ 凭据面 6 个端点已于 M6（2026-09-28）**回退为真实调用**：
    #   /{id}/connect、/{id}/disconnect、/accounts、/accounts/{id}/check、
    #   /publish/logs、/stats —— 真实行为由 test_platform_credential_face.py 覆盖。
    # 平台侧会话能力（任务A 余量）—— 仍为诚实 501（共 3 个）
    ("post", f"{BASE}/accounts/a1/refresh", {}),
    ("post", f"{BASE}/accounts/a1/relogin", {}),
    ("post", f"{BASE}/keepalive", {}),
]
IDS = [c[1].split("/platforms/")[1] or "(root)" for c in CASES]


class TestDeadEndpointsReturn501:
    @pytest.mark.parametrize("method,path,kwargs", CASES, ids=IDS)
    def test_endpoint_501_uniform_shape(self, db_mock, admin_user, method, path, kwargs):
        resp = getattr(_client(db_mock, admin_user), method)(path, **kwargs)
        assert resp.status_code == 501, resp.text
        assert resp.status_code not in (200, 500)
        body = resp.json()
        assert set(body.keys()) == EXPECTED_TOP_KEYS, body          # 外层同形
        assert body["code"] == 501, body
        assert isinstance(body["message"], str) and body["message"], body
        assert set(body["data"].keys()) == {"reason"}, body          # data 内层同形
        assert body["data"]["reason"].endswith("_unsupported"), body

    def test_all_501_bodies_have_identical_shape(self, db_mock, admin_user):
        """锁③：仍在 501 的各端点 body 键结构必须完全一致（防前端两套解析分支）。

        注：发布面 5 个（M1）+ 凭据面 6 个（M6）已回退为真实调用，
        本集合现为平台侧会话能力 3 个。
        """
        client = _client(db_mock, admin_user)
        shapes = set()
        reasons = []
        for method, path, kwargs in CASES:
            resp = getattr(client, method)(path, **kwargs)
            assert resp.status_code == 501, resp.text
            body = resp.json()
            shapes.add(
                (
                    tuple(sorted(body.keys())),
                    tuple(sorted(body["data"].keys())),
                )
            )
            reasons.append(body["data"]["reason"])
        assert len(shapes) == 1, f"14 端点 501 形状不一致：{shapes}"
        assert len(set(reasons)) == len(reasons), f"reason 应互异：{reasons}"

    def test_retry_mutates_per_contract(self, db_mock, admin_user):
        """契约 §3.5：M1 实装后 retry **必须**先置 pending、retry_count+1 并 commit，
        再触发执行机。

        旧断言「不 mutate」是 501 止血期的临时语义（怕置 pending 后永不执行而卡死）；
        方法实装后该风险消除，语义**反转**为「按契约 mutate」。
        """
        task = db_mock.query.return_value.filter_by.return_value.first.return_value
        task.retry_count = 2
        resp = _client(db_mock, admin_user).post(f"{BASE}/publish/tasks/task-1/retry")
        assert resp.status_code == 200, resp.text
        assert task.status == "pending", "契约 §3.5：retry 须把任务置回 pending"
        assert task.retry_count == 3, "契约 §3.5：retry_count 须 +1"
        db_mock.commit.assert_called()

    def test_retry_missing_task_returns_404(self, admin_user):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        resp = _client(db, admin_user).post(f"{BASE}/publish/tasks/no-such/retry")
        assert resp.status_code == 404
