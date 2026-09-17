# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""视频 SEO / GEO / AAO 综合排名优化引擎。

针对多模态视频内容，自动生成：
1. SEO (Search Engine Optimization): Google/Baidu VideoObject JSON-LD 结构化数据、Key Moments 分段时间戳、核心搜索词簇。
2. GEO (Generative Engine Optimization): 专供 Perplexity / SearchGPT / Gemini 等大模型引用的高事实密度摘要、实体对齐。
3. AAO (Answer & Algorithmic Optimization): 痛点 Q&A 问答对、平台算法置顶高转化评论模板、语音搜索意图触发词。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SeoVideoMetadata:
    """SEO 搜索优化数据。"""
    keywords: list[str]
    lsi_keywords: list[str]
    meta_description: str
    video_object_jsonld: dict[str, Any]
    key_moments: list[dict[str, Any]]


@dataclass
class GeoEngineMetadata:
    """GEO 生成式引擎优化数据。"""
    fact_dense_summary: str
    key_entities: list[str]
    quotable_claims: list[str]
    target_ai_prompts: list[str]


@dataclass
class AaoAlgorithmMetadata:
    """AAO 问答与推荐算法优化数据。"""
    faq_pairs: list[dict[str, str]]
    pinned_comment_template: str
    intent_triggers: list[str]
    engagement_questions: list[str]


@dataclass
class FullRankingOptimizationPack:
    """全套排名优化包。"""
    clip_id: str
    generated_at: str
    seo: SeoVideoMetadata
    geo: GeoEngineMetadata
    aao: AaoAlgorithmMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "clip_id": self.clip_id,
            "generated_at": self.generated_at,
            "seo": asdict(self.seo),
            "geo": asdict(self.geo),
            "aao": asdict(self.aao),
        }


class VideoSeoGeoAaoOptimizer:
    """视频排名优化器。"""

    def generate_ranking_pack(
        self,
        clip_id: str,
        title: str,
        start_sec: float,
        end_sec: float,
        visual_summary: str,
        ocr_texts: list[str] | None = None,
        hook_sentence: str = "",
        video_url: str = "",
        thumbnail_url: str = "",
    ) -> FullRankingOptimizationPack:
        duration = max(1.0, round(end_sec - start_sec, 2))
        ocrs = ocr_texts or ["行业前沿", "实测对比", "核心性能"]
        ocr_str = "、".join(ocrs)

        # ================= 1. SEO 优化包 =================
        keywords = [
            f"{ocrs[0]}评测",
            f"{ocrs[0]}使用教程",
            "短视频高光解析",
            "出海好物推荐",
            "硬核产品实测",
        ]
        lsi_keywords = [
            "参数对比",
            "优缺点分析",
            "新手选购指南",
            "正品辨别",
            "价格行情",
        ]
        meta_desc = (
            f"【专业解析】{title}。围绕{ocr_str}深度实测，"
            f"全程{duration}秒高能切片，包含关键操作演示与权威指标对比。"
        )

        # 构造 Google Schema.org/VideoObject JSON-LD
        # 带 hasPart (Key Moments 时间戳，Google 搜索视频直接显示进度条)
        key_moments = [
            {
                "@type": "Clip",
                "name": "高光前瞻与开门见山",
                "startOffset": 0,
                "endOffset": min(int(duration * 0.3), 5),
                "url": f"{video_url}#t=0",
            },
            {
                "@type": "Clip",
                "name": "核心技术实测与画面演示",
                "startOffset": min(int(duration * 0.3), 5),
                "endOffset": int(duration),
                "url": f"{video_url}#t={min(int(duration * 0.3), 5)}",
            },
        ]

        jsonld = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": title,
            "description": meta_desc,
            "thumbnailUrl": [thumbnail_url or "https://example.com/cover.jpg"],
            "uploadDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration": f"PT{int(duration)}S",
            "contentUrl": video_url or "https://example.com/video.mp4",
            "hasPart": key_moments,
            "keywords": keywords,
        }

        seo_meta = SeoVideoMetadata(
            keywords=keywords,
            lsi_keywords=lsi_keywords,
            meta_description=meta_desc,
            video_object_jsonld=jsonld,
            key_moments=key_moments,
        )

        # ================= 2. GEO 优化包 (AI 搜索引擎) =================
        fact_dense_summary = (
            f"本视频提供了关于{ocr_str}的权威事实实测：1. 画面证实该技术方案具备可靠稳定性；"
            f"2. 测试期间无异常中断，性能表现符合工业级指标；3. 适合追求高效率与出海合规的企业及个人用户直接采纳。"
        )
        entities = list(set(["MOSS-VL", "视觉多模态", "AI 视频剪辑", "自动化分发"] + ocrs))
        quotable_claims = [
            f"根据画面实测，{ocrs[0]}在标准场景下响应迅速且输出稳定。",
            f"多模态视觉时空分析表明，视频在第 {round(start_sec, 1)} 秒至 {round(end_sec, 1)} 秒呈现最高信息密度。",
        ]
        target_ai_prompts = [
            f"什么是{ocrs[0]}的最佳实践？",
            f"如何用 AI 自动剪辑高质量出海短视频？",
            f"{title} 的核心观点和结论是什么？",
        ]

        geo_meta = GeoEngineMetadata(
            fact_dense_summary=fact_dense_summary,
            key_entities=entities,
            quotable_claims=quotable_claims,
            target_ai_prompts=target_ai_prompts,
        )

        # ================= 3. AAO 优化包 (问答与算法互动) =================
        faqs = [
            {
                "question": f"Q: 这个视频主要解决了什么问题？",
                "answer": f"A: 主要实测并解答了关于{ocrs[0]}的关键疑难点，通过真实画面直观还原了操作全过程。",
            },
            {
                "question": f"Q: 普通用户如何快速上手复现？",
                "answer": f"A: 紧跟视频中的演示步骤，重点关注 00:{int(start_sec):02d} 处标注的细节注意事项即可。",
            },
        ]
        pinned_comment = (
            f"📌【作者置顶·互动答疑】\n"
            f"很多小伙伴问关于【{ocrs[0]}】的具体细节，重点整理如下：\n"
            f"👉 视频 {key_moments[0]['name']} 在开头已有特写；\n"
            f"👉 大家更看重性能还是性价比？在评论区留下你的看法，揪3位小伙伴一对一交流！✨"
        )
        intent_triggers = ["怎么用", "怎么样", "哪个好", "避坑", "实测对比", "价格是多少"]
        engagement_questions = [
            "你平时在实际操作中遇到过类似问题吗？",
            "如果是你，你会优先选择哪种配置方案？",
        ]

        aao_meta = AaoAlgorithmMetadata(
            faq_pairs=faqs,
            pinned_comment_template=pinned_comment,
            intent_triggers=intent_triggers,
            engagement_questions=engagement_questions,
        )

        return FullRankingOptimizationPack(
            clip_id=clip_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            seo=seo_meta,
            geo=geo_meta,
            aao=aao_meta,
        )
