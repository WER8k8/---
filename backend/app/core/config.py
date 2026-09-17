# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import os
import secrets
import warnings
from pathlib import Path
from typing import Optional, Any

from pydantic import ConfigDict, field_validator, Field
from pydantic_settings import BaseSettings


def _parse_bool_with_strip(v: Any) -> bool:
    """_parse_bool_with_strip。

    参数说明：
    :param v: 参数 v
    :return: 返回处理结果。
    """
    if isinstance(v, str):
        v = v.strip().lower()
        if v in ("true", "1", "yes", "y"):
            return True
        if v in ("false", "0", "no", "n"):
            return False
    return bool(v)


# 环境配置单一真相：config/{ENVIRONMENT}/.env 优先，回退 .env。
# 消除 backend/.env 与 config/dev/.env 双文件维护负担（清理项）。
_env_val = os.environ.get("ENVIRONMENT", "dev")
_env_name = {"development": "dev", "production": "prod", "test": "test"}.get(_env_val, _env_val)
_env_candidates = [
    os.environ.get("ENV_FILE"),
    f"config/{_env_name}/.env",
    ".env",
]
_env_file = [p for p in _env_candidates if p]

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=_env_file, env_file_encoding="utf-8", extra="allow")
    APP_NAME: str = "优丁 B2B SaaS"
    PROJECT_NAME: str = "优丁 B2B SaaS"
    PROJECT_DESCRIPTION: str = "优丁全球外贸B2B增长系统 - 智能建站、SEO矩阵、多模态获客与商机转化"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    MVP_LAUNCH: bool = False

    # 大模型与 AI 引擎配置（平台密钥/模型详见下方「15大模型平台统一管理」段）
    AI_PROVIDER: str = "openai"
    AI_OPENAI_MODEL: str = "qwen3.8-flash"
    AI_OPENAI_FALLBACK_MODEL: str = "glm-5.3-flash"
    # 轮16 Model Gateway：能力路由+成本记账门面（默认关，零回归；启用后旺财 N4 经网关写入 model_call_ledger）
    MODEL_GATEWAY_ENABLED: bool = False
    # RLS 试点表挂载（数据库层租户隔离）。默认关——必须等 per-request 租户注入
    # 就绪才能启用，否则启用后未注入租户的路径会把带 tenant_id 的表读写过滤为空。
    RLS_PILOT_ENABLED: bool = False
    RLS_PILOT_TABLES: str = ""  # 逗号分隔的试点表名（不含 schema），如 "mcp_servers"
    # 轮21 Trace/经验飞轮接线（task_traces + 终态钩子 + Canary 发布门禁）。
    # 默认关——任务端先接 start/complete Trace；终态钩子 / 门禁接线随业务链路启用。
    EVOLUTION_TRACE_ENABLED: bool = False
    # 轮23 任务端接线：统一任务控制面副作用（TaskTrace/终态钩子/计量埋点）与
    # Model Gateway ai_generation 计量旁路。默认关——核心 ai_tasks 状态机不受此开关
    # 影响；开启后副作用故障仍不阻断主链路。注意：gateway 计量经 meter_events 汇总
    # 进 token_ledger，与 model_call_ledger 聚合路径二选一启用，避免双重扣减。
    TASK_CONTROL_ENABLED: bool = False
    # 轮24 双记账防护：model_call_ledger→token_ledger 聚合闸门（默认关）。
    # 与 TASK_CONTROL_ENABLED（meter_events 计量路径）互斥启用，防止 token_ledger
    # 双重扣减；切换记账主路径时先关 TASK_CONTROL_ENABLED 再开本开关。
    MODEL_CALL_LEDGER_AGGREGATE_ENABLED: bool = False
    # 轮25-B Browser Runtime（P5）：Playwright + CDP 浏览器执行层（默认关，零回归）。
    # 启用条件：① 安装 playwright（`pip install playwright && playwright install chromium`）
    # ② BROWSER_RUNTIME_ALLOWED_TENANTS 白名单（防全量滥用，按租户灰度）
    # ③ 每个租户 Profile 目录与浏览器可执行权限（沙箱隔离）
    # 关闭时所有调用降级到 noop 并记录 warning，绝不阻断调用方主链路。
    BROWSER_RUNTIME_ENABLED: bool = False
    # 允许使用 Browser Runtime 的租户 ID 列表（逗号分隔，空 = 拒绝所有）
    # 推荐：与 Pipeline/Policy Engine 的 Canary 灰度纪律一致（5/25/50/100%）
    BROWSER_RUNTIME_ALLOWED_TENANTS: str = ""
    SITE_URL: str = "https://youding.com"
    # CORS配置
    # SaaS 主域名 (租户子域名基于此)
    SAAS_PRIMARY_DOMAIN: str = "youding-saas.com"
    # CORS配置 — 生产环境强制从 CORS_ORIGINS 环境变量读取，不再硬编码 localhost
    # 开发环境默认值通过 ENVIRONMENT=development 自动注入
    @property
    def CORS_ORIGINS(self) -> list[str]:
        """CORS_ORIGINS。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        raw = os.getenv("CORS_ORIGINS", "")
        # 开发环境：未配置时自动注入 localhost（仅 dev）
        if not raw.strip() and self.ENVIRONMENT == "development":
            raw = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"
        raw = raw.strip()
        if not raw:
            return []
        # 兼容 JSON 数组格式，如 '["http://a.com","http://b.com"]'
        if raw.startswith("["):
            import json
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        # 逗号分隔格式
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    ALLOWED_HOSTS: list[str] = ["youding.com", "youding-saas.com"]
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./youding_dev.db"
    DATABASE_READ_URL: Optional[str] = Field(None, env="DATABASE_READ_URL", description="数据库只读副本连接串")
    DB_TYPE: str = "sqlite"
    # SEO 矩阵 admin_users：与 Node 双模式对齐。优先 MySQL（生产），否则 SQLite 文件。
    SEO_MATRIX_SQLITE_PATH: Optional[str] = None
    SEO_MATRIX_DATABASE_URL: Optional[str] = None
    SEO_MATRIX_DB_HOST: Optional[str] = None
    SEO_MATRIX_DB_PORT: int = 3306
    SEO_MATRIX_DB_USER: Optional[str] = None
    SEO_MATRIX_DB_PASSWORD: Optional[str] = None
    SEO_MATRIX_DB_NAME: Optional[str] = None
    # Redis配置
    REDIS_ENABLED: bool = True
    # 登录防暴（与 refresh 黑名单共用 REDIS_URL；失败时 login_bruteforce 降级内存）
    LOGIN_BF_USE_REDIS: bool = True
    @field_validator("REDIS_ENABLED", "LOGIN_BF_USE_REDIS", mode="before")
    @classmethod
    def validate_bool_settings(cls, v: Any) -> bool:
        """validate_bool_settings。

        参数说明：
        :param cls: 参数 cls
        :param v: 参数 v
        :return: 返回处理结果。
        """
        return _parse_bool_with_strip(v)
    LOGIN_BF_REDIS_PREFIX: str = "login_bf"
    LOGIN_BF_REDIS_STATE_TTL: int = 1200  # 秒，须大于最长锁定时长并留余量以便键过期回收
    # 额外登录路由（相对 auth 路由前缀），默认 login 即 /api/v1/auth/login；与
    # VITE_AUTH_LOGIN_PATH 末段一致
    AUTH_LOGIN_ROUTE: str = "login"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_DB_ARQ: int = 1
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CONNECT_TIMEOUT: float = 1.0
    REDIS_SOCKET_TIMEOUT: float = 1.0
    # 司令部快照缓存（云端 Redis + SWR + 后台预热）
    COMMAND_CENTER_CACHE_TTL_SEC: int = 90
    COMMAND_CENTER_STALE_TTL_SEC: int = 300
    COMMAND_CENTER_PREWARM_INTERVAL_SEC: int = 45
    # 物流（Sprint H）
    LOGISTICS_PROVIDER: str = "demo"  # demo | kuaidi100
    KUAIDI100_API_KEY: Optional[str] = None
    KUAIDI100_CUSTOMER: Optional[str] = None
    LOGISTICS_FALLBACK_DEMO: bool = True
    # SSL（Sprint H / P0-01）
    SSL_PROVIDER: str = "mock"  # mock | http | acme | certbot
    ACME_WEBHOOK_URL: Optional[str] = None
    DEMO_HTTPS_DOMAIN: Optional[str] = None  # P0-02 保温厂演示独立域
    PAYMENT_WEBHOOK_SECRET: Optional[str] = None  # P0-07 回调 HMAC
    PAYMENT_STRICT_VERIFY: bool = False  # P0-07 生产验签 + egress 金额校验
    OPS_CRON_TOKEN: Optional[str] = None  # 外部 cron 调用 /ops/* 可选令牌
    # 出口 IP：manual=运营录入；mock=演示；asocks=JIT 采购；iproyal=长期养号住宅IP
    EGRESS_PROVIDER: str = "manual"  # manual | mock | asocks | iproyal
    EGRESS_JIT_COUNTRY: str = "US"
    EGRESS_QC_ENABLED: bool = True
    EGRESS_MOCK_DELAY_SEC: float = 2.0
    # IPRoyal 静态住宅IP自动采购（长期养号专用）
    IPROYAL_API_TOKEN: Optional[str] = None
    IPROYAL_API_BASE: str = "https://apid.iproyal.com/v1/reseller"
    IPROYAL_PRODUCT_ID: int = 9              # Static Residential 产品ID
    IPROYAL_PLAN_ID: int = 4                 # 默认60天计划ID（最佳性价比）
    IPROYAL_LOCATION_ID: int = 51            # 默认位置ID
    IPROYAL_CARD_ID: Optional[int] = None    # 绑卡ID（不填用余额扣款）
    IPROYAL_BATCH_SIZE: int = 5              # 每批采购数（IPRoyal最低5）
    IPROYAL_POOL_LOW_WATERMARK: int = 2      # 低水位线，低于此触发补充
    IPROYAL_QC_MULTI_ISP: bool = True        # 双ISP验证
    IPROYAL_AUTO_RENEW_DAYS: int = 7         # 到期前7天自动续费
    IPROYAL_RENEW_PLAN_ID: int = 4           # 续费计划ID（60天）
    IPROYAL_ALERT_WEBHOOK_URL: str = ""      # 续费失败告警webhook
    ASOCKS_API_KEY: Optional[str] = None
    ASOCKS_API_BASE: str = "https://api.asocks.com"
    ASOCKS_LIST_URL: Optional[str] = None
    ASOCKS_LIST_TYPE: str = "res"
    ASOCKS_TRAFFIC_LIMIT_GB: int = 10
    ASOCKS_TYPE_ID: Optional[int] = None
    ASOCKS_PROXY_TYPE_ID: Optional[int] = None
    CRAWL_WEBHOOK_SECRET: str = ""  # 国际询盘爬虫 Webhook HMAC（/api/v1/international/webhook）
    GSC_ADS_WEBHOOK_SECRET: str = ""  # GSC/Ads 归因 webhook（/api/v1/foreign-trade/attribution/gsc-ads-webhook）
    AI_CHAT_WEBHOOK_SECRET: str = ""  # AI 接待 webhook（/api/v1/chat/chat/webhook）
    RANK_SCHEDULER_ENABLED: bool = False  # 生产可开：每日关键词排名后台线程
    TAVILY_API_KEY: Optional[str] = None  # RADAR-09 技术雷达外网搜索
    GITHUB_TOKEN: Optional[str] = None  # GitHub 生态侦察 Search API（可选，提高限额）
    GITHUB_ECOSYSTEM_SCOUT_ENABLED: Optional[bool] = None  # 研究员代搜 GitHub 补齐 catalog 缺口
    # Google Custom Search API（获客搜索，可选；未配置则降级 Mock）
    GOOGLE_CSE_API_KEY: Optional[str] = None
    GOOGLE_CSE_CX: Optional[str] = None  # Custom Search Engine ID
    GOOGLE_CSE_BASE_URL: str = "https://www.googleapis.com/customsearch/v1"
    # WhatsApp Business Cloud API（可选；未配置则降级 Mock）
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: Optional[str] = None
    WHATSAPP_API_BASE: str = "https://graph.facebook.com/v19.0"
    # LinkedIn Sales Navigator API（可选；未配置则降级 Mock）
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None
    LINKEDIN_API_BASE: str = "https://api.linkedin.com/v2"
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_SECURE: bool = False
    # JWT配置
    SECRET_KEY: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # annex 附属统一登录桥令牌（goodjob/trade-ai 回调 /annex/redeem 用；§9.3）
    ANNEX_BRIDGE_TOKEN: str = ""
    # JWT HttpOnly Cookie 配置（FIX-22: 安全升级）
    JWT_COOKIE_NAME: str = "uj_access_token"
    JWT_REFRESH_COOKIE_NAME: str = "uj_refresh_token"
    JWT_USER_INFO_COOKIE_NAME: str = "uj_user_info"  # 非 HttpOnly，前端读取角色/用户名
    JWT_COOKIE_SAMESITE: str = "lax"  # lax | strict | none
    JWT_COOKIE_PATH: str = "/"
    JWT_REFRESH_COOKIE_PATH: str = "/api/v1/auth/refresh"  # refresh cookie 仅 refresh 端点可见
    @property
    def JWT_COOKIE_SECURE(self) -> bool:
        """生产环境启用 Secure 标志（仅 HTTPS 发送 Cookie）。"""
        return self.is_production()

    @property
    def JWT_COOKIE_DOMAIN(self) -> Optional[str]:
        """Cookie 域名：生产环境设为根域以支持子域共享。"""
        if self.is_production():
            return os.getenv("JWT_COOKIE_DOMAIN", None)
        return None  # 开发环境不设 domain，默认当前域

    # ========================================
    # 向量检索与知识图谱配置
    # ========================================
    # Qdrant 向量数据库
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_DEFAULT_COLLECTION: str = "default_vectors"
    # Neo4j 知识图谱
    NEO4J_URI: str = ""
    NEO4J_USER: str = ""
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"
    # ========================================
    # AI 模型配置 — 15大模型平台统一管理
    # ========================================
    # OpenAI
    AI_OPENAI_API_KEY: Optional[str] = None
    AI_OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    # Anthropic Claude
    AI_ANTHROPIC_API_KEY: Optional[str] = None        # 已配置 ✅
    AI_ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    # Google Gemini
    AI_GEMINI_API_KEY: Optional[str] = None
    AI_GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com"
    AI_GEMINI_ASR_MODEL: str = "gemini-2.0-flash"
    # DeepSeek（GPU 云端推理，H800 集群）
    AI_DEEPSEEK_API_KEY: Optional[str] = None
    AI_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_DEEPSEEK_MODELS: dict = {
        "code": "deepseek-coder",
        "logic": "deepseek-reasoner",
        "general": "deepseek-chat",
        "chinese": "deepseek-chat",
        "vision": "deepseek-chat",
    }
    # NVIDIA NIM（integrate.api.nvidia.com）
    # Key 本身不过期；免费额度/计费以 NVIDIA 控制台政策为准，需自行关注用量。
    AI_NVIDIA_API_KEY: Optional[str] = None
    AI_NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    # Cosmos 视频 NIM 自托管端点（/v1/infer）；托管 catalog 暂不提供 integrate 上的 infer
    AI_NVIDIA_COSMOS_BASE_URL: Optional[str] = None
    AI_NVIDIA_MODEL: str = "meta/llama-3.1-70b-instruct"
    # 按业务场景默认模型（完整列表见 GET /super-admin/ai-config/nvidia/catalog）
    AI_NVIDIA_MODELS: dict = {
        "inference": "meta/llama-3.1-8b-instruct",
        "article": "meta/llama-3.1-70b-instruct",
        "code": "qwen/qwen3-coder-480b-a35b-instruct",
        "logic": "mistralai/mistral-large-3-675b-instruct-2512",
        "general": "meta/llama-3.1-70b-instruct",
        "chinese": "meta/llama-3.1-70b-instruct",
        "vision": "meta/llama-3.2-11b-vision-instruct",
        "text_to_video": "nvidia/cosmos-predict1-5b",
        "image_to_video": "nvidia/cosmos-predict1-7b-video2world",
        "video_transfer": "nvidia/cosmos-transfer2.5-2b",
        "article_to_video_script": "meta/llama-3.1-8b-instruct",
        "article_to_video_render": "nvidia/cosmos-predict1-5b",
        "video_understanding": "nvidia/cosmos-reason2-8b",
        "embedding": "nvidia/nv-embed-v1",
    }
    # 阿里 Wan-Video (Wan2.1) 视频生成引擎配置
    VIDEO_GENERATION_ENGINE: str = "wan"  # wan | cosmos
    WAN_VIDEO_BASE_URL: Optional[str] = None
    WAN_VIDEO_API_KEY: Optional[str] = None
    WAN_VIDEO_MODEL_T2V: str = "wanx2.1-t2v-plus"
    WAN_VIDEO_MODEL_I2V: str = "wanx2.1-i2v-plus"

    # 多媒体工厂 / 渲染服务配置
    MEDIA_FACTORY_AUTO_RENDER: bool = True
    MEDIA_FACTORY_MOCK_RENDER: bool = False
    MEDIA_FACTORY_AI_WRITE_TIMEOUT: int = 8
    MEDIA_FACTORY_INFER_TIMEOUT: int = 600
    MEDIA_FACTORY_DEFAULT_FRAMES: int = 33
    MEDIA_OUTPUT_DIR: str = "uploads/media_factory"
    MEDIA_RETENTION_HOURS: int = 72
    MEDIA_HANDOFF_DELETE_HOURS: int = 1
    MEDIA_CLEANUP_SCHEDULER_ENABLED: bool = False
    MEDIA_CLEANUP_INTERVAL_MINUTES: int = 15
    MEDIA_FACTORY_MONTHLY_LIMIT_PER_TENANT: int = 0  # 0=不限制
    # 视频云存储分层（见 docs/MEDIA-FACTORY-CLOUD-STORAGE.md）
    MEDIA_CLOUD_PLAY_PRIMARY: str = "cuplayer"  # cuplayer | r2
    MEDIA_CLOUD_ARCHIVE: str = "r2"
    MEDIA_CLOUD_BACKUP: str = "lenslink"  # lenslink | none
    MEDIA_CUPLAYER_WRITETOKEN: Optional[str] = None
    MEDIA_CUPLAYER_SECRETKEY: Optional[str] = None
    MEDIA_CUPLAYER_USERID: Optional[str] = None
    MEDIA_CUPLAYER_READTOKEN: Optional[str] = None
    MEDIA_CUPLAYER_CATAID: int = 1
    MEDIA_CUPLAYER_UPLOAD_URL: str = (
        "http://v.polyv.net/uc/services/rest?method=uploadfile"
    )
    MEDIA_R2_ACCOUNT_ID: Optional[str] = None
    MEDIA_R2_ACCESS_KEY_ID: Optional[str] = None
    MEDIA_R2_SECRET_ACCESS_KEY: Optional[str] = None
    MEDIA_R2_BUCKET: Optional[str] = None
    MEDIA_R2_PUBLIC_BASE_URL: Optional[str] = None
    MEDIA_R2_CDN_BASE_URL: Optional[str] = None
    MEDIA_LENSLINK_ENDPOINT: Optional[str] = None
    MEDIA_LENSLINK_ACCESS_KEY: Optional[str] = None
    MEDIA_LENSLINK_SECRET_KEY: Optional[str] = None
    MEDIA_LENSLINK_BUCKET: Optional[str] = None
    MEDIA_LENSLINK_PUBLIC_BASE_URL: Optional[str] = None
    MEDIA_LENSLINK_SECURE: bool = True
    MEDIA_LENSLINK_REGION: str = "us-east-1"
    MEDIA_LENSLINK_PRESIGN_SECONDS: int = 604800
    MEDIA_CLOUD_UPLOAD_ENABLED: bool = True
    MEDIA_R2_PRESIGN_SECONDS: int = 604800  # 7 天，海外发布拉取用
    # 产品图片空间 — 国内七牛 / 海外 R2（见 product_image_storage_service）
    FILE_STORAGE_DEFAULT_REGION: str = "cn"  # 超管未绑租户时的默认分区：cn | global
    QINIU_ACCESS_KEY: Optional[str] = None
    QINIU_SECRET_KEY: Optional[str] = None
    QINIU_BUCKET: Optional[str] = None
    QINIU_PUBLIC_BASE_URL: Optional[str] = None  # 绑 CDN 域名，如 https://img.example.com
    QINIU_UPLOAD_HOST: str = "https://upload.qiniup.com"  # 华北 Bucket 常用 https://up-z1.qiniup.com
    MEDIA_AUTO_PUBLISH_TENANT_SITE: bool = True  # 上云后自动登记租户视频落地页（SEO/GEO）
    MEDIA_TENANT_VIDEO_PATH_PREFIX: str = "/v/"
    # AiToEarn 视频真发（抖音/快手/B站等）— 配置 API Key 后作为 Worker 链 fallback
    AITOEARN_API_BASE: str = "https://mcp.aitoearn.cn"
    AITOEARN_API_KEY: Optional[str] = None
    # Hermes 视频矩阵 Worker — social-auto-upload / biliup / 小红书 MCP
    SAU_ENABLED: bool = True
    SAU_CLI_PATH: Optional[str] = None
    SAU_HOME: Optional[str] = None
    SAU_ACCOUNT_PREFIX: str = "youding"
    SAU_BILIBILI_TID: int = 249
    SAU_SIDECAR_URL: Optional[str] = None
    PUBLISH_RESULT_NOTIFY_ENABLED: bool = False
    PUBLISH_RESULT_WEBHOOK_URL: str = ""
    BILIUP_ENABLED: bool = True
    BILIUP_CLI_PATH: Optional[str] = None
    BILIUP_COOKIE_FILE: Optional[str] = None
    XHS_MCP_ENABLED: bool = False
    XHS_MCP_BASE_URL: str = "http://127.0.0.1:18060"
    PUBLISH_WORKER_TIMEOUT_SEC: int = 900
    # 双线冗余：生产建议 true — 外站国内平台须 SAU 主路 + AiToEarn 备路同时就绪
    PUBLISH_DUAL_LINE_REQUIRED: bool = False
    # 场景失败时自动降级（如 article → inference）
    AI_SCENARIO_FALLBACK_ENABLED: bool = True
    # ORCH-23: LLM 单次调用整体超时（秒），含随机抖动 0–5s 防惊群
    AI_LLM_REQUEST_TIMEOUT: float = 30.0
    # ORCH-23: 单次重试内 LLM 调用超时（秒），默认 15s（总预算 30s 可配置）
    AI_LLM_PER_CALL_TIMEOUT: float = 15.0
    AI_SCENARIO_HEALTH_SCHEDULER_ENABLED: bool = False
    AI_SCENARIO_HEALTH_CHECK_HOUR: int = 7
    AI_SCENARIO_HEALTH_CHECK_MINUTE: int = 0
    AI_SCENARIO_HEALTH_INTERVAL_HOURS: int = 0  # >0 时按小时间隔，否则每日定点
    AI_SCENARIO_HEALTH_CHAT_TIMEOUT: float = 45.0  # glm 等大模型 ping 可能 >25s
    # 英伟达免费通道：客户可用模型定时探测（默认 1:00 / 12:00 / 20:00 北京时间）
    # None = 生产自动开启，开发默认关闭；显式 0/false 可关闭生产调度
    NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED: Optional[bool] = None
    NVIDIA_CUSTOMER_PROBE_SLOTS: str = "1:00,12:00,20:00"
    NVIDIA_CUSTOMER_PROBE_TZ: str = "Asia/Shanghai"
    @property
    def nvidia_customer_probe_scheduler_active(self) -> bool:
        """nvidia_customer_probe_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.NVIDIA_CUSTOMER_PROBE_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # Hermes 7×24 巡站维护（只读探测 + 快照；生产默认每 15 分钟）
    HERMES_SITE_PATROL_SCHEDULER_ENABLED: Optional[bool] = None
    HERMES_SITE_PATROL_INTERVAL_MINUTES: int = 15
    HERMES_SITE_PATROL_HTTP_SELF_URL: str = "http://127.0.0.1:8001"
    HERMES_ALERT_WEBHOOK_URL: str = ""  # 默认同 FEISHU_WEBHOOK_URL
    HERMES_ALERT_COOLDOWN_MINUTES: int = 60
    HERMES_AUTO_REMEDIATION_ENABLED: Optional[bool] = None
    HERMES_OPS_AUTOPILOT_ENABLED: Optional[bool] = None  # 巡站后跑技术雷达+通知
    HERMES_CONTINUOUS_ITERATION_ENABLED: Optional[bool] = None  # 研究员+ECC+部门路由（小时去重）
    HERMES_ECC_EXPERT_REVIEW_ENABLED: Optional[bool] = None
    HERMES_ECC_LLM_REVIEW_ENABLED: Optional[bool] = None
    HERMES_ECC_LLM_REVIEW_MAX_CANDIDATES: int = 3
    HERMES_WECHAT_WEBHOOK_URL: str = ""  # 企业微信/Server酱等文本 Webhook，与飞书并行
    HERMES_OPS_DRAIN_LIMIT: int = 3  # Hermes 每轮仅 drain 少量队列，不与客户抢 worker
    # 平台生存基金（财迷疯 · 万里汇 WorldFirst）
    PLATFORM_SURVIVAL_ENABLED: bool = True
    PLATFORM_SURVIVAL_PRIMARY_RAIL: str = "worldfirst"
    PLATFORM_SURVIVAL_DAILY_TARGET_CNY_MINOR: int = 100000
    SURVIVAL_WORLDFIRST_CLIENT_ID: Optional[str] = None
    SURVIVAL_WORLDFIRST_WEBHOOK_SECRET: Optional[str] = None
    # PC-04 平台账号会话巡检配置（每日低峰纯 DB 判定过期，不触网）
    PLATFORM_SESSION_PATROL_HOUR: int = 4
    PLATFORM_SESSION_PATROL_MINUTE: int = 15
    PLATFORM_COOKIE_STALE_DAYS: int = 30
    # 财迷疯 · 摸金校尉分身（与 SaaS Hermes 维护宪法隔离）
    HERMES_GREEDY_AVATAR_ENABLED: bool = True
    HERMES_GREEDY_AUTO_PUBLISH_ENABLED: Optional[bool] = None
    HERMES_GREEDY_REVENUE_LOOP_SCHEDULER_ENABLED: Optional[bool] = None
    HERMES_GREEDY_REVENUE_LOOP_INTERVAL_HOURS: int = 24
    HERMES_GREEDY_DEFAULT_LOCALE: str = "global"
    HERMES_GREEDY_ENDURANCE_TICK_MINUTES: int = 60
    HERMES_GREEDY_ENDURANCE_SCHEDULER_ENABLED: Optional[bool] = None
    HERMES_GREEDY_DIGEST_SCHEDULER_ENABLED: Optional[bool] = None
    HERMES_GREEDY_DIGEST_POLL_MINUTES: int = 30
    HERMES_GREEDY_DIGEST_WEEKDAY: int = 0  # 0=Monday
    HERMES_GREEDY_DIGEST_HOUR: int = 9
    HERMES_GREEDY_DIGEST_TIMEZONE: str = "Asia/Shanghai"
    HERMES_GREEDY_DIGEST_WEBHOOK_URL: str = ""
    HERMES_GREEDY_PUBLISH_TENANT_ID: str = ""
    HERMES_GREEDY_BOOTSTRAP_ON_STARTUP: Optional[bool] = None
    OPS_AUTOPILOT_DEV_ENABLED: Optional[bool] = None
    OPS_AUTOPILOT_INTERVAL_MINUTES: int = 120
    @property
    def ops_autopilot_dev_active(self) -> bool:
        """ops_autopilot_dev_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.OPS_AUTOPILOT_DEV_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "development"

    @property
    def command_center_prewarm_active(self) -> bool:
        """云端 Redis 开启时后台预热司令部快照（用户打开亚秒级）。"""
        raw = (os.getenv("COMMAND_CENTER_PREWARM_ENABLED") or "").strip().lower()
        if raw in ("0", "false", "no", "off"):
            return False
        if (self.ENVIRONMENT or "").strip().lower() == "development":
            return False
        return bool(self.REDIS_ENABLED)

    @property
    def greedy_bootstrap_on_startup(self) -> bool:
        """greedy_bootstrap_on_startup。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.HERMES_GREEDY_AVATAR_ENABLED:
            return False
        flag = self.HERMES_GREEDY_BOOTSTRAP_ON_STARTUP
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    @property
    def greedy_endurance_scheduler_active(self) -> bool:
        """greedy_endurance_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.HERMES_GREEDY_AVATAR_ENABLED:
            return False
        flag = self.HERMES_GREEDY_ENDURANCE_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # Hermes × agency-orchestrator 专家角色库（产品内嵌 YAML DAG，不依赖 Node 生产部署）
    HERMES_AGENCY_ORCHESTRATOR_ENABLED: bool = True
    AGENCY_ROLES_DIR: Optional[str] = None
    AGENCY_WORKFLOWS_DIR: Optional[str] = None
    AGENCY_ORCHESTRATOR_CLI_ENABLED: bool = False  # 开发机可选 npx ao run 对照
    HERMES_AGENCY_LLM_ENABLED: bool = True
    HERMES_AGENCY_DEFAULT_PROVIDER: Optional[str] = None
    HERMES_AGENCY_PROVIDER_CHAIN: str = (
        "hermes-cli,ollama,gemini-cli,deepseek,claude-code,copilot-cli,codex-cli,openai,claude"
    )
    HERMES_AGENCY_CLI_TIMEOUT_SEC: int = 600
    HERMES_AGENCY_OLLAMA_MODEL: str = "llama3.1"
    HERMES_AGENCY_AUTO_DOCKER_OLLAMA: bool = False  # bootstrap 时尝试 docker compose 起 Ollama
    HERMES_AGENCY_AUTO_NPM_INSTALL: bool = False  # 生产默认关；仅开发机或显式开启
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    @property
    def hermes_site_patrol_scheduler_active(self) -> bool:
        """hermes_site_patrol_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.HERMES_SITE_PATROL_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    @property
    def greedy_revenue_loop_scheduler_active(self) -> bool:
        """greedy_revenue_loop_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.HERMES_GREEDY_AVATAR_ENABLED:
            return False
        flag = self.HERMES_GREEDY_REVENUE_LOOP_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    @property
    def greedy_survival_digest_scheduler_active(self) -> bool:
        """greedy_survival_digest_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self.HERMES_GREEDY_AVATAR_ENABLED:
            return False
        flag = self.HERMES_GREEDY_DIGEST_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    @property
    def hermes_auto_remediation_active(self) -> bool:
        """hermes_auto_remediation_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.HERMES_AUTO_REMEDIATION_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    @property
    def hermes_ops_autopilot_active(self) -> bool:
        """hermes_ops_autopilot_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.HERMES_OPS_AUTOPILOT_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # DeerFlow 2.0：超级智能体框架，支持子 Agent 编排、沙箱执行、Skills 系统
    DEERFLOW_VERSION: str = "1.0"
    DEERFLOW_GATEWAY_URL: Optional[str] = None
    DEERFLOW_LANGGRAPH_URL: Optional[str] = None
    # DeerFlow：调度器每日跑 drain；自动入队须显式开启 + 套餐合格
    DEERFLOW_SCHEDULER_ENABLED: Optional[bool] = None
    DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED: Optional[bool] = None
    DEERFLOW_SCHEDULE_HOUR: int = 7
    DEERFLOW_SCHEDULE_MINUTE: int = 30
    DEERFLOW_SCHEDULE_TENANT_IDS: str = ""
    DEERFLOW_SCHEDULE_MAX_TENANTS: int = 50
    DEERFLOW_SCHEDULE_PLAN_CODES: str = "pro,enterprise,flagship"
    DEERFLOW_SCHEDULE_MONTHLY_LIMIT_PER_TENANT: int = 4
    DEERFLOW_SCHEDULE_MESSAGE: str = ""
    DEERFLOW_RUN_PENDING_LIMIT: int = 10
    DEERFLOW_TENANT_CELERY_ENABLED: Optional[bool] = None
    INCLUSION_PROBE_REAL_ENABLED: Optional[bool] = None
    # 出海参谋：UN Comtrade 定时刷新海关公开统计（默认每周一 03:30）
    TRADE_INTEL_SCHEDULER_ENABLED: Optional[bool] = None
    TRADE_INTEL_REFRESH_WEEKDAY: int = 0
    TRADE_INTEL_REFRESH_HOUR: int = 3
    TRADE_INTEL_REFRESH_MINUTE: int = 30
    TRADE_INTEL_REFRESH_SEED_DB: bool = True
    UN_COMTRADE_USE_PREVIEW: bool = True
    UN_COMTRADE_SUBSCRIPTION_KEY: Optional[str] = None
    @property
    def trade_intel_scheduler_active(self) -> bool:
        """trade_intel_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.TRADE_INTEL_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # Rank Guard RUM 指标（可选，来自监控/前端上报）
    RUM_LCP_MS: Optional[int] = None
    RUM_INP_MS: Optional[int] = None
    RUM_ERROR_RATE: Optional[float] = None
    @property
    def deerflow_tenant_celery_active(self) -> bool:
        """deerflow_tenant_celery_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.DEERFLOW_TENANT_CELERY_ENABLED
        if flag is not None:
            return bool(flag)
        return True

    @property
    def deerflow_schedule_auto_enqueue_active(self) -> bool:
        """deerflow_schedule_auto_enqueue_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.DEERFLOW_SCHEDULE_AUTO_ENQUEUE_ENABLED
        if flag is not None:
            return bool(flag)
        return False

    @property
    def deerflow_scheduler_active(self) -> bool:
        """deerflow_scheduler_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.DEERFLOW_SCHEDULER_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # 每日自主运营闭环（串联 tech_radar → geo_probe → content_gen → publish → inquiry → attribution → feedback）
    DAILY_AUTONOMOUS_CYCLE_ENABLED: Optional[bool] = None
    DAILY_AUTONOMOUS_CYCLE_HOUR: int = 6
    DAILY_AUTONOMOUS_CYCLE_MINUTE: int = 0
    @property
    def daily_autonomous_cycle_active(self) -> bool:
        """daily_autonomous_cycle_active。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        flag = self.DAILY_AUTONOMOUS_CYCLE_ENABLED
        if flag is not None:
            return bool(flag)
        return (self.ENVIRONMENT or "").strip().lower() == "production"

    # 百度文心一言
    AI_BAIDU_API_KEY: Optional[str] = None
    AI_BAIDU_BASE_URL: str = "https://qianfan.baidubce.com/v2"
    # 阿里通义千问
    AI_ALIYUN_API_KEY: Optional[str] = None
    AI_ALIYUN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 字节豆包
    AI_BYTE_API_KEY: Optional[str] = None
    AI_BYTE_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    # 智谱GLM
    AI_ZHIPU_API_KEY: Optional[str] = None
    AI_ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    # Kimi (月之暗面)
    AI_KIMI_API_KEY: Optional[str] = None
    AI_KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    # 零一万物
    AI_01WANWU_API_KEY: Optional[str] = None
    AI_01WANWU_BASE_URL: str = "https://api.lingyiwanwu.com/v1"
    # 硅基流动 (SiliconFlow)
    AI_SILICONFLOW_API_KEY: Optional[str] = None
    AI_SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    # MiniMax
    AI_MINIMAX_API_KEY: Optional[str] = None
    AI_MINIMAX_BASE_URL: str = "https://api.minimaxi.chat/v1"
    # 讯飞星火（LLM，与下方 LFASR 听写密钥无关）
    AI_XUNFEI_API_KEY: Optional[str] = None
    AI_XUNFEI_BASE_URL: str = "https://spark-api-open.xf-yun.com/v1"
    # 讯飞语音转写（中文片出海 · 录音文件转写大模型 WebAPI）
    XFYUN_LFASR_APP_ID: str = ""
    XFYUN_LFASR_API_KEY: str = ""
    XFYUN_LFASR_SECRET_KEY: str = ""
    XFYUN_LFASR_ENABLED: bool = False
    XFYUN_LFASR_PREFERRED: bool = True
    XFYUN_LFASR_BASE_URL: str = "https://office-api-ist-dx.iflyaisol.com"
    XFYUN_LFASR_LANGUAGE: str = "autodialect"
    XFYUN_LFASR_POLL_INTERVAL_SEC: float = 5.0
    XFYUN_LFASR_MAX_WAIT_SEC: int = 1800
    # Vozo AI 视频翻译/配音/口型（Enterprise API，可选上游）
    VOZO_API_KEY: str = ""
    VOZO_API_BASE_URL: str = "https://api.vozo.ai"
    VOZO_WEBHOOK_SECRET: str = ""
    # 开源本地化 sidecar / CLI（MS-H，对标 Vozo/山海智影；未部署不得假成功）
    KRILLINAI_CLI_PATH: str = ""
    KRILLINAI_SERVICE_URL: str = ""
    LINLY_DUBBING_BASE_URL: str = ""
    YOUDUB_WEBUI_BASE_URL: str = ""
    VIDEOLINGO_BASE_URL: str = ""
    V2VT_SERVICE_URL: str = ""
    NARRATOR_AI_BASE_URL: str = ""
    PYVIDEOTRANS_CLI_PATH: str = ""
    PYVIDEOTRANS_BASE_URL: str = ""
    MUSETALK_SERVICE_URL: str = ""
    OPENSOURCE_LOCALIZATION_PREFERRED: str = ""  # 留空则按 OPTIMAL_PICK_ORDER 智能选择
    CROSS_BORDER_PUBLIC_BASE_URL: str = "http://127.0.0.1:8001"  # sidecar 拉取 /uploads 视频用
    # Web 剪辑器嵌入（MS-C/MS-D PoC；未配置则前端显示「未部署」不 iframe 假页面）
    FLY_CUT_EMBED_URL: str = ""
    OPENCUT_EMBED_URL: str = ""
    AI_MIMO_API_KEY: Optional[str] = None
    AI_MIMO_BASE_URL: str = "https://api.xiaomimimo.com/v1"
    # Meta Llama（开源，通过托管服务访问）
    AI_META_API_KEY: Optional[str] = None
    AI_META_BASE_URL: str = ""
    # GPU 优先级链：NVIDIA NIM（免费额度）→ DeepSeek → OpenAI（可选兜底）
    GPU_CODE_PROVIDER_PRIORITY: list[str] = ["nvidia", "deepseek"]
    GPU_DEFAULT_PROVIDER_PRIORITY: list[str] = ["nvidia", "deepseek", "openai"]
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    # 飞书机器人配置
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""
    FEISHU_EVENT_ENCRYPT_KEY: str = ""
    FEISHU_BOT_NAME: str = "优丁建材助手"
    FEISHU_API_BASE_URL: str = "https://open.feishu.cn/open-apis"
    FEISHU_DEFAULT_RECEIVER: str = ""  # 默认消息接收者open_id
    FEISHU_DEFAULT_GROUP_ID: str = ""  # 默认消息群组ID
    FEISHU_NOTIFICATION_ENABLED: bool = True  # 是否启用飞书通知（默认开启）
    FEISHU_WEBHOOK_URL: str = ""  # 飞书群机器人Webhook地址
    FEISHU_OPS_WEBHOOK_URL: str = ""  # 运维通知飞书群机器人 Webhook 地址
    # 询盘 IM / 社媒 Worker（MOD-02 · Lane I/P）
    INQUIRY_WEBHOOK_SECRET: str = ""
    SOCIAL_INTERACTION_WEBHOOK_SECRET: str = ""
    WECOM_CORP_ID: str = ""
    WECOM_AGENT_ID: str = ""
    WECOM_AGENT_SECRET: str = ""
    WECOM_PUSH_TO_USERIDS: str = ""  # 仅开发兜底；生产推送用租户后台 /client/wecom-push-config
    DOUYIN_APP_ID: str = ""
    DOUYIN_APP_SECRET: str = ""
    # 国密（SM2/SM3/SM4）与创始人专属调试 — 见 docs/安全与国密-源码调试说明.md
    GM_SM4_KEY: str = ""  # 32 位十六进制优先；空则派生自 SECRET_KEY
    GM_SM2_PUBLIC_KEY: str = ""
    GM_SM2_PRIVATE_KEY: str = ""
    FOUNDER_WECHAT_OPENID: str = ""  # 创始人微信 ID（wechat_xxx 或仅填微信号如 qq979072138）
    FOUNDER_WECHAT_BIND_KEY: str = ""  # 创始人微信号（与 OPENID 二选一或同时填同一串）
    FOUNDER_ADMIN_USERNAME: str = ""  # 可选：超管登录名绑死（如与微信号相同）
    EXPORT_PLATFORM_FOUNDER_ONLY: bool = True  # 全平台 CSV 导出仅创始人（成果保护）
    FOUNDER_DEBUG_TOKEN: str = ""  # 开发兜底；生产优先 FOUNDER_WECHAT_OPENID
    FOUNDER_DEBUG_IPS: str = ""  # 可选逗号分隔 IP/CIDR，空则不限制 IP
    # 安全配置
    RATE_LIMIT_MAX_REQUESTS: int = 200
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_REQUIRE_REDIS: bool = True  # 生产环境强制要求 Redis；False 时允许内存降级
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: list[str] = [
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "dwg",
        "dxf",
    ]
    # 邮件服务配置（SMTP）
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    # 零成本获客：Resend 免费版（3000 封/月免费）
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""
    # SMTP 兼容字段（email_send_service 使用）
    @property
    def SMTP_HOST(self) -> str:
        """SMTP_HOST。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.SMTP_SERVER

    @property
    def SMTP_USER(self) -> str:
        """SMTP_USER。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.SMTP_USERNAME

    @property
    def SMTP_USE_TLS(self) -> bool:
        """SMTP_USE_TLS。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self.SMTP_PORT in (587, 2525)

    FRONTEND_URL: str = "http://localhost:3000"
    # 第三方 OAuth（管理端登录）
    OAUTH_REDIRECT_URI: str = "http://localhost:5173/login/oauth-callback"
    OAUTH_DEV_BYPASS: bool = False  # 仅开发环境可设为 True，生产环境强制禁用
    QQ_APP_ID: str = ""
    QQ_APP_KEY: str = ""
    WECHAT_OPEN_APP_ID: str = ""
    WECHAT_OPEN_APP_SECRET: str = ""
    DINGTALK_APP_ID: str = ""
    DINGTALK_APP_SECRET: str = ""

    # Browser Runtime 远程 CDP 集群与并发护栏配置（建议 2 落地）
    BROWSER_RUNTIME_WS_ENDPOINT: str = ""  # 远程无头浏览器连接端点，如 ws://browserless:3000
    BROWSER_RUNTIME_MAX_CONCURRENCY: int = 4  # 单节点浏览器最大并发数（防内存击穿）

    # 租户解析分布式二级缓存配置（建议 1 落地）
    TENANT_CACHE_REDIS_ENABLED: bool = True  # 是否优先使用 Redis 作为分布式租户缓存
    TENANT_CACHE_TTL_SEC: int = 60  # 租户信息缓存过期时间（秒）

    def __init__(self, **kwargs):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        super().__init__(**kwargs)
        # 根据环境设置DEBUG
        if self.ENVIRONMENT == "development":
            self.DEBUG = True
            # 未显式配置时禁用 Redis，避免手起 uvicorn 时每请求等 2s 连接超时
            if os.getenv("REDIS_ENABLED") is None:
                self.REDIS_ENABLED = False
            if os.getenv("LOGIN_BF_USE_REDIS") is None:
                self.LOGIN_BF_USE_REDIS = False

        self._init_secret_key()
        self._init_jwt_secret_key()
        self._init_production_key_validation()
        self._init_seo_matrix_sqlite()
        self._init_database_url_resolution()
        self._init_db_type_validation()

    def _init_secret_key(self) -> None:
        """SECRET_KEY 强制校验（与 JWT 同等重要）。"""
        _weak_secret_literals = {
            "",
            "your-secret",
            "your-jwt",
            "replace-me",
            "your-password",
            "your-key",
            "dev-secret-key-for-development-only-keep-it-safe",
            "changeme",
        }
        _secret_value = str(self.SECRET_KEY or "").strip()
        if (not _secret_value
                or len(_secret_value) < 32
                or _secret_value in _weak_secret_literals):
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "[安全错误] 生产环境必须配置强随机 SECRET_KEY(>=32字符)。"
                    "请通过环境变量设置：export SECRET_KEY=$(python -c \"import secrets; print(secrets.token_hex(32))\")"
                )
            # dev: 优先从 auto-secret 文件恢复(确保跨重启稳定),否则生成
            persisted = self._load_persisted_dev_secret("secret")
            if persisted:
                self.SECRET_KEY = persisted
                warnings.warn("[DEV] SECRET_KEY 为占位符,已从 logs/auto-secret-dev.txt 复用", stacklevel=2)
            else:
                generated = secrets.token_hex(32)
                self.SECRET_KEY = generated
                self._persist_dev_secret("secret", generated)
                warnings.warn(
                    "[DEV] SECRET_KEY 为占位符,已生成强随机密钥并写入 logs/auto-secret-dev.txt"
                    "(跨重启复用,JWT 不会失效)", stacklevel=2)

    def _init_jwt_secret_key(self) -> None:
        """JWT 密钥强制校验。"""
        _weak_secret_literals = {
            "",
            "your-secret",
            "your-jwt",
            "replace-me",
            "your-password",
            "your-key",
            "dev-secret-key-for-development-only-keep-it-safe",
            "changeme",
        }
        _jwt_value = str(self.JWT_SECRET_KEY or "").strip()
        if (not _jwt_value
                or len(_jwt_value) < 32
                or _jwt_value in _weak_secret_literals):
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "[安全错误] 生产环境必须配置强随机 JWT_SECRET_KEY(>=32字符)。"
                    "请通过环境变量设置：export JWT_SECRET_KEY=$(python -c \"import secrets; print(secrets.token_hex(32))\")"
                )
            persisted = self._load_persisted_dev_secret("jwt")
            if persisted:
                self.JWT_SECRET_KEY = persisted
                warnings.warn("[DEV] JWT_SECRET_KEY 为占位符,已从 logs/auto-secret-dev.txt 复用", stacklevel=2)
            else:
                generated = secrets.token_hex(32)
                self.JWT_SECRET_KEY = generated
                self._persist_dev_secret("jwt", generated)
                warnings.warn(
                    "[DEV] JWT_SECRET_KEY 为占位符,已生成强随机密钥并写入 logs/auto-secret-dev.txt",
                    stacklevel=2)

    def _init_production_key_validation(self) -> None:
        """生产环境：关键密钥不得使用示例占位符。"""
        if self.ENVIRONMENT == "production":
            weak_patterns = [
                "change-me", "change_me", "changeme",
                "your-secret", "your-jwt", "replace-me",
                "your-password", "your-key",
            ]
            for key_name in ["JWT_SECRET_KEY", "REDIS_PASSWORD",
                             "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY",
                             "SMTP_PASSWORD"]:
                val = str(getattr(self, key_name, "") or "").lower()
                for pat in weak_patterns:
                    if pat in val:
                        raise ValueError(
                            f"[安全错误] 生产环境 {key_name} 包含弱密码模式 '{pat}'。"
                            f"请立即更换为强随机值。"
                        )
            # Also check DATABASE_URL for weak credentials
            db_url = str(getattr(self, "DATABASE_URL", "") or "").lower()
            for pat in weak_patterns:
                if pat in db_url:
                    raise ValueError(
                        f"[安全错误] 生产环境 DATABASE_URL 包含弱密码模式 '{pat}'。"
                        f"请立即更换为强随机值。"
                    )

    def _init_seo_matrix_sqlite(self) -> None:
        """解析 SEO Matrix 数据库的 sqlite 回退路径。"""
        has_matrix_mysql = bool(
            (self.SEO_MATRIX_DATABASE_URL or "").strip()
            or (
                (self.SEO_MATRIX_DB_HOST or "").strip()
                and (self.SEO_MATRIX_DB_NAME or "").strip()
                and self.SEO_MATRIX_DB_USER is not None
                and str(self.SEO_MATRIX_DB_USER).strip() != ""
            )
        )
        if not has_matrix_mysql and not self.SEO_MATRIX_SQLITE_PATH:
            cand = Path(__file__).resolve(
            ).parents[3] / "seo-backend" / "database" / "database.sqlite"
            if cand.is_file():
                self.SEO_MATRIX_SQLITE_PATH = str(cand)

    def _init_database_url_resolution(self) -> None:
        """sqlite 类型时解析数据库路径。"""
        if self.DB_TYPE == "sqlite" and "postgresql" not in self.DATABASE_URL:
            from app.core.sqlite_paths import resolve_sqlite_database_url
            self.DATABASE_URL = resolve_sqlite_database_url(self.DATABASE_URL)

    def _init_db_type_validation(self) -> None:
        """数据库类型 / 驱动一致性校验(P3-015)。"""
        db_url = (self.DATABASE_URL or "").lower()
        if self.DB_TYPE == "postgresql":
            if "postgresql" not in db_url and "postgres://" not in db_url:
                raise ValueError(
                    f"[配置错误] DB_TYPE=postgresql 但 DATABASE_URL 不含 postgresql 协议:\n"
                    f"  当前 URL: {self.DATABASE_URL}\n"
                    f"  正确格式: postgresql+asyncpg://user:pass@host:5432/dbname"
                )
            # 驱动建议:asyncpg for SQLAlchemy 2.0 async
            if "postgresql://" in db_url and "+asyncpg" not in db_url:
                warnings.warn(
                    f"[配置建议] DB_TYPE=postgresql 时建议在 URL 中显式声明驱动 +asyncpg,"
                    f"当前 URL: {self.DATABASE_URL}",
                    stacklevel=2,
                )
        elif self.DB_TYPE == "sqlite":
            if "sqlite" not in db_url:
                raise ValueError(
                    f"[配置错误] DB_TYPE=sqlite 但 DATABASE_URL 不含 sqlite 协议:\n"
                    f"  当前 URL: {self.DATABASE_URL}"
                )
        elif self.DB_TYPE not in ("sqlite", "postgresql"):
            warnings.warn(
                f"[配置警告] 未知 DB_TYPE='{self.DB_TYPE}',"
                f"仅支持 sqlite / postgresql",
                stacklevel=2,
            )

    def is_production(self) -> bool:
        """是否为生产环境。"""
        return self.ENVIRONMENT == "production"

    # === Dev 密钥持久化助手(仅 dev 使用) ===
    @staticmethod
    def _dev_secret_file() -> Path:
        """dev 模式下持久化自动生成密钥的位置
        优先级:1) ENV_FILE 同目录的 logs/  2) backend/logs/
        文件已在 .gitignore 中,不会泄露。
        """
        backend_root = Path(__file__).resolve().parents[2]
        return backend_root / "logs" / "auto-secret-dev.txt"

    @classmethod
    def _load_persisted_dev_secret(cls, kind: str) -> Optional[str]:
        """从持久化文件加载 dev 密钥。kind: 'secret' | 'jwt'"""
        try:
            f = cls._dev_secret_file()
            if not f.is_file():
                return None
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(f"#"):
                    continue
                if line.startswith(f"{kind}="):
                    return line.split("=", 1)[1].strip()
        except Exception:  # noqa: BLE001
            return None
        return None

    @classmethod
    def _persist_dev_secret(cls, kind: str, value: str) -> None:
        """把自动生成的 dev 密钥写入 logs/auto-secret-dev.txt
        供后续启动复用,JWT 不会因重启失效。
        """
        try:
            f = cls._dev_secret_file()
            f.parent.mkdir(parents=True, exist_ok=True)
            existing: dict[str, str] = {}
            if f.is_file():
                for line in f.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        existing[k.strip()] = v.strip()
            existing[kind] = value
            # 写出时附说明,且限制文件权限为 0600(类 Unix 生效,Windows 通过 ACL)
            lines = [
                "# Auto-generated dev secrets — DO NOT commit, do not use in production",
                "# Replaced automatically on each start when .env has placeholder values",
                "",
            ]
            for k, v in existing.items():
                lines.append(f"{k}={v}")
            content = "\n".join(lines) + "\n"
            f.write_text(content, encoding="utf-8")
            # Unix: 限制文件权限为 0600(仅所有者读写)
            # Windows: chmod 无效,但 NTFS 继承自父目录权限;
            # 无论如何,文件已在 .gitignore 中,不会泄露到版本库
            try:
                import os
                os.chmod(f, 0o600)
            except (OSError, NotImplementedError):  # noqa: BLE001
                # Windows 或受限环境:忽略,文件安全由 NTFS ACL / .gitignore 保护
                pass
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"[DEV] 持久化 {kind} 到文件失败: {exc}", stacklevel=2)


settings = Settings()
