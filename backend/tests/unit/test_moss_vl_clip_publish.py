"""MOSS-VL AI 智能剪辑与一键分发单元测试。"""

import unittest
from pathlib import Path
from app.services.moss_vl_service import MossVLService, HighlightClipCandidate
from app.services.moss_auto_clip_pipeline import MossAutoClipPipeline
from app.services.moss_clip_and_publish_workflow import MossClipAndPublishWorkflow
from app.api.v1.routes.moss_vl_clip_publish import (
    analyze_video,
    auto_clip,
    clip_and_publish,
    MossAnalyzeRequest,
    MossAutoClipRequest,
    MossClipAndPublishRequest,
)


class TestMossVLClipPublish(unittest.TestCase):

    def setUp(self):
        self.moss_service = MossVLService()
        self.pipeline = MossAutoClipPipeline(moss_service=self.moss_service)
        self.workflow = MossClipAndPublishWorkflow(
            clip_pipeline=self.pipeline,
            moss_service=self.moss_service,
        )

    def test_spatiotemporal_analysis(self):
        """测试 MOSS-VL 时空多模态视频解析与分镜划分。"""
        res = self.moss_service.analyze_video_spatiotemporal("test_sample.mp4", duration_sec=100.0)
        self.assertIn("MOSS-VL", res["model"])
        self.assertGreater(len(res["scenes"]), 0)
        self.assertIn("highlight_score", res["scenes"][0])

    def test_highlight_detection(self):
        """测试高光候选切片识别。"""
        analysis = self.moss_service.analyze_video_spatiotemporal("test_sample.mp4", duration_sec=120.0)
        candidates = self.moss_service.detect_highlights_and_clips(analysis, min_clip_duration=15.0, max_clip_duration=60.0)
        self.assertGreater(len(candidates), 0)
        first = candidates[0]
        self.assertIsInstance(first, HighlightClipCandidate)
        self.assertGreaterEqual(first.duration, 15.0)

    def test_visual_grounded_subtitles(self):
        """测试画文融合精准视译。"""
        subtitles = [
            {"start_sec": 5.0, "end_sec": 10.0, "text": "欢迎观看这个产品亮点演示"},
        ]
        scenes = [
            {"start_sec": 0.0, "end_sec": 15.0, "ocr_texts": ["PRO-SERIES"], "visual_summary": "操作特写"},
        ]
        items = self.moss_service.translate_with_visual_grounding(subtitles, scenes, target_languages=["en", "es"])
        self.assertEqual(len(items), 1)
        self.assertIn("en", items[0].translations)
        self.assertIn("es", items[0].translations)

    def test_platform_copywriting_generation(self):
        """测试针对抖音、小红书、TikTok、YouTube 的定制文案生成。"""
        candidate = HighlightClipCandidate(
            clip_id="clip_001",
            start_sec=10.0,
            end_sec=35.0,
            duration=25.0,
            score=0.92,
            reason="视觉冲突剧烈",
            hook_sentence="3秒看懂核心功能！",
            tags=["黑科技", "好物分享"],
        )
        platforms = ["douyin", "xhs", "tiktok", "youtube"]
        meta = self.moss_service.generate_platform_copywriting(candidate, platforms)
        self.assertIn("douyin", meta)
        self.assertIn("tiktok", meta)
        self.assertIn("#Shorts", meta["youtube"]["title"])

    def test_auto_clip_pipeline_execution(self):
        """测试自动剪辑流水线产物与元数据。"""
        res = self.pipeline.execute_auto_clip_pipeline(
            video_path_or_url="test_demo.mp4",
            video_duration_sec=90.0,
            target_aspect_ratio="9:16",
        )
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["clips_count"], 0)
        first_clip = res["clips"][0]
        self.assertEqual(first_clip["aspect_ratio"], "9:16")
        self.assertTrue(Path(first_clip["subtitle_srt_path"]).exists())

    def test_clip_and_publish_workflow(self):
        """测试端到端自动剪辑并推送一键分发队列。"""
        wf_res = self.workflow.run_clip_and_publish_workflow(
            video_path_or_url="full_product_review.mp4",
            target_platforms=["douyin", "xhs", "tiktok"],
            tenant_id="tenant_888",
            video_duration_sec=80.0,
            auto_dispatch=True,
        )
        self.assertEqual(wf_res["status"], "completed")
        self.assertEqual(wf_res["tenant_id"], "tenant_888")
        self.assertGreater(len(wf_res["dispatched_tasks"]), 0)
        # 每个切片分发到 3 个平台
        self.assertEqual(
            len(wf_res["dispatched_tasks"]),
            wf_res["total_clips_generated"] * 3
        )

    def test_api_routes(self):
        """测试 FastAPI 路由契约。"""
        # 1. analyze
        res1 = analyze_video(MossAnalyzeRequest(video_source="test.mp4", duration_sec=60.0))
        self.assertEqual(res1["code"], 0)
        self.assertIn("scenes", res1["data"])

        # 2. auto-clip
        res2 = auto_clip(MossAutoClipRequest(video_source="test.mp4", duration_sec=60.0))
        self.assertEqual(res2["code"], 0)
        self.assertGreater(res2["data"]["clips_count"], 0)

        # 3. clip-and-publish
        res3 = clip_and_publish(MossClipAndPublishRequest(video_source="test.mp4", duration_sec=60.0))
        self.assertEqual(res3["code"], 0)
        self.assertIn("dispatched_tasks", res3["data"])


if __name__ == "__main__":
    unittest.main()
