import os
from typing import Optional
from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_llm: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7
    monthly_budget: float = 100.0

    class Config:
        env_file = ".env"
        env_prefix = "AI_"
        extra = "ignore"


ai_settings = AISettings()
