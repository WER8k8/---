# -*- coding: utf-8 -*-
"""分发执行器「三分法」回归测试（不连真库，全部假发布服务）。

钉住 2026-09-10 实测结论：n4 分发节点此前恒失败，根因是平台目录压根没读到
（`backend/app/data/platforms.json` 不存在，旧 load_platforms 缺文件即返回 []），
于是 PublishService 对任何平台都回 "Platform config not found"，一条真实请求都没发出。
修好数据源后必须区分三种情况，谁也不许冒充谁：

    · 真发成功            → succeeded
    · 渠道未配置 / 未接入  → not_configured，节点 skipped（不发请求）
    · 配了但真发失败       → failed（error 必须带平台名和原因）

另钉两条护栏：
    · PublishService 必须拿到编排上下文的 db（否则又退回"自己乱开连接/读不到库"的老路）
    · 未接入的渠道不许真的去调 publish（省掉无意义的网络请求，也避免误报）
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from app.schemas.hermes_orchestration import ExecutorResult, TaskNode
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.publish_executor import PublishExecutor
from app.services.publish_capability_registry import (
    PLATFORM_NOT_CONFIGURED,
    PLATFORM_NOT_IMPLEMENTED,
)

# 库里 platforms 表的显示名 + 发布器键（真源是 DB，这里只是把测试打桩成同一形状）
_CATALOG = {
    "wechat": {"id": "wechat", "name": "微信公众号", "publisher_key": "wechat"},
    "zhihu": {"id": "zhihu", "name": "知乎", "publisher_key": "zhihu"},
    "facebook": {"id": "facebook", "name": "Facebook", "publisher_key": "facebook"},
    "linkedin": {"id": "linkedin", "name": "LinkedIn", "publisher_key": "linkedin"},
    "douyin": {"id": "douyin", "name": "抖音", "publisher_key": "douyin"},
}

# 每个渠道"真发一次会返回什么"——照真实 PublishService.publish 的返回形状写
_PUBLISH_OUTCOMES = {
    "wechat": {
        "status": "failed",
        "error_code": PLATFORM_NOT_CONFIGURED,
        "configured": False,
        "missing_credentials": ["appid", "appsecret"],
        "error_message": "微信公众号 渠道凭证未配置：appid, appsecret",
    },
    "zhihu": {
        "status": "failed",
        "error_code": PLATFORM_NOT_CONFIGURED,
        "configured": False,
        "missing_credentials": ["cookies"],
        "error_message": "知乎 渠道凭证未配置：cookies",
    },
    "facebook": {
        "status": "success",
        "platform_post_url": "https://www.facebook.com/youding/posts/1022334455",
    },
    "linkedin": {
        "status": "failed",
        "error_code": "API_ERROR",
        "error_message": "LinkedIn 返回 401，access_token 已过期",
    },
}


class _FakePublishService:
    """替身发布服务：记录构造时拿到的 db、实际被调用过的渠道。"""

    instances: list = []

    def __init__(self, db=None):
        self.db = db
        self.published: list = []
        _FakePublishService.instances.append(self)

    def find_platform_config(self, ref):
        return _CATALOG.get(str(ref or "").strip())

    async def publish(self, platform_id, content):
        self.published.append(platform_id)
        outcome = _PUBLISH_OUTCOMES.get(platform_id)
        if outcome is None:
            return {
                "status": "failed",
                "error_code": PLATFORM_NOT_CONFIGURED,
                "error_message": f"{platform_id} 不在平台目录",
            }
        return dict(outcome)


@pytest.fixture(autouse=True)
def _reset_fake():
    _FakePublishService.instances = []
    yield
    _FakePublishService.instances = []


def _run(channels, *, capability="publish.multi", db="FAKE_DB", extra=None):
    """跑一次分发执行器，返回 (result, 假服务实例)。

    实例为 None 表示执行器压根没构造发布服务（入参不足 / 能力不支持），
    这类提前返回的分支本身就是要断言的行为。
    """
    ctx = ExecutorContext(db=db, tenant_id="tenant-1", plan_id="plan-1")
    params = {"channels": channels, "title": "石英石台面", "body": "正文"}
    params.update(extra or {})
    node = TaskNode(
        id="n4", executor="publish", capability=capability, depends_on=[], input=params
    )
    with patch("app.services.publish_service.PublishService", _FakePublishService):
        result = asyncio.run(PublishExecutor().run(node, ctx))
    return result, (_FakePublishService.instances[-1] if _FakePublishService.instances else None)


def test_all_unconfigured_lands_skipped_not_failed():
    """全渠道未配置 → skipped：既不算成功，也不把整条链判死。"""
    result, svc = _run(["wechat", "douyin"])

    assert result.status == "skipped"
    assert result.error in (None, "")
    assert result.output["succeeded"] == 0
    assert result.output["failed"] == 0
    assert result.output["not_configured"] == 2
    detail = result.output["not_configured_detail"]
    assert detail["wechat"]["error_code"] == PLATFORM_NOT_CONFIGURED
    assert detail["douyin"]["error_code"] == PLATFORM_NOT_IMPLEMENTED
    # 一句话人话要说清"没发请求"，不许写成"发布失败"
    assert "未发起任何真实请求" in result.output["summary"]
    assert svc.published == ["wechat"]  # 抖音压根没接入，不配浪费一次调用


def test_unwired_channel_never_reaches_publisher():
    """未接入的渠道必须在预检就拦下，一次真实调用都不发。"""
    _result, svc = _run(["douyin"])

    assert svc.published == []
    assert _result.output["not_configured_detail"]["douyin"]["error_code"] == (
        PLATFORM_NOT_IMPLEMENTED
    )


def test_partial_success_is_reported_as_partial():
    """部分成功 → succeeded，但 partial=True，不许谎报"全部成功"。"""
    result, svc = _run(["facebook", "wechat"])

    assert result.status == "succeeded"
    assert result.output["succeeded"] == 1
    assert result.output["partial"] is True
    assert result.output["not_configured"] == 1
    assert result.output["summary"].startswith("1/2")
    assert svc.published == ["facebook", "wechat"]


def test_real_failure_carries_platform_reason():
    """配了但真发失败 → failed，error 必须带平台名和原因，不能只说"均失败"。"""
    result, _svc = _run(["linkedin"])

    assert result.status == "failed"
    assert result.output["failed"] == 1
    assert "LinkedIn" in result.error
    assert "401" in result.error


def test_mixed_failure_and_unconfigured_kept_separate():
    """真发失败与未配置要分开计数，未配置不混进失败原因里。"""
    result, _svc = _run(["facebook", "linkedin", "wechat"])

    assert result.status == "succeeded"  # 有真发成功即部分达成
    assert result.output["succeeded"] == 1
    assert result.output["failed"] == 1
    assert result.output["not_configured"] == 1
    assert "1 个渠道真发失败" in result.error
    assert "另有 1 个未配置" in result.error
    assert "401" in result.error
    assert "wechat" not in result.error.split("｜")[-1]


def test_missing_channels_and_content_fail_explicitly():
    """入参不足直接 failed，错误码用下划线前缀，方便机器判断。"""
    no_channels, _ = _run([])
    assert no_channels.status == "failed"
    assert no_channels.error.startswith("missing_channels")

    no_content, _ = _run(["wechat"], extra={"title": None, "body": None})
    assert no_content.status == "failed"
    assert no_content.error.startswith("missing_content")


def test_unsupported_capability_is_skipped():
    """声明外的能力不改语义去瞎执行，记 skipped 并说明原因。"""
    result, svc = _run(["facebook"], capability="publish.bogus")

    assert result.status == "skipped"
    assert "publish.bogus" in result.error
    # 连发布服务都不该被构造，更不该发出任何请求
    assert svc is None


def test_service_receives_context_db():
    """执行器必须把编排上下文的 db 交给发布服务（平台目录真源在库里）。"""
    sentinel = object()
    result, svc = _run(["facebook"], db=sentinel)

    assert svc.db is sentinel
    assert result.status == "succeeded"


def test_declared_capabilities_cover_new_output_fields():
    """能力声明里的产出字段要跟实际输出一致，下游 input_from 才不会取空。"""
    declared = PublishExecutor.get_capabilities()["publish.multi"]["output"]

    for field in ("results", "succeeded", "failed", "not_configured", "summary"):
        assert field in declared, f"能力声明缺产出字段 {field}"


def test_result_status_values_are_contract_legal():
    """执行器只能返回契约允许的 status，越界会让状态机白死。"""
    legal = {"succeeded", "failed", "skipped", "degraded", "aborted"}

    for channels in (["facebook"], ["wechat"], ["douyin"], ["linkedin"]):
        result, _ = _run(channels)
        assert isinstance(result, ExecutorResult)
        assert result.status in legal
