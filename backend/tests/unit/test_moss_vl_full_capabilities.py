"""MOSS-VL 官方开源完整能力深度测试套件。"""

import unittest
from app.services.moss_vl.xrope_spatial_temporal import XRoPEEmbedding, SpatiotemporalCoordinate
from app.services.moss_vl.realtime_session import create_realtime_session, MossRealtimeSession
from app.services.moss_vl.offline_inference import OfflineInferenceEngine
from app.services.moss_vl.model_loader import MossVLModelLoader
from app.services.moss_vl.repo_syncer import MossRepoSyncer
from app.services.moss_vl_service import MossVLService


class TestMossVLFullCapabilities(unittest.TestCase):

    def setUp(self):
        self.service = MossVLService()

    def test_xrope_spatiotemporal_embedding(self):
        """验证官方 XRoPE 三维时空位置编码器数学计算与时序交并比。"""
        xrope = XRoPEEmbedding(dim=64)
        coord = SpatiotemporalCoordinate(t=12.5, h=0.3, w=0.7)
        res = xrope.encode_coordinate(coord)
        self.assertEqual(res["total_dim"], 64)
        self.assertGreater(res["phase_t_norm"], 0)

        # 验证 Temporal IoU
        iou = xrope.compute_temporal_iou((10.0, 20.0), (15.0, 25.0))
        self.assertEqual(iou, 0.3333)

    def test_realtime_streaming_session_lifecycle(self):
        """验证官方对标 MOSS-VL-Realtime 实时视频流推送与交互。"""
        session = create_realtime_session("test_stream_001")
        self.assertIsInstance(session, MossRealtimeSession)

        # 推入视频帧
        for idx in range(15):
            session.push_frame(f"frame_binary_{idx}", timestamp=idx * 0.1)

        stats = session.get_session_stats()
        self.assertEqual(stats["buffered_frames"], 15)
        self.assertTrue(stats["xrope_active"])

        # 实时提问
        session.push_prompt("画面中是否出现产品正面？")
        outputs = list(session.stream_outputs())
        self.assertGreater(len(outputs), 0)
        self.assertIn("视觉", outputs[0].content)

    def test_offline_dense_video_grounding(self):
        """验证官方离线密集事件定位引擎。"""
        engine = OfflineInferenceEngine()
        events = engine.run_dense_video_grounding("sample.mp4", total_duration=80.0)
        self.assertEqual(len(events), 4)
        self.assertGreater(events[0].importance_score, 0.5)

        # 批处理
        batch_out = engine.batch_process([{"video_path": "demo.mp4", "prompt": "测试"}])
        self.assertEqual(len(batch_out), 1)
        self.assertEqual(batch_out[0]["events_count"], 4)

    def test_official_model_loader_and_quantization(self):
        """验证官方权重源映射与量化模式。"""
        loader = MossVLModelLoader(
            model_name_or_path="OpenMOSS-Team/MOSS-VL-Realtime",
            quantization="fp8",
            source="modelscope",
        )
        pipe = loader.load_pipeline()
        self.assertEqual(pipe["status"], "ready")
        self.assertEqual(pipe["quantization"], "fp8")
        self.assertIn("modelscope.cn", pipe["repo_url"])

    def test_repo_syncer_git_integration(self):
        """验证官方开源仓库 Git 自动化同步器检测。"""
        syncer = MossRepoSyncer()
        self.assertEqual(syncer.OFFICIAL_REPO_URL, "https://github.com/OpenMOSS/MOSS-VL.git")
        # 检测 git 是否在环境可用
        git_ok = syncer.check_git_installed()
        self.assertIsInstance(git_ok, bool)

    def test_moss_service_facade_integration(self):
        """验证统一门面服务调度全套官方架构。"""
        analysis = self.service.analyze_video_spatiotemporal("factory_inspection.mp4", duration_sec=100.0)
        self.assertEqual(analysis["engine"], "OpenMOSS_Official_Full_Architecture")
        self.assertTrue(analysis["xrope_active"])
        self.assertGreater(analysis["scenes_count"], 0)

        # 创建实时会话
        rt = self.service.create_realtime_session()
        self.assertIsNotNone(rt)


if __name__ == "__main__":
    unittest.main()
