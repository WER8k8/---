from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "轻集料混凝土 SEO系统"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:80", "https://youding.com"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "youding.com"]

    DATABASE_URL: str = "sqlite:///./youding_dev.db"
    DB_TYPE: str = "sqlite"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    AI_OPENAI_API_KEY: Optional[str] = None
    AI_ANTHROPIC_API_KEY: Optional[str] = None
    AI_GEMINI_API_KEY: Optional[str] = None
    AI_DEEPSEEK_API_KEY: Optional[str] = None
    AI_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    AI_NVIDIA_API_KEY: Optional[str] = None
    AI_NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    AI_NVIDIA_MODEL: str = "meta/llama-3.1-70b-instruct"
    
    AI_NVIDIA_MODELS: dict = {
        "code": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "logic": "mistralai/mistral-large-3-675b-instruct-2512",
        "general": "meta/llama-3.1-70b-instruct",
        "chinese": "z-ai/glm4.7",
        "vision": "qwen/qwen3-coder-480b-a35b-instruct",
    }

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # 安全配置
    RATE_LIMIT_MAX_REQUESTS: int = 200
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx", "xls", "xlsx", "dwg", "dxf"]

    # 邮件服务配置
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.JWT_SECRET_KEY:
            if self.DEBUG:
                # 开发环境使用固定的测试密钥，避免每次重启token失效
                import warnings
                warnings.warn("开发环境：使用测试JWT密钥（请勿在生产环境使用）")
                self.JWT_SECRET_KEY = "dev_secret_key_for_testing_only"
            else:
                raise ValueError(
                    "❌ 生产环境必须配置JWT_SECRET_KEY环境变量！\n"
                    "请在.env文件或环境变量中设置：\n"
                    "  JWT_SECRET_KEY=your-secure-random-secret-key\n"
                    "建议使用以下命令生成安全的密钥：\n"
                    "  python -c 'import secrets; print(secrets.token_hex(32))'"
                )

        if self.DB_TYPE == "sqlite" and "postgresql" not in self.DATABASE_URL:
            if not self.DATABASE_URL.startswith("sqlite"):
                sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "youding_dev.db")
                self.DATABASE_URL = f"sqlite:///{sqlite_path}"


settings = Settings()
