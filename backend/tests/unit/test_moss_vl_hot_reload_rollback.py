"""MOSS-VL 官方追踪、热更新与回滚单元测试套件。"""

import unittest
from app.services.moss_vl.hot_reload_manager import MossHotReloadManager
from app.services.moss_vl_service import MossVLService
from app.api.v1.routes.moss_vl_clip_publish import (
    get_version_status,
    check_upstream,
    hot_reload_model,
    rollback_model,
    get_version_history,
    MossHotReloadRequest,
    MossRollbackRequest,
)


class TestMossVLHotReloadRollback(unittest.TestCase):

    def setUp(self):
        self.manager = MossHotReloadManager()
        self.service = MossVLService()

    def test_check_upstream_updates(self):
        """测试官方仓库上游更新探测。"""
        res = self.manager.check_upstream_updates()
        self.assertIn("upstream_repo", res)
        self.assertIn("github.com/OpenMOSS/MOSS-VL", res["upstream_repo"])
        self.assertIn("has_update", res)

    def test_hot_reload_zero_downtime_swap(self):
        """测试双缓冲影子实例与原子指针切换。"""
        orig_version = self.manager.current_instance.snapshot.version_id

        # 触发热更新
        res = self.manager.hot_reload(
            new_commit_hash="a1b2c3d4",
            new_release_tag="v1.1.0",
            quantization="fp8",
        )
        self.assertTrue(res["success"])
        new_version = res["active_version"]
        self.assertNotEqual(orig_version, new_version)

        # 验证 service 门面动态感知最新版本
        analysis = self.service.analyze_video_spatiotemporal("test.mp4", duration_sec=60.0)
        self.assertEqual(analysis["version_id"], new_version)
        self.assertEqual(analysis["commit_hash"], "a1b2c3d4")

    def test_hot_reload_self_test_failure_guard(self):
        """测试影子实例探针自检失败时的熔断保护（不中断当前服务）。"""
        current_active = self.manager.current_instance.snapshot.version_id

        # 强制注入探针失败
        res = self.manager.hot_reload(
            new_commit_hash="bad_commit",
            new_release_tag="v9.9.9",
            force_fail_self_test=True,
        )
        self.assertFalse(res["success"])
        self.assertIn("自动阻断", res["msg"])

        # 确保当前系统版本未受影响
        self.assertEqual(self.manager.current_instance.snapshot.version_id, current_active)

    def test_instant_rollback(self):
        """测试一键秒级回滚到历史健康快照。"""
        # 先热更新一个版本
        self.manager.hot_reload(new_commit_hash="commit_to_rollback", new_release_tag="v2.0.0")
        target_version = self.manager.current_instance.snapshot.version_id

        # 执行回滚
        rb_res = self.manager.rollback_to_version()
        self.assertTrue(rb_res["success"])
        self.assertNotEqual(self.manager.current_instance.snapshot.version_id, target_version)

    def test_management_api_routes(self):
        """测试 FastAPI 热更新与回滚管控路由契约。"""
        # 1. status
        status = get_version_status()
        self.assertEqual(status["code"], 0)
        self.assertTrue(status["data"]["is_zero_downtime_active"])

        # 2. check-upstream
        up = check_upstream()
        self.assertEqual(up["code"], 0)

        # 3. hot-reload api
        hr_api = hot_reload_model(MossHotReloadRequest(commit_hash="api_commit", release_tag="v3.0.0"))
        self.assertEqual(hr_api["code"], 0)

        # 4. rollback api
        rb_api = rollback_model(MossRollbackRequest())
        self.assertEqual(rb_api["code"], 0)

        # 5. history
        hist = get_version_history()
        self.assertEqual(hist["code"], 0)
        self.assertGreater(len(hist["data"]), 1)


if __name__ == "__main__":
    unittest.main()
