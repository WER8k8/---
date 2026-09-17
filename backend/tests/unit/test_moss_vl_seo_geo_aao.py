"""SEO / GEO / AAO 排名优化引擎与 MOSS-VL 联动单元测试。"""

import unittest
from pathlib import Path

from app.services.video_seo_geo_aao_optimizer import VideoSeoGeoAaoOptimizer
from app.services.moss_auto_clip_pipeline import MossAutoClipPipeline
from app.services.moss_clip_and_publish_workflow import MossClipAndPublishWorkflow


class TestMossVlSeoGeoAao(unittest.TestCase):

    def setUp(self):
        self.optimizer = VideoSeoGeoAaoOptimizer()
        self.pipeline = MossAutoClipPipeline()
        self.workflow = MossClipAndPublishWorkflow()

    def test_seo_metadata_generation(self):
        """测试 SEO 关键词与 VideoObject Schema JSON-LD 生成。"""
        pack = self.optimizer.generate_ranking_pack(
            clip_id="clip_001",
            title="颠覆性黑科技实测",
            start_sec=10.0,
            end_sec=40.0,
            visual_summary="高精度演示镜头",
            ocr_texts=["精准激光雕刻", "微米级误差"],
        )
        self.assertIn("精准激光雕刻评测", pack.seo.keywords)
        jsonld = pack.seo.video_object_jsonld
        self.assertEqual(jsonld["@type"], "VideoObject")
        self.assertIn("hasPart", jsonld)
        self.assertGreater(len(jsonld["hasPart"]), 0)
        # 验证 Key Moments
        first_clip = jsonld["hasPart"][0]
        self.assertEqual(first_clip["@type"], "Clip")

    def test_geo_generative_ai_optimization(self):
        """测试针对 AI 搜索（SearchGPT/Perplexity）的 GEO 事实密集型摘要与实体。"""
        pack = self.optimizer.generate_ranking_pack(
            clip_id="clip_002",
            title="出海带货破局关键",
            start_sec=0.0,
            end_sec=25.0,
            visual_summary="产品开箱测试",
            ocr_texts=["CE认证", "防水防尘IP68"],
        )
        self.assertIn("事实实测", pack.geo.fact_dense_summary)
        self.assertIn("防水防尘IP68", pack.geo.key_entities)
        self.assertGreater(len(pack.geo.target_ai_prompts), 0)

    def test_aao_answer_and_algorithm_optimization(self):
        """测试 AAO 问答对与平台置顶评论互动模版。"""
        pack = self.optimizer.generate_ranking_pack(
            clip_id="clip_003",
            title="3秒学会这个技巧",
            start_sec=5.0,
            end_sec=35.0,
            visual_summary="快速上手流程",
            ocr_texts=["智能一键配网"],
        )
        self.assertGreater(len(pack.aao.faq_pairs), 0)
        self.assertTrue(pack.aao.faq_pairs[0]["question"].startswith("Q:"))
        self.assertIn("【作者置顶·互动答疑】", pack.aao.pinned_comment_template)

    def test_pipeline_with_ranking_pack(self):
        """测试自动剪辑流水线产物包含 JSON-LD 和排名优化数据。"""
        result = self.pipeline.execute_auto_clip_pipeline(
            video_path_or_url="test_ranking.mp4",
            video_duration_sec=60.0,
            target_aspect_ratio="9:16",
        )
        self.assertEqual(result["status"], "success")
        first_clip = result["clips"][0]
        self.assertIn("ranking_pack", first_clip)
        self.assertIn("seo", first_clip["ranking_pack"])
        self.assertIn("geo", first_clip["ranking_pack"])
        self.assertIn("aao", first_clip["ranking_pack"])
        
        # 验证 jsonld 文件已生成
        jsonld_file = Path(first_clip["jsonld_path"])
        self.assertTrue(jsonld_file.exists())
        self.assertIn("VideoObject", jsonld_file.read_text(encoding="utf-8"))

    def test_clip_publish_workflow_enhancement(self):
        """测试一键分发工作流自动携带置顶评论、SEO词和GEO摘要。"""
        wf = self.workflow.run_clip_and_publish_workflow(
            video_path_or_url="test_publish.mp4",
            target_platforms=["douyin", "xhs", "tiktok", "youtube"],
            video_duration_sec=70.0,
            auto_dispatch=True,
        )
        self.assertTrue(wf["ranking_enhancement_active"])
        first_task = wf["dispatched_tasks"][0]
        self.assertIn("pinned_comment", first_task)
        self.assertIn("seo_keywords", first_task)
        self.assertIn("geo_summary", first_task)
        self.assertGreater(len(first_task["seo_keywords"]), 0)


if __name__ == "__main__":
    unittest.main()
