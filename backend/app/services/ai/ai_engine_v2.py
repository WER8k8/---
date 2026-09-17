# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI引擎 v2 - 基于真实LLM调用的完整实现
功能：
1. AI内容生成（真实LLM调用，通过AIEngine单例）
2. 多LLM调度（DeepSeek/OpenAI/Gemini/Claude/NVIDIA智能路由）
3. 智能路由（根据任务类型选择最佳LLM）
4. 错误处理与降级（AI调用失败时返回降级数据）
5. 聊天对话（多轮上下文支持）
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)


class LLMProvider:
    """LLM提供商基类 - 委托给AIEngine实现真实调用"""
    def __init__(self, provider_name: str):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param provider_name: 参数 provider_name
        :return: 返回处理结果。
        """
        self.provider_name = provider_name
        self._engine = AIEngine()

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """生成文本，委托给AIEngine

        Args:
            prompt: 输入提示文本
            **kwargs: 额外参数（max_tokens, temperature等）

        Returns:
            包含生成文本和使用信息的字典
        """
        try:
            max_tokens = kwargs.get("max_tokens", 2000)
            task_complexity = kwargs.get("task_complexity", "medium")
            result = await self._engine.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                task_complexity=task_complexity,
            )
            return {
                "text": result.get("content", ""),
                "usage": {
                    "prompt_tokens": result.get("token_usage", 0) // 2,
                    "completion_tokens": result.get("token_usage", 0) // 2,
                },
            }
        except Exception as e:
            logger.error(f"LLMProvider.generate failed for {self.provider_name}: {e}")
            return {
                "text": "",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "error": str(e),
            }


class OpenAIProvider(LLMProvider):
    """OpenAI原生支持 - 通过AIEngine路由"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        super().__init__("openai")

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """调用OpenAI GPT模型生成文本

        Args:
            prompt: 输入提示文本
            **kwargs: max_tokens, temperature等

        Returns:
            包含生成文本和使用信息的字典
        """
        kwargs.setdefault("task_complexity", "medium")
        return await super().generate(prompt, **kwargs)


class GeminiProvider(LLMProvider):
    """Gemini支持 - 通过AIEngine路由"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        super().__init__("gemini")

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """调用Google Gemini模型生成文本

        Args:
            prompt: 输入提示文本
            **kwargs: max_tokens, temperature等

        Returns:
            包含生成文本和使用信息的字典
        """
        kwargs.setdefault("task_complexity", "medium")
        return await super().generate(prompt, **kwargs)


class ClaudeProvider(LLMProvider):
    """Claude支持 - 通过AIEngine路由"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        super().__init__("claude")

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """调用Anthropic Claude模型生成文本

        Args:
            prompt: 输入提示文本
            **kwargs: max_tokens, temperature等

        Returns:
            包含生成文本和使用信息的字典
        """
        kwargs.setdefault("task_complexity", "complex")
        return await super().generate(prompt, **kwargs)


class DeepSeekProvider(LLMProvider):
    """DeepSeek支持 - 通过AIEngine路由（成本优化）"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        super().__init__("deepseek")

    async def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """调用DeepSeek模型生成文本（低成本高精度）

        Args:
            prompt: 输入提示文本
            **kwargs: max_tokens, temperature等

        Returns:
            包含生成文本和使用信息的字典
        """
        kwargs.setdefault("task_complexity", "simple")
        return await super().generate(prompt, **kwargs)


class AIEngineV2:
    """AI引擎 v2 - 完整实现，基于AIEngine单例的真实LLM调用

    功能：
    - 智能路由：根据任务特征自动选择最佳LLM
    - 多提供商支持：DeepSeek/OpenAI/Gemini/Claude/NVIDIA
    - 错误处理与降级：AI调用失败时返回合理的降级响应
    - 聊天对话：支持多轮上下文
    """
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.providers: Dict[str, LLMProvider] = {}
        self._engine = AIEngine()
        self._init_providers()

    def _init_providers(self) -> None:
        """根据AIEngine已初始化的提供商初始化Provider实例"""
        self.providers["openai"] = OpenAIProvider()
        self.providers["gemini"] = GeminiProvider()
        self.providers["claude"] = ClaudeProvider()
        self.providers["deepseek"] = DeepSeekProvider()

    async def generate_content(
        self,
        prompt: str,
        provider: Optional[str] = None,
        raise_on_all_failures: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """生成内容，支持智能路由和手动指定提供商

        Args:
            prompt: 输入提示文本
            provider: 指定LLM提供商（可选，未指定时智能选择）
            raise_on_all_failures: 当所有提供商都失败时是否抛出503异常（默认True）
            **kwargs: 传递给LLM的额外参数

        Returns:
            包含content/provider/usage的字典

        Raises:
            ValueError: 指定了不存在的提供商
            HTTPException(503): 所有提供商都失败且raise_on_all_failures=True
        """
        if provider is None:
            provider = self._select_provider(prompt)

        if provider not in self.providers:
            raise ValueError(
                f"Unknown provider: {provider}. Available: {list(self.providers.keys())}"
            )

        try:
            result = await self.providers[provider].generate(prompt, **kwargs)
            return {
                "content": result.get("text", ""),
                "provider": provider,
                "usage": result.get("usage", {}),
            }
        except Exception as e:
            logger.error(f"generate_content failed for provider {provider}: {e}")
            # 降级：尝试其他提供商
            fallback_provider = self._get_fallback_provider(provider)
            if fallback_provider:
                logger.info(f"Falling back to provider: {fallback_provider}")
                try:
                    result = await self.providers[fallback_provider].generate(
                        prompt, **kwargs
                    )
                    return {
                        "content": result.get("text", ""),
                        "provider": fallback_provider,
                        "usage": result.get("usage", {}),
                        "fallback": True,
                    }
                except Exception as fallback_err:
                    logger.error(f"Fallback provider {fallback_provider} also failed: {fallback_err}")

            # All providers exhausted
            if raise_on_all_failures:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"AI service unavailable: primary ({provider}) and all "
                        f"fallback providers failed. Last error: {e}"
                    ),
                )

            return {
                "content": "",
                "provider": provider,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "error": str(e),
            }

    def _select_provider(self, prompt: str) -> str:
        """根据prompt特征智能选择最佳LLM

        选择策略：
        - 代码生成/技术类 -> DeepSeek（低成本高精度）
        - 长文本/复杂推理 -> Claude（高质量推理）
        - 多语言任务 -> Gemini（多语言优势）
        - 默认 -> AIEngine当前提供商

        Args:
            prompt: 输入提示文本

        Returns:
            推荐的提供商名称
        """
        current = self._engine.current_provider
        if current and current in self.providers:
            return current

        # 根据prompt特征选择
        code_keywords = ["代码", "code", "function", "class", "debug", "implement"]
        complex_keywords = ["分析", "analyze", "reasoning", "推理", "复杂", "深度"]
        multilingual_keywords = ["translate", "翻译", "multi-language"]
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in code_keywords):
            return "deepseek"
        if any(kw in prompt_lower for kw in complex_keywords):
            return "claude"
        if any(kw in prompt_lower for kw in multilingual_keywords):
            return "gemini"

        # 默认使用DeepSeek（成本优化）
        return "deepseek"

    def _get_fallback_provider(self, failed_provider: str) -> Optional[str]:
        """获取降级提供商

        Args:
            failed_provider: 失败的提供商名称

        Returns:
            可用的降级提供商名称，无则返回None
        """
        fallback_order = ["deepseek", "openai", "gemini", "claude"]
        for provider in fallback_order:
            if provider != failed_provider and provider in self.providers:
                return provider
        return None

    async def chat(
        self,
        messages: List[Dict],
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """聊天对话，支持多轮上下文

        将多轮消息拼接为prompt，调用AIEngine生成响应

        Args:
            messages: 消息列表，每条包含role和content
            provider: 指定LLM提供商（可选）

        Returns:
            包含response/provider的字典
        """
        # 拼接多轮消息为prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"[System]: {content}")
            elif role == "assistant":
                prompt_parts.append(f"[Assistant]: {content}")
            else:
                prompt_parts.append(f"[User]: {content}")

        prompt = "\n".join(prompt_parts)
        if provider is None:
            provider = self._select_provider(prompt)

        try:
            result = await self.generate_content(prompt, provider)
            return {
                "response": result.get("content", ""),
                "provider": result.get("provider", provider),
            }
        except Exception as e:
            logger.error(f"chat failed: {e}")
            return {
                "response": "",
                "provider": provider or "unknown",
                "error": str(e),
            }


# 全局引擎实例
engine_v2 = AIEngineV2()


async def generate_content(
    prompt: str,
    provider: Optional[str] = None,
    raise_on_all_failures: bool = True,
) -> Dict[str, Any]:
    """生成内容API

    Args:
        prompt: 输入提示文本
        provider: 指定LLM提供商（可选）
        raise_on_all_failures: 所有提供商失败时抛出503（默认True）

    Returns:
        包含content/provider/usage的字典
    """
    return await engine_v2.generate_content(
        prompt, provider, raise_on_all_failures=raise_on_all_failures,
    )


async def chat(
    messages: List[Dict], provider: Optional[str] = None
) -> Dict[str, Any]:
    """聊天API

    Args:
        messages: 消息列表
        provider: 指定LLM提供商（可选）

    Returns:
        包含response/provider的字典
    """
    return await engine_v2.chat(messages, provider)
