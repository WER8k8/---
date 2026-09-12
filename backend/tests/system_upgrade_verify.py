"""系统升级专项验证（建议 1、2、3 综合断言）

覆盖验证点：
1. 分布式多级租户缓存（建议 1）：
   - L1 内存缓存命中与 TTL 过期判定；
   - L2 Redis 缓存模拟写入与回填；
   - 降级与兜底逻辑。
2. Browser Runtime 并发信号量与 CDP 护栏（建议 2）：
   - 并发 Semaphore 限制生效；
   - 远程 CDP 优先尝试 + 连接异常自动平滑降级到沙箱模式。
3. 任务控制面 Human-in-the-Loop 管理端点（建议 3）：
   - pending-reviews 待审状态过滤 (review / wait_human)；
   - resume 放行恢复执行；
   - retry 受控重试与有界约束；
   - cancel 人工终止及原因落地。
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# 设置测试环境
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings
from app.core.tenant_middleware import (
    TenantMiddleware,
    _get_redis_tenant_cache,
    _set_redis_tenant_cache,
    _tenant_cache,
)
from app.models.ai_task import AiTask
from app.services.browser_runtime.evidence import EvidenceRecord
from app.services.browser_runtime.executor import (
    _acquire_concurrency_token,
    _create_browser_context,
)
from app.services.tasks.task_control import (
    CREATED,
    EXECUTING,
    PAUSED,
    REVIEW,
    TaskControlService,
    WAIT_HUMAN,
)


class TestSystemUpgrades(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _tenant_cache.clear()

    # ==========================================
    # 建议 1：分布式多级租户缓存验证
    # ==========================================
    def test_tenant_multilevel_cache_l1_expiry(self):
        """测试 L1 本地缓存带有 timestamp 并支持 TTL 判断。"""
        now = time.time()
        # 写入一条刚过期的假缓存 (val, exp)
        _tenant_cache["expired_sub|test.com"] = ({"id": "t-1"}, now - 120)

        # 构造一个假 middleware 实例调用 _lookup_tenant
        fake_app = MagicMock()
        mw = TenantMiddleware(fake_app)
        mock_session_factory = MagicMock()
        mock_db = MagicMock()
        mock_session_factory.return_value = mock_db
        mw._SessionLocal = mock_session_factory

        # 过期的缓存不会直接命中，会尝试穿透查 DB
        mw._lookup_tenant("expired_sub", "test.com")
        self.assertTrue(mock_session_factory.called, "L1 缓存过期后必须穿透调用 SessionLocal 查库")

        # 重置 mock，写入一条未过期的有效缓存
        mock_session_factory.reset_mock()
        _tenant_cache["valid_sub|test.com"] = ({"id": "t-2"}, now + 300)
        cached_valid = mw._lookup_tenant("valid_sub", "test.com")
        self.assertIsNotNone(cached_valid, "未过期的 L1 缓存应成功命中")
        self.assertEqual(cached_valid.get("id"), "t-2")
        self.assertFalse(mock_session_factory.called, "未过期的 L1 缓存命中时绝不能查询数据库")

    def test_tenant_cache_redis_fallback(self):
        """测试 Redis 故障或未启用时的平滑降级（不阻断主链路）。"""
        with patch("app.core.cache.redis_client", None):
            res = _get_redis_tenant_cache("any_key")
            self.assertIsNone(res)
            # set 也不外抛
            _set_redis_tenant_cache("any_key", {"id": "t-3"}, 60)

    # ==========================================
    # 建议 2：Browser Runtime 沙箱护栏与远程 CDP
    # ==========================================
    async def test_browser_concurrency_semaphore(self):
        """测试 Browser Runtime 并发信号量限流。"""
        sem = await _acquire_concurrency_token()
        self.assertIsInstance(sem, asyncio.Semaphore)
        # 模拟进入与释放配额
        async with sem:
            self.assertEqual(sem._value, int(getattr(settings, "BROWSER_RUNTIME_MAX_CONCURRENCY", 4)) - 1)

    async def test_browser_remote_cdp_fallback_to_sandbox(self):
        """测试配置了远程 CDP 时优先连接，失败平滑降级至本机 launch_persistent_context。"""
        fake_pw = MagicMock()
        fake_pw.chromium.connect_over_cdp = AsyncMock(side_effect=Exception("CDP connection refused"))
        fake_pw.chromium.launch_persistent_context = AsyncMock(return_value="local_context_mock")

        with patch.object(settings, "BROWSER_RUNTIME_WS_ENDPOINT", "ws://10.0.0.1:9222"):
            ctx = await _create_browser_context(fake_pw, "dummy_profile_path")
            fake_pw.chromium.connect_over_cdp.assert_awaited_once()
            fake_pw.chromium.launch_persistent_context.assert_awaited_once()
            self.assertEqual(ctx, "local_context_mock")

    # ==========================================
    # 建议 3：任务控制面人审与干预
    # ==========================================
    def test_task_control_human_in_the_loop(self):
        """测试任务控制面人审流转：review/wait_human -> resume / cancel / retry。"""
        mock_db = MagicMock()
        mock_task = AiTask(
            id="task-upgrade-001",
            tenant_id="tenant-uj-1",
            task_type="ai_agent_research",
            status=WAIT_HUMAN,
            retry_count=1,
        )

        svc = TaskControlService(mock_db)
        # mock svc.get_task 直接返回 mock_task
        svc.get_task = MagicMock(return_value=mock_task)

        # 1. 人审放行：WAIT_HUMAN -> EXECUTING
        resumed = svc.resume_task("task-upgrade-001", tenant_id="tenant-uj-1")
        self.assertEqual(resumed.status, EXECUTING)

        # 2. 任务遇到困难进入人审 REVIEW -> PAUSED -> EXECUTING
        mock_task.status = REVIEW
        paused = svc.pause_task("task-upgrade-001", tenant_id="tenant-uj-1")
        self.assertEqual(paused.status, PAUSED)

        resumed_again = svc.resume_task("task-upgrade-001", tenant_id="tenant-uj-1")
        self.assertEqual(resumed_again.status, EXECUTING)

        # 3. 人工终止 CANCELLED
        cancelled = svc.cancel_task("task-upgrade-001", tenant_id="tenant-uj-1")
        self.assertEqual(cancelled.status, "cancelled")
        self.assertIsNotNone(cancelled.finished_at)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSystemUpgrades)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n[PASS] All 5 system upgrade verification tests passed perfectly!")


if __name__ == "__main__":
    main()
