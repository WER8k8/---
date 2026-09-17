# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多模态外贸营销工厂服务 - 真实大模型驱动的生图提示词、社媒营销发帖、外贸短视频分镜生成与视频剪辑装配。"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)


def _extract_json_block(text: str) -> dict[str, Any]:
    """从大模型原始输出中提取并解析合法 JSON 字典。"""
    if not text or not isinstance(text, str):
        return {}
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
    if match:
        cleaned = match.group(1).strip()
    else:
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            cleaned = cleaned[brace_start : brace_end + 1]
    try:
        return json.loads(cleaned)
    except Exception:
        return {"raw_content": text}


class AIMultimodalStudio:
    """多模态营销工作室 — 整合视觉、发帖、视频分镜与智能剪辑编排。"""

    def __init__(self):
        self.ai = AIEngine()

    async def generate_image_prompts(
        self, product_name: str, scene: str = "studio", target_market: str = "global"
    ) -> dict[str, Any]:
        """调用大模型生成专业 Midjourney / SD 级产品商业摄影提示词。"""
        prompt = f"""作为一个顶级工业与跨境电商视觉设计师，请为外贸产品【{product_name}】设计专业的AI生图Prompt。
场景类型：{scene}
目标海外市场：{target_market}

请以严格的 JSON 格式输出：
{{
  "product_name": "{product_name}",
  "scene": "{scene}",
  "positive_prompt": "英文正向生图提示词（包含商业摄影、材质、光影、渲染器Octane Render参数、8k分辨率）",
  "negative_prompt": "英文反向提示词（blurry, distorted, low quality, watermark, text）",
  "recommended_ratio": "16:9",
  "lighting_style": "光影风格说明",
  "color_palette": ["主色调", "辅助色", "质感色"]
}}
请只输出合法的 JSON 代码块，不要附带额外客套话。"""

        try:
            raw = await self.ai.generate(prompt, model="general")
            parsed = _extract_json_block(raw)
            if "positive_prompt" in parsed:
                pp = parsed["positive_prompt"]
                if product_name not in pp:
                    parsed["positive_prompt"] = f"{product_name}, {pp}"
                return parsed
        except Exception as e:
            logger.warning(f"大模型生图提示词生成降级: {e}")

        # 降级保底
        return {
            "product_name": product_name,
            "scene": scene,
            "positive_prompt": f"Commercial studio photography of {product_name}, elegant lighting, 8k, sharp focus",
            "negative_prompt": "low quality, blurry, watermark",
            "recommended_ratio": "16:9",
            "lighting_style": "Soft Box Studio Lighting",
            "color_palette": ["#4a9b8c", "#2a6b60", "#f3f4f6"],
        }

    async def generate_social_post(
        self, product_name: str, platform: str = "linkedin", language: str = "en"
    ) -> dict[str, Any]:
        """调用大模型生成多平台海外营销博文（发帖子链路）。"""
        prompt = f"""作为资深海外B2B数字营销操盘手，请为产品【{product_name}】撰写发布在【{platform}】的高转化率营销推广博文。
目标语言：{language}
平台特性：符合 {platform} 用户浏览习惯与算法推荐逻辑。

请以严格的 JSON 格式输出：
{{
  "platform": "{platform}",
  "language": "{language}",
  "title": "引人注目的标题",
  "copywriting": "正文内容（包含买家痛点唤醒、产品核心卖点解构、信任背书、CTA行动指引）",
  "hashtags": ["#Tag1", "#Tag2", "#Tag3", "#Tag4"],
  "call_to_action": "明确的询盘/留言行动指引",
  "estimated_reach_score": 88
}}
请只输出合法的 JSON 代码块。"""

        try:
            raw = await self.ai.generate(prompt, model="general")
            parsed = _extract_json_block(raw)
            if "copywriting" in parsed:
                cw = parsed["copywriting"]
                if product_name not in cw:
                    parsed["copywriting"] = f"{product_name}: {cw}"
                if not any("#B2B" in h for h in parsed.get("hashtags", [])):
                    parsed.setdefault("hashtags", []).append("#B2B")
                return parsed
        except Exception as e:
            logger.warning(f"大模型社媒发帖生成降级: {e}")

        # 降级保底
        tag = product_name.replace(" ", "")
        return {
            "platform": platform,
            "language": language,
            "title": f"Next-Gen {product_name} for Global Markets",
            "copywriting": f"Boost your efficiency with our industrial-grade {product_name}. Direct OEM supply. Contact us today!",
            "hashtags": [f"#{tag}", "#B2BGlobal", "#ExportTrade", "#SmartManufacturing"],
            "call_to_action": "Send an RFQ today for direct factory discounts.",
            "estimated_reach_score": 80,
        }

    async def generate_video_script(
        self,
        product_name: str,
        duration_sec: int = 30,
        target_market: str = "global",
        language: str = "en",
    ) -> dict[str, Any]:
        """调用大模型生成专业的出海短视频分镜脚本（视频生成链路）。"""
        prompt = f"""作为专业出海短视频导演，请为外贸产品【{product_name}】策划一个时长约 {duration_sec} 秒的高转化短视频分镜脚本。
目标市场：{target_market}
配音与字幕语言：{language}

请以严格的 JSON 格式输出：
{{
  "title": "视频标题",
  "product_name": "{product_name}",
  "duration_total": {duration_sec},
  "aspect_ratio": "9:16",
  "bgm_style": "背景音乐风格（如 Uplifting Corporate / Modern Tech Beats）",
  "scenes": [
    {{
      "scene_id": 1,
      "duration_sec": 5,
      "visual_description": "分镜画面视觉描述（运镜、景别、视觉主体动效）",
      "visual_prompt_ai": "AI生图/生视频英文提示词",
      "voiceover": "旁白口播配音台词",
      "onscreen_text": "屏幕花字贴片文案",
      "sound_effect": "转场与特定动作音效"
    }}
  ]
}}
请策划 4-6 个紧凑分镜头，总时长等于 {duration_sec} 秒。只输出合法 JSON 代码块。"""

        try:
            raw = await self.ai.generate(prompt, model="general")
            parsed = _extract_json_block(raw)
            if "scenes" in parsed and isinstance(parsed["scenes"], list) and len(parsed["scenes"]) > 0:
                return parsed
        except Exception as e:
            logger.warning(f"大模型视频脚本生成降级: {e}")

        # 降级保底分镜
        return {
            "title": f"{product_name} Global Showcase",
            "product_name": product_name,
            "duration_total": duration_sec,
            "aspect_ratio": "9:16",
            "bgm_style": "Dynamic Corporate Inspiration",
            "scenes": [
                {
                    "scene_id": 1,
                    "duration_sec": 6,
                    "visual_description": f"Close-up dynamic rotation shot of {product_name} with sleek metallic texture",
                    "visual_prompt_ai": f"Hyper-realistic 8k cinematic shot of {product_name}, modern studio, dynamic camera pan",
                    "voiceover": f"Looking for reliable {product_name}? Engineered for perfection.",
                    "onscreen_text": f"PREMIUM {product_name.upper()}",
                    "sound_effect": "Whoosh transition",
                },
                {
                    "scene_id": 2,
                    "duration_sec": 14,
                    "visual_description": "Split-screen comparison showing performance and durability in factory conditions",
                    "visual_prompt_ai": "Smart factory production line, high precision robotics assembling parts, cinematic lighting",
                    "voiceover": "Certified international quality with 30% higher longevity and zero-defect assurance.",
                    "onscreen_text": "ISO9001 Certified • High Durability",
                    "sound_effect": "Subtle digital click",
                },
                {
                    "scene_id": 3,
                    "duration_sec": 10,
                    "visual_description": "Fast-paced showcase of global shipping containers, global map and contact badge",
                    "visual_prompt_ai": "Cargo ship at modern seaport at sunset, container logistics, worldwide trade",
                    "voiceover": "Global door-to-door delivery. Request your custom quotation now.",
                    "onscreen_text": "Global Supply • Contact Us Today",
                    "sound_effect": "Impact boom & fade out",
                },
            ],
        }

    async def assemble_video_edit_spec(self, script_data: dict[str, Any]) -> dict[str, Any]:
        """将分镜脚本自动装配为可供 ffmpeg / 渲染流水线直接消费的工程剪辑时间轴规范。"""
        scenes = script_data.get("scenes", [])
        total_duration = 0.0
        timeline_tracks = []
        voiceover_scripts = []

        current_time = 0.0
        for idx, sc in enumerate(scenes):
            d = float(sc.get("duration_sec", 5))
            track_item = {
                "track_index": idx + 1,
                "start_time": current_time,
                "end_time": current_time + d,
                "duration": d,
                "visual_prompt": sc.get("visual_prompt_ai", ""),
                "subtitle": sc.get("onscreen_text", ""),
                "voiceover_line": sc.get("voiceover", ""),
                "transition": "crossfade" if idx > 0 else "fade_in",
                "transition_duration": 0.5,
            }
            timeline_tracks.append(track_item)
            if sc.get("voiceover"):
                voiceover_scripts.append(f"[{current_time:.1f}s - {current_time + d:.1f}s] {sc.get('voiceover')}")
            current_time += d

        total_duration = current_time

        edit_spec = {
            "project_name": script_data.get("title", "Video_Edit_Project"),
            "aspect_ratio": script_data.get("aspect_ratio", "9:16"),
            "resolution": "1080x1920" if script_data.get("aspect_ratio") == "9:16" else "1920x1080",
            "fps": 30,
            "total_duration": total_duration,
            "bgm_style": script_data.get("bgm_style", "Modern Tech"),
            "audio_mix": {
                "bgm_volume": 0.25,
                "voiceover_volume": 1.0,
                "ducking_enabled": True,
            },
            "timeline": timeline_tracks,
            "ffmpeg_filter_complex_recipe": f"concat=n={len(scenes)}:v=1:a=1",
            "voiceover_manifest": voiceover_scripts,
        }
        return edit_spec

