import json
import re
from typing import Optional
from ai_engine.core.engine import AIEngine


class KeywordAnalyzer:
    SEARCH_INTENT_PATTERNS = {
        "informational": ["什么是", "如何", "区别", "标准", "规范", "价格", "多少钱"],
        "commercial": ["哪家好", "推荐", "排名", "供应商", "厂家", "批发"],
        "transactional": ["购买", "采购", "订购", "报价", "询价", "下单"],
        "navigational": ["官网", "公司", "地址", "电话", "联系"],
    }

    def __init__(self, engine: Optional[AIEngine] = None):
        self.engine = engine or AIEngine()

    def analyze_intent(self, keyword: str) -> dict:
        for intent, patterns in self.SEARCH_INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in keyword:
                    return {"intent": intent, "matched_pattern": pattern}
        return {"intent": "informational", "matched_pattern": None}

    def estimate_difficulty(self, keyword: str) -> dict:
        length = len(keyword)
        has_specific = bool(re.search(r"[A-Z0-9]+", keyword))
        is_niche = any(kw in keyword for kw in ["轻集料", "陶粒", "加气", "保温", "混凝土"])
        difficulty_score = 30
        if length > 6:
            difficulty_score += 10
        if is_niche:
            difficulty_score -= 15
        if has_specific:
            difficulty_score += 5
        difficulty_score = max(5, min(95, difficulty_score))
        level = "high" if difficulty_score > 65 else "medium" if difficulty_score > 35 else "low"
        return {"score": difficulty_score, "level": level, "factors": {"length": length, "is_niche": is_niche}}

    async def analyze_keyword_deep(self, keyword: str) -> dict:
        prompt = f"""分析建材行业关键词「{keyword}」的SEO数据，返回JSON格式：
{{
  "intent": "搜索意图",
  "difficulty": 难度分数(1-100),
  "related_keywords": ["相关关键词1", "相关关键词2", "相关关键词3", "相关关键词4", "相关关键词5"],
  "content_suggestions": ["内容建议1", "内容建议2", "内容建议3"],
  "target_audience": "目标受众描述"
}}"""
        result = await self.engine.generate(prompt, model="gpt-4o-mini")
        try:
            return json.loads(result.content)
        except (json.JSONDecodeError, AttributeError):
            basic = self.estimate_difficulty(keyword)
            intent_info = self.analyze_intent(keyword)
            return {
                "intent": intent_info["intent"],
                "difficulty": basic["score"],
                "related_keywords": [f"{keyword} 价格", f"{keyword} 厂家", f"{keyword} 标准"],
                "content_suggestions": [f"介绍{keyword}的产品特性", f"{keyword}的技术参数和应用场景"],
                "target_audience": f"关注{keyword}的建材采购商和工程技术人员",
            }

    def calculate_trend(self, keyword: str, historical_data: list[dict]) -> dict:
        if not historical_data or len(historical_data) < 2:
            return {"direction": "stable", "change_percent": 0, "volatility": "low"}
        recent = sum(d.get("volume", 0) for d in historical_data[-3:]) / max(len(historical_data[-3:]), 1)
        older = sum(d.get("volume", 0) for d in historical_data[:-3]) / max(len(historical_data[:-3]), 1) if len(historical_data) > 3 else recent
        if recent > older * 1.1:
            direction = "up"
        elif recent < older * 0.9:
            direction = "down"
        else:
            direction = "stable"
        change = ((recent - older) / max(older, 1)) * 100
        return {"direction": direction, "change_percent": round(change, 1), "volatility": "medium" if abs(change) > 20 else "low"}
