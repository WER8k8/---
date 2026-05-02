from typing import Optional
from ai_engine.core.config import ai_settings


class LLMFactory:
    @staticmethod
    def create(model: Optional[str] = None):
        model_name = model or ai_settings.default_llm

        if model_name.startswith("gpt"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=ai_settings.openai_api_key,
                model=model_name,
                temperature=ai_settings.temperature,
                max_tokens=ai_settings.max_tokens,
            )
        elif model_name.startswith("claude"):
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                api_key=ai_settings.anthropic_api_key,
                model=model_name,
                temperature=ai_settings.temperature,
                max_tokens=ai_settings.max_tokens,
            )
        elif model_name.startswith("gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                api_key=ai_settings.gemini_api_key,
                model=model_name,
                temperature=ai_settings.temperature,
                max_tokens=ai_settings.max_tokens,
            )

        raise ValueError(f"不支持的模型: {model_name}")
