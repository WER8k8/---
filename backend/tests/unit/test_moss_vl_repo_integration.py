"""MOSS-VL 官方整仓物理集成与联动测试套件。"""

import unittest
from pathlib import Path
from app.services.moss_vl.repo_syncer import MossRepoSyncer
from app.services.moss_vl.offline_inference import OfflineInferenceEngine
from app.api.v1.routes.moss_vl_clip_publish import get_repo_status


class TestMossVLRepoIntegration(unittest.TestCase):

    def setUp(self):
        self.syncer = MossRepoSyncer()
        self.engine = OfflineInferenceEngine()

    def test_repo_presence_and_structure(self):
        """验证官方整仓目录、子模块及核心推理脚本已物理存在。"""
        self.assertTrue(self.syncer.is_repo_present(), "MOSS-VL 官方整仓未能在本地检测到")
        report = self.syncer.get_repo_inspection_report()
        self.assertTrue(report["installed"])
        self.assertTrue(report["has_offline_inference_script"])
        self.assertTrue(report["has_online_realtime_script"])
        self.assertTrue(report["has_requirements_txt"])
        self.assertGreater(report["total_items_count"], 50)
        self.assertGreater(report["python_source_files_count"], 10)

    def test_sys_path_injection(self):
        """验证官方整仓目录已被注入系统 sys.path。"""
        injected = self.syncer.ensure_repo_in_sys_path()
        self.assertIsInstance(injected, list)
        report = self.syncer.get_repo_inspection_report()
        self.assertTrue(report["sys_path_injected"])

    def test_official_script_path_binding(self):
        """验证离线推理引擎成功绑定官方 run_inference.py 脚本。"""
        script_path = self.engine.get_official_script_path()
        self.assertIsNotNone(script_path)
        self.assertTrue(script_path.is_file())
        self.assertEqual(script_path.name, "run_inference.py")

    def test_repo_status_api(self):
        """验证 FastAPI 官方整仓状态诊断路由返回合规数据。"""
        res = get_repo_status()
        self.assertEqual(res["code"], 0)
        data = res["data"]
        self.assertTrue(data["installed"])
        self.assertIn("inference", data["core_subdirectories"])
        self.assertTrue(data["core_subdirectories"]["inference"])


if __name__ == "__main__":
    unittest.main()
