import json
import asyncio
from typing import Optional
from ai_engine.core.config import ai_settings


class AIEngine:
    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or ai_settings.default_llm
        self._provider = None
        self._token_stats = {"total_prompt_tokens": 0, "total_completion_tokens": 0, "total_cost": 0.0}

    def _resolve_provider(self, model: Optional[str] = None):
        model_name = model or self.default_model
        from ai_engine.core.providers.llm_factory import LLMFactory
        return LLMFactory.create(model_name)

    def _track_usage(self, prompt_tokens: int, completion_tokens: int, cost: float):
        self._token_stats["total_prompt_tokens"] += prompt_tokens
        self._token_stats["total_completion_tokens"] += completion_tokens
        self._token_stats["total_cost"] += cost

    async def generate(self, prompt: str, model: Optional[str] = None,
                       max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> dict:
        llm = self._resolve_provider(model)
        actual_max_tokens = max_tokens or ai_settings.max_tokens
        actual_temperature = temperature if temperature is not None else ai_settings.temperature

        messages = [{"role": "user", "content": prompt}]

        try:
            if hasattr(llm, 'ainvoke'):
                response = await llm.ainvoke(messages)
                content = response.content if hasattr(response, 'content') else str(response)
                token_usage = self._estimate_tokens(prompt, content)
            elif hasattr(llm, 'generate'):
                response = await llm.generate([messages], max_tokens=actual_max_tokens, temperature=actual_temperature)
                content = response.generations[0][0].text
                token_usage = self._estimate_tokens(prompt, content)
            else:
                content = str(llm)
                token_usage = self._estimate_tokens(prompt, content)

            cost = self._calculate_cost(token_usage["completion_tokens"], model or self.default_model)
            self._track_usage(token_usage["prompt_tokens"], token_usage["completion_tokens"], cost)

            return {
                "content": content,
                "token_usage": token_usage["total_tokens"],
                "cost": cost,
                "model": model or self.default_model,
            }
        except Exception as e:
            return {
                "content": "",
                "error": str(e),
                "token_usage": 0,
                "cost": 0.0,
                "model": model or self.default_model,
            }

    async def generate_batch(self, prompts: list[str], model: Optional[str] = None) -> list[dict]:
        tasks = [self.generate(prompt, model) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def _estimate_tokens(self, prompt: str, response: str) -> dict:
        prompt_tokens = len(prompt) // 2 + len(prompt.split()) // 2
        completion_tokens = len(response) // 2 + len(response.split()) // 2
        return {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens}

    def _calculate_cost(self, tokens: int, model: str) -> float:
        rates = {
            "gpt-4o": 0.00001,
            "gpt-4o-mini": 0.000003,
            "gpt-3.5-turbo": 0.000002,
            "claude-3-opus": 0.000015,
            "claude-3-sonnet": 0.000003,
            "claude-3-haiku": 0.000001,
            "gemini-1.5-pro": 0.000007,
            "gemini-1.5-flash": 0.000001,
        }
        rate = rates.get(model, 0.000005)
        return round(tokens * rate, 6)

    def get_stats(self) -> dict:
        return self._token_stats

    def reset_stats(self):
        self._token_stats = {"total_prompt_tokens": 0, "total_completion_tokens": 0, "total_cost": 0.0}

    async def analyze_seo_content(self, content: str, keyword: str) -> dict:
        prompt = f"""分析以下内容在关键词"{keyword}"上的SEO表现。

内容:
{content[:2000]}

请返回JSON格式分析结果，包含:
1. keyword_density: 关键词密度(百分比)
2. keyword_in_title: 标题是否含关键词(bool)
3. keyword_in_h1: H1是否含关键词(bool)
4. keyword_in_first_paragraph: 首段是否含关键词(bool)
5. content_length: 内容长度
6. suggestions: 优化建议列表"""

        result = await self.generate(prompt, max_tokens=1000)
        content = result.get("content", "")
        try:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            analysis = json.loads(content[json_start:json_end])
        except (ValueError, json.JSONDecodeError):
            analysis = {"error": "解析失败", "raw": content[:200]}

        analysis["token_usage"] = result.get("token_usage", 0)
        analysis["cost"] = result.get("cost", 0)
        return analysis

    async def generate_meta_tags(self, content: str, keyword: str, page_type: str = "product") -> dict:
        prompt = f"""为以下{page_type}页面生成SEO Meta标签。

核心关键词: {keyword}

内容摘要: {content[:1000]}

请返回JSON:
1. meta_title: 15-30字
2. meta_description: 50-120字
3. h1_tag: 核心标题
4. slug: URL别名(英文)"""

        result = await self.generate(prompt, max_tokens=500)
        content = result.get("content", "")
        try:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            meta = json.loads(content[json_start:json_end])
        except (ValueError, json.JSONDecodeError):
            meta = {"title": content[:50], "description": content[50:150]}

        meta["token_usage"] = result.get("token_usage", 0)
        return meta
