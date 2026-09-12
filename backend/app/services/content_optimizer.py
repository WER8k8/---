import json
import logging
import re
from typing import Optional

import tiktoken
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.seo import AiOptimizationLog

logger = logging.getLogger(__name__)

TECHNICAL_WHITELIST = {
    "density_range": (
        800,
        1950),
    "strength_grades": [
        "LC5.0",
        "LC7.5",
        "LC10",
        "LC15",
        "LC20",
        "LC25",
        "LC30",
        "LC35",
        "LC40",
        "LC45",
        "LC50"],
    "thermal_conductivity_range": (
        0.18,
        0.50),
}

TECHNICAL_PATTERNS = {
    "density": re.compile(r"(\d+)\s*(?:kg/m³|kg/m3)"),
    "strength": re.compile(r"LC\d+(?:\.\d+)?"),
    "thermal": re.compile(r"(\d+\.?\d*)\s*W/(?:m·K|mK|m\*K)"),
}


class ContentOptimizer:
    def __init__(self, ai_engine=None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param ai_engine: 参数 ai_engine
        :return: 返回处理结果。
        """
        self.ai_engine = ai_engine

    def extract_technical_params(self, content: str) -> dict:
        """extract_technical_params。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :return: 返回处理结果。
        """
        params = {}
        density_match = TECHNICAL_PATTERNS["density"].search(content)
        if density_match:
            val = int(density_match.group(1))
            if TECHNICAL_WHITELIST["density_range"][0] <= val <= TECHNICAL_WHITELIST["density_range"][1]:
                params["density"] = density_match.group(0)

        strength_matches = TECHNICAL_PATTERNS["strength"].findall(content)
        if strength_matches:
            valid = [
                s for s in strength_matches if s in TECHNICAL_WHITELIST["strength_grades"]]
            if valid:
                params["strength"] = valid[0]

        thermal_match = TECHNICAL_PATTERNS["thermal"].search(content)
        if thermal_match:
            val = float(thermal_match.group(1))
            low, high = TECHNICAL_WHITELIST["thermal_conductivity_range"]
            if low <= val <= high:
                params["thermal_conductivity"] = thermal_match.group(0)

        return params

    def validate_compliance(self, original: str, optimized: str) -> dict:
        """validate_compliance。

        参数说明：
        :param self: 参数 self
        :param original: 参数 original
        :param optimized: 参数 optimized
        :return: 返回处理结果。
        """
        orig_params = self.extract_technical_params(original)
        opt_params = self.extract_technical_params(optimized)
        issues = []
        preserved = True
        for key in orig_params:
            if key not in opt_params:
                issues.append({"param": key,
                               "original": orig_params[key],
                               "optimized": None,
                               "issue": "参数丢失"})
                preserved = False
            elif orig_params[key] != opt_params[key]:
                issues.append({"param": key,
                               "original": orig_params[key],
                               "optimized": opt_params[key],
                               "issue": "参数被修改"})
                preserved = False

        forbidden_words = [
            "最",
            "第一",
            "首个",
            "唯一",
            "冠军",
            "顶级",
            "百分百",
            "100%",
            "零风险",
            "无效退款"]
        for word in forbidden_words:
            if word in optimized:
                issues.append({"param": "ad_text", "original": None,
                              "optimized": word, "issue": "含禁用广告词"})
                preserved = False

        return {
            "is_valid": preserved,
            "issues": issues,
            "technical_params_preserved": preserved}

    def restore_technical_params(self, original: str, optimized: str) -> str:
        """restore_technical_params。

        参数说明：
        :param self: 参数 self
        :param original: 参数 original
        :param optimized: 参数 optimized
        :return: 返回处理结果。
        """
        orig_params = self.extract_technical_params(original)
        result = optimized
        for key, value in orig_params.items():
            pattern = TECHNICAL_PATTERNS.get(key)
            if pattern and key == "strength":
                existing = pattern.findall(result)
                if not existing:
                    result = result.replace("轻集料混凝土", f"轻集料混凝土（{value}）", 1)
            elif pattern and key in ("density", "thermal_conductivity"):
                existing = pattern.search(result)
                if not existing:
                    result += f"（技术参数：{value}）"
        return result

    def estimate_tokens(self, text: str, model_name: str = "gpt-4o") -> int:
        """Count tokens using tiktoken for accurate model-specific counting.

        Falls back to the old len/2 heuristic if tiktoken cannot resolve the encoding.
        """
        try:
            enc = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.debug(
                "tiktoken: model '%s' not recognized, falling back to cl100k_base",
                model_name,
            )
            try:
                enc = tiktoken.get_encoding("cl100k_base")
            except Exception:
                logger.debug("tiktoken: cl100k_base unavailable, falling back to len/2")
                return len(text) // 2 + len(re.findall(r"\s+", text))
        return len(enc.encode(text))

    async def optimize(
            self,
            content: str,
            opt_type: str,
            keywords: list[str],
            model: str = "gpt-4o",
            db: Session = None) -> dict:
        """optimize。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param opt_type: 参数 opt_type
        :param keywords: 参数 keywords
        :param model: 参数 model
        :param db: 参数 db
        :return: 返回处理结果。
        """
        orig_params = self.extract_technical_params(content)
        orig_tokens = self.estimate_tokens(content)
        opt_type_guide = {
            "title": "优化Meta标题，控制在15-30字，包含核心关键词，有吸引力",
            "description": "优化Meta描述，控制在50-120字，包含关键词和行动号召",
            "alt_text": "优化图片Alt文本，控制在5-20字，描述图片内容并包含关键词",
            "content": "优化正文内容，保持500-2000字，提升可读性和SEO效果",
        }.get(opt_type, "优化内容以提升SEO效果")
        guidance = opt_type_guide
        keywords_str = ", ".join(keywords)
        if self.ai_engine:
            prompt = f"""你是一个SEO优化专家，请对以下内容进行{opt_type}类型优化。

优化指南：{guidance}

核心关键词：{keywords_str}

技术参数（必须保持原值，不可修改）：
{json.dumps(orig_params, ensure_ascii=False)}

原始内容：
{content}

请返回优化后的内容，仅输出优化结果，不要额外解释。"""

            ai_result = await self.ai_engine.generate(prompt, model=model, max_tokens=self.estimate_tokens(content) * 2)
            optimized = ai_result.get("content", content)
            token_usage = ai_result.get("token_usage", orig_tokens * 2)
            cost = ai_result.get("cost", 0.0)
        else:
            optimized = content
            token_usage = orig_tokens
            cost = 0.0

        optimized = self.restore_technical_params(content, optimized)
        compliance = self.validate_compliance(content, optimized)
        if db:
            log = AiOptimizationLog(
                resource_type="content",
                resource_id=f"optimize_{opt_type}",
                optimization_type=opt_type,
                original_content=content[:500],
                optimized_content=optimized[:500],
                model_used=model,
                tokens_used=token_usage,
            )
            db.add(log)
            db.commit()

        changes = []
        if content != optimized:
            changes.append(f"{opt_type}已优化")
        if not compliance["technical_params_preserved"]:
            changes.append("技术参数已恢复")

        return {
            "optimized_content": optimized,
            "changes": changes,
            "token_usage": token_usage,
            "cost": round(
                cost,
                6),
            "technical_params_preserved": compliance["technical_params_preserved"],
        }
