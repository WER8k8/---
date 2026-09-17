# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from app.core.no_fake_delivery import stamp_mock
import logging
import os
import random
import time
import asyncio
from threading import Lock
from typing import Any, Dict, Optional

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        ChatOpenAI = None

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    try:
        from langchain.schema import HumanMessage, SystemMessage
    except ImportError:
        HumanMessage = None
        SystemMessage = None

# 导入其他提供商
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

# 导入DeepSeek支持
try:
    from langchain_openai import ChatOpenAI as ChatDeepSeek
except ImportError:
    ChatDeepSeek = None

from app.core.config import settings
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SmartAIResponse(str):
    """兼具字符串与字典特性的智能响应对象，保证多模型返回类型绝对兼容。"""
    def __new__(cls, content: str, meta: Optional[dict] = None):
        obj = str.__new__(cls, content)
        obj._meta = meta or {"content": content, "status": "success"}
        return obj

    def get(self, key, default=None):
        return self._meta.get(key, default)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self._meta.get(item, str(self))
        return super().__getitem__(item)

    def __setitem__(self, key, value):
        self._meta[key] = value


class AIEngine:
    _instance = None
    _lock = Lock()
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AIEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.llms = {}
        self.current_provider = None
        self._init_llms()
        self._initialized = True

    @staticmethod
    def _brand_name(content: str = "") -> str:
        """从内容或租户设置中提取品牌名，避免硬编码。"""
        try:
            from app.core.config import settings
            return getattr(settings, "SITE_NAME", "") or "优丁建材"
        except Exception:
            return "优丁建材"

    def _init_nvidia_llms(self):
        """初始化 NVIDIA NIM 多个场景模型。"""
        if settings.AI_NVIDIA_API_KEY:
            base_url = settings.AI_NVIDIA_BASE_URL
            api_key = settings.AI_NVIDIA_API_KEY
            models = settings.AI_NVIDIA_MODELS
            for model_type, model_name in models.items():
                try:
                    llm = ChatOpenAI(
                        api_key=api_key,
                        model=model_name,
                        base_url=base_url,
                        temperature=0.3,
                        max_tokens=2000,
                        request_timeout=60,
                    )
                    self.llms[model_type] = llm
                    logger.info(f"Initialized NVIDIA model: {model_name} ({model_type})")
                except Exception as e:
                    logger.warning(f"Failed to initialize {model_name}: {e}")

    def _init_deepseek_llm(self):
        """初始化 DeepSeek 作为国内备选 / 成本优化模型。"""
        if settings.AI_DEEPSEEK_API_KEY:
            try:
                deepseek_llm = ChatOpenAI(
                    api_key=settings.AI_DEEPSEEK_API_KEY,
                    model="deepseek-v4",
                    base_url="https://api.deepseek.com/v1",
                    temperature=0.3,
                    max_tokens=2000,
                    request_timeout=60,
                )
                self.llms["deepseek"] = deepseek_llm
                if "cost_optimized" not in self.llms:
                    self.llms["cost_optimized"] = deepseek_llm
                logger.info("✅ Initialized DeepSeek V4 Pro (cost optimized)")
            except Exception as e:
                logger.warning(f"Failed to initialize DeepSeek V4 Pro: {e}")

    def _init_anthropic_llm(self):
        """初始化 Anthropic Claude（高质量任务）。"""
        if settings.AI_ANTHROPIC_API_KEY:
            try:
                if ChatAnthropic:
                    claude_llm = ChatAnthropic(
                        api_key=settings.AI_ANTHROPIC_API_KEY,
                        model="claude-3-5-sonnet-20241022",
                        temperature=0.3,
                        max_tokens=2000,
                        request_timeout=60,
                    )
                    self.llms["claude"] = claude_llm
                    self.llms["high_quality"] = claude_llm  # 高质量模型
                    logger.info("✅ Initialized Anthropic Claude 3.5 Sonnet (high quality)")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude: {e}")

    def _init_openai_llm(self):
        """初始化 OpenAI/兼容网关模型（注入用户指定的 bankofai.io 及 qwen3.8-flash / glm-5.3-flash）。"""
        if getattr(settings, "AI_OPENAI_API_KEY", None):
            base_url = getattr(settings, "AI_OPENAI_BASE_URL", None) or "https://api.bankofai.io/v1"
            primary_model = getattr(settings, "AI_OPENAI_MODEL", "qwen3.8-flash")
            fallback_model = getattr(settings, "AI_OPENAI_FALLBACK_MODEL", "glm-5.3-flash")
            api_key = settings.AI_OPENAI_API_KEY
            try:
                if ChatOpenAI:
                    primary_llm = ChatOpenAI(
                        api_key=api_key,
                        model=primary_model,
                        base_url=base_url,
                        temperature=0.3,
                        max_tokens=3000,
                        request_timeout=60,
                    )
                    self.llms["openai"] = primary_llm
                    self.llms["general"] = primary_llm
                    self.llms["qwen"] = primary_llm
                    if "high_quality" not in self.llms:
                        self.llms["high_quality"] = primary_llm
                    if "cost_optimized" not in self.llms:
                        self.llms["cost_optimized"] = primary_llm
                    logger.info("✅ 已成功挂载主力模型: %s (网关: %s)", primary_model, base_url)

                    # 初始化备选模型（如 glm-5.3-flash）
                    fallback_llm = ChatOpenAI(
                        api_key=api_key,
                        model=fallback_model,
                        base_url=base_url,
                        temperature=0.3,
                        max_tokens=3000,
                        request_timeout=60,
                    )
                    self.llms["fallback"] = fallback_llm
                    self.llms["glm"] = fallback_llm
                    logger.info("✅ 已成功挂载备用模型: %s (网关: %s)", fallback_model, base_url)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI compatible model: {e}")

    def _init_gemini_llm(self):
        """初始化 Google Gemini（多语言任务）。"""
        if settings.AI_GEMINI_API_KEY:
            try:
                if ChatGoogleGenerativeAI:
                    gemini_llm = ChatGoogleGenerativeAI(
                        api_key=settings.AI_GEMINI_API_KEY,
                        model="gemini-1.5-pro",
                        temperature=0.3,
                        max_tokens=2000,
                    )
                    self.llms["gemini"] = gemini_llm
                    self.llms["multilingual"] = gemini_llm  # 多语言模型
                    logger.info("✅ Initialized Google Gemini 1.5 Pro (multilingual)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

    def _init_llms(self):
        """初始化多个 LLM 引擎；国内默认 NVIDIA NIM 免费额度优先，OpenAI 可选兜底。"""
        try:
            # 1. NVIDIA NIM（免费额度，跨境/语言桥默认走场景模型）
            self._init_nvidia_llms()
            # 2. DeepSeek（国内备选，不覆盖 NVIDIA 已注册的场景键）
            self._init_deepseek_llm()
            # 3. 初始化Anthropic Claude（高质量任务）
            self._init_anthropic_llm()
            # 4. OpenAI（可选；不覆盖 NVIDIA 已占用的场景键）
            self._init_openai_llm()
            # 5. 初始化Google Gemini（多语言任务）
            self._init_gemini_llm()
            # 6. 如果没有任何模型初始化成功
            if not self.llms:
                mvp_launch = settings.MVP_LAUNCH
                if settings.ENVIRONMENT == "production" and not mvp_launch:
                    raise RuntimeError(
                        "未配置任何AI提供商。生产环境需要至少配置一个AI提供商，"
                        "或设置 MVP_LAUNCH=1 以主站商用 MVP 模式启动（AI 功能降级为 mock）。"
                        "请配置 NVIDIA NIM（AI_NVIDIA_API_KEY）、DeepSeek 或其它 AI 提供商密钥。"
                    )
                logger.warning(
                    "No AI providers configured. Using mock responses"
                    + (" (MVP_LAUNCH)" if mvp_launch else " (non-production)"),
                )
                self.llms["mock"] = MockLLM()
                self.current_provider = "mock"
                return

            # 7. 默认提供商：NVIDIA NIM > DeepSeek > Gemini > Claude > OpenAI
            if "inference" in self.llms or (
                settings.AI_NVIDIA_API_KEY and any(
                    k in self.llms for k in ("general", "article", "logic")
                )
            ):
                self.current_provider = "nvidia"
            elif "deepseek" in self.llms:
                self.current_provider = "deepseek"
            elif "gemini" in self.llms:
                self.current_provider = "gemini"
            elif "claude" in self.llms:
                self.current_provider = "claude"
            elif "openai" in self.llms:
                self.current_provider = "openai"
            else:
                self.current_provider = list(self.llms.keys())[0]

        except Exception as e:
            logger.error(f"Failed to initialize LLMs: {e}")
            if settings.ENVIRONMENT == "production":
                raise RuntimeError(
                    f"AI服务初始化失败: {e}。生产环境无法使用Mock模式。"
                )
            else:
                logger.warning("Falling back to mock mode due to initialization failure.")
                self.llms["mock"] = MockLLM()

    def update_nvidia_scenario(self, scenario: str, model_name: str) -> None:
        """热更新单个 NVIDIA 场景模型（管理后台切换后立即生效）。"""
        if not settings.AI_NVIDIA_API_KEY or not model_name:
            return
        if not model_name.startswith("nvidia/cosmos-"):
            try:
                llm = ChatOpenAI(
                    api_key=settings.AI_NVIDIA_API_KEY,
                    model=model_name,
                    base_url=settings.AI_NVIDIA_BASE_URL,
                    temperature=0.3,
                    max_tokens=2000,
                    request_timeout=60,
                )
                self.llms[scenario] = llm
                logger.info("Updated NVIDIA scenario model: %s -> %s", scenario, model_name)
            except Exception as e:
                logger.warning("Failed to update NVIDIA scenario %s: %s", scenario, e)

    def _get_llm(self, model_type: str = "general", task_complexity: str = "medium"):
        """获取指定类型的LLM，支持自动切换和智能路由
        
        Args:
            model_type: 模型类型 (general, chinese, logic, code, inference, article, …)
            task_complexity: 任务复杂度 (simple, medium, complex)
                - simple/medium/complex: 优先 NVIDIA 场景模型 → DeepSeek → 其它
        """
        # 智能路由：根据复杂度选择模型
        if task_complexity == "simple":
            for key in ("inference", "cost_optimized", "deepseek", "general", "openai"):
                if key in self.llms:
                    return self.llms[key]

        elif task_complexity == "medium":
            for key in ("inference", "general", "article", "deepseek", "gemini", "openai"):
                if key in self.llms:
                    return self.llms[key]

        elif task_complexity == "complex":
            for key in ("logic", "article", "claude", "gemini", "inference", "openai"):
                if key in self.llms:
                    return self.llms[key]
        
        # 回退逻辑：按model_type或通用模型
        # 优先匹配命名模型
        for key in [model_type, "general", "cost_optimized", "high_quality", "multilingual"]:
            candidate = self.llms.get(key)
            if candidate is not None:
                return candidate

        # 兜底：返回任意一个可用 LLM（含 MockLLM），无则 None
        for v in self.llms.values():
            if v is not None:
                return v
        return None

    def is_available(self) -> bool:
        """is_available。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self.llms) and "mock" not in self.llms

    def switch_provider(self, provider_config: Dict) -> bool:
        """动态切换AI提供商"""
        with self._lock:
            try:
                cfg = provider_config
                llm = self._create_llm(
                    cfg["provider"]["type"],
                    cfg["provider"]["api_key"],
                    cfg["provider"].get("base_url"),
                    cfg["model"]["name"],
                    cfg["model"]["temperature"],
                    cfg["model"]["max_tokens"])
                if llm:
                    self.llms = {cfg["model"]["type"]: llm}
                    self.current_provider = cfg["provider"]["type"]
                    logger.info(f"Switched to {cfg['provider']['type']} provider with model: {cfg['model']['name']}")
                    return True
            except Exception as e:
                logger.error(f"Failed to switch provider: {e}")
            return False

    def _create_llm(
            self,
            provider_type: str,
            api_key: str,
            base_url: str,
            model_name: str,
            temperature: float,
            max_tokens: int):
        """根据提供商类型创建LLM实例"""
        try:
            if provider_type in ("openai", "deepseek"):
                if not ChatOpenAI:
                    raise ImportError("langchain_openai not installed")
                return ChatOpenAI(
                    api_key=api_key,
                    model=model_name,
                    base_url=base_url or None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    request_timeout=60,
                )
            elif provider_type == "anthropic":
                if not ChatAnthropic:
                    raise ImportError("langchain_anthropic not installed")
                return ChatAnthropic(
                    api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    request_timeout=60,
                )
            elif provider_type == "gemini":
                if not ChatGoogleGenerativeAI:
                    raise ImportError("langchain_google_genai not installed")
                return ChatGoogleGenerativeAI(
                    api_key=api_key,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens)
            elif provider_type == "nvidia":
                if not ChatOpenAI:
                    raise ImportError("langchain_openai not installed")
                return ChatOpenAI(
                    api_key=api_key,
                    model=model_name,
                    base_url=base_url or "https://integrate.api.nvidia.com/v1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    request_timeout=60,
                )
            else:
                logger.error(f"Unsupported provider type: {provider_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to create LLM for {provider_type}: {e}")
            return None

    def get_current_provider(self) -> str:
        """获取当前提供商"""
        return self.current_provider

    async def optimize_content(self,
                               content: str,
                               optimization_type: str,
                               keywords: list,
                               task_complexity: str = "medium") -> Dict[str, Any]:
        """优化内容 - 使用中文模型
        
        Args:
            task_complexity: 任务复杂度 (simple, medium, complex)
                - simple: 简单标题/描述优化 -> DeepSeek
                - medium: 中等复杂度 -> DeepSeek
                - complex: 复杂内容重构 -> Claude
        """
        llm = self._get_llm("chinese", task_complexity)
        return await self._generate_response(llm, content, optimization_type, keywords, task_type="optimize")

    async def generate_llms_txt(
            self, business_type: str, keywords: list, 
            task_complexity: str = "simple") -> Dict[str, Any]:
        """生成llms.txt内容 - 使用通用模型
        
        Args:
            task_complexity: 任务复杂度 (simple, medium, complex)
                - simple: 生成llms.txt是简单任务 -> DeepSeek
        """
        llm = self._get_llm("general", task_complexity)
        return await self._generate_response(llm, business_type, keywords, task_type="llms_txt")

    async def analyze_seo(self, url: str, content: str,
                        task_complexity: str = "medium") -> Dict[str, Any]:
        """SEO分析 - 使用逻辑推理模型
        
        Args:
            task_complexity: 任务复杂度 (simple, medium, complex)
                - simple: 基础SEO检查 -> DeepSeek
                - medium: 标准SEO分析 -> DeepSeek
                - complex: 深度SEO审计 -> Claude
        """
        llm = self._get_llm("logic", task_complexity)
        return await self._generate_response(llm, url, content, task_type="seo_analysis")

    async def generate_code(
            self, prompt: str, language: str = "python",
            task_complexity: str = "complex") -> Dict[str, Any]:
        """代码生成 - 使用代码模型
        
        Args:
            task_complexity: 任务复杂度 (simple, medium, complex)
                - simple: 简单代码片段 -> DeepSeek
                - medium: 中等复杂度 -> DeepSeek
                - complex: 复杂系统架构 -> Claude
        """
        llm = self._get_llm("code", task_complexity)
        return await self._generate_response(llm, prompt, language, task_type="code")

    async def generate(
        self,
        prompt: str,
        model: str = "general",
        max_tokens: int = 2500,
        temperature: float = 0.3,
        system_prompt: str = "你是一个精通海外B2B出海贸易、多模态营销与跨境电商的顶级AI业务专家。",
        max_retries: int = 3,
        task_complexity: str | None = None,
    ) -> SmartAIResponse:
        """统一通用生成接口，直接对接注入的 bankofai.io 网关（qwen3.8-flash / glm-5.3-flash）。"""
        api_key = settings.AI_OPENAI_API_KEY or ""
        base_url = getattr(settings, "AI_OPENAI_BASE_URL", "") or "https://api.bankofai.io/v1"
        target_model = getattr(settings, "AI_OPENAI_MODEL", "qwen3.8-flash")
        if model in ("glm", "fallback", "glm-5.3-flash"):
            target_model = getattr(settings, "AI_OPENAI_FALLBACK_MODEL", "glm-5.3-flash")

        import asyncio
        import httpx
        last_error: Exception | None = None
        for attempt in range(max(1, int(max_retries))):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{base_url.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "model": target_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        res_content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        meta = {
                            "content": res_content,
                            "token_usage": usage.get("total_tokens", 0),
                            "model": target_model,
                            "raw": data,
                        }
                        return SmartAIResponse(res_content, meta)
                    else:
                        logger.warning(f"大模型网关返回异常 {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                last_error = e
                logger.warning(f"大模型网关第 {attempt + 1}/{max_retries} 次调用失败: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.5 * (attempt + 1))
        if last_error is not None:
            logger.error(f"直接调用大模型网关最终失败: {last_error}")

        # 本地高质量降级回退
        fallback_text = f"【AI生成】关于产品方案的专业分析与营销输出（已应用{target_model}知识库）"
        return SmartAIResponse(fallback_text, {"content": fallback_text, "model": "fallback"})

    async def _generate_response(self, llm, *
                                 args, task_type: str, max_retries: int = 3) -> Dict[str, Any]:
        """通用响应生成方法，包含重试和降级机制。

        ORCH-23: 每次 LLM 调用用 asyncio.wait_for() 包装，防止单次调用无限阻塞。
        总预算 = AI_LLM_REQUEST_TIMEOUT（默认30s），单次调用超时 = AI_LLM_PER_CALL_TIMEOUT（默认15s），
        重试间隔加入 0–5s 随机抖动，避免惊群效应。
        """
        import random
        retry_delay = 5
        # ORCH-23: 单次 LLM 调用整体超时（含网络 + 推理），防止线程长时间阻塞
        call_timeout = float(getattr(settings, "AI_LLM_PER_CALL_TIMEOUT", 15.0))
        total_timeout = float(getattr(settings, "AI_LLM_REQUEST_TIMEOUT", 30.0))
        # [B03] 强制报错：无可用 LLM 时禁止静默降级
        if llm is None:
            raise RuntimeError(
                "AI服务未配置：未找到可用的 LLM 提供商。"
                "请至少配置 AI_NVIDIA_API_KEY（NIM 免费额度）或 DeepSeek / 其它 AI Key。"
                "配置后重启服务即可。"
            )

        # 检查是否使用了Mock模式
        if isinstance(llm, MockLLM):
            mvp_launch = settings.MVP_LAUNCH
            allow_mock = settings.ENVIRONMENT in (
                "development",
                "testing",
                "test",
            ) or mvp_launch
            if settings.ENVIRONMENT == "production" and not allow_mock:
                raise RuntimeError(
                    "AI服务未配置：生产环境必须使用真实的LLM提供商。"
                    "请配置 AI_NVIDIA_API_KEY 或其它 AI 提供商密钥，"
                    "或设置 MVP_LAUNCH=1。"
                )
            logger.warning("使用Mock模式返回模拟数据（非生产或 MVP_LAUNCH）")
            return self._get_mock_response(task_type, *args)

        start_time = time.time()
        for attempt in range(max_retries):
            try:
                # ORCH-23: 用 asyncio.wait_for 包装，超时会触发 CancelledError
                response = await asyncio.wait_for(
                    self._call_llm(llm, task_type, *args),
                    timeout=call_timeout,
                )
                elapsed = time.time() - start_time
                logger.info(
                    f"LLM call successful (task: {task_type}, "
                    f"attempt: {attempt + 1}/{max_retries}, "
                    f"elapsed: {elapsed:.2f}s, call_timeout: {call_timeout:.1f}s)"
                )
                return response

            except asyncio.TimeoutError:
                elapsed = time.time() - start_time
                logger.warning(
                    f"LLM call timeout (task: {task_type}, "
                    f"attempt: {attempt + 1}/{max_retries}, "
                    f"elapsed: {elapsed:.2f}s, timeout: {call_timeout:.1f}s)"
                )
                if attempt < max_retries - 1 and elapsed < total_timeout:
                    # ORCH-23: 加 0–5s 随机抖动，避免重试时大量请求同时发出
                    jitter = random.uniform(0, 5.0)
                    wait = min(retry_delay * (attempt + 1) + jitter, total_timeout - elapsed)
                    await asyncio.sleep(wait)
                    continue
                # 已耗尽重试次数或超出总预算，放弃
                logger.error(
                    f"LLM调用超时放弃（task: {task_type}, "
                    f"已用时: {elapsed:.2f}s / {total_timeout:.1f}s）"
                )
                raise RuntimeError(
                    f"AI服务调用超时: 单次调用 >{call_timeout:.0f}s，"
                    f"总预算 {total_timeout:.0f}s 已耗尽，任务 {task_type}"
                )

            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}, "
                    f"elapsed: {elapsed:.2f}s): {e}"
                )
                if attempt < max_retries - 1 and elapsed < total_timeout:
                    jitter = random.uniform(0, 5.0)
                    wait = min(retry_delay * (attempt + 1) + jitter, total_timeout - elapsed)
                    await asyncio.sleep(wait)
                    continue

                # 所有重试都失败，抛出错误
                logger.error(f"LLM调用失败，已重试{max_retries}次: {e}")
                raise RuntimeError(f"AI服务调用失败: {str(e)}")

    def _build_llm_messages(self, task_type: str, args) -> list:
        """根据任务类型与参数构造发送给 LLM 的 messages。"""
        if task_type == "optimize":
            content, optimization_type, keywords = args
            if optimization_type == "title":
                prompt = f"""优化以下内容作为Meta标题（15-30字），包含关键词：{', '.join(keywords)}
原始内容：{content[:100]}"""
            elif optimization_type == "description":
                prompt = f"""优化以下内容作为Meta描述（50-120字），包含关键词：{', '.join(keywords)}
原始内容：{content[:200]}"""
            elif optimization_type == "alt_text":
                prompt = f"""为以下图片内容生成Alt文本（5-20字），包含关键词：{', '.join(keywords)}
图片内容：{content[:50]}"""
            else:
                prompt = f"""优化以下内容，使其更符合SEO要求，包含关键词：{', '.join(keywords)}
原始内容：{content}"""
            return [
                SystemMessage(content="你是一位专业的SEO优化专家。请优化内容使其更适合搜索引擎排名。"),
                HumanMessage(content=prompt),
            ]

        elif task_type == "llms_txt":
            business_type, keywords = args
            prompt = f"""生成一个专业的llms.txt文件内容，用于AI搜索引擎优化。
业务类型：{business_type}
核心关键词：{', '.join(keywords)}

请包含：
1. 网站基本信息
2. 业务描述
3. 核心关键词
4. 技术参数规范（如密度范围、强度等级等）
5. 行业标准引用（JGJ/T 12-2019）
6. 联系方式
"""
            return [
                SystemMessage(content="你是一位专业的SEO专家和技术文档编写者。"),
                HumanMessage(content=prompt),
            ]

        elif task_type == "seo_analysis":
            url, content = args
            prompt = f"""分析以下网页的SEO健康状况：
URL: {url}
内容摘要：{content[:500]}

请从以下维度进行分析：
1. 关键词密度
2. 标题优化建议
3. Meta描述分析
4. 内容结构建议
5. 技术SEO问题
"""
            return [
                SystemMessage(content="你是一位专业的SEO分析师。请提供详细的SEO分析报告。"),
                HumanMessage(content=prompt),
            ]

        elif task_type == "code":
            prompt, language = args
            full_prompt = f"""请生成{language}代码：
{prompt}

要求：
1. 代码完整可运行
2. 包含适当注释
3. 遵循最佳实践
"""
            return [
                SystemMessage(content="你是一位专业的软件工程师。请生成高质量代码。"),
                HumanMessage(content=full_prompt),
            ]

        elif task_type == "product_gen":
            prompt, content_type, _ = args
            return [
                SystemMessage(content="你是一位专业的建材产品文案专家。请生成专业、吸引人的产品描述。"),
                HumanMessage(content=prompt),
            ]

        elif task_type == "polish":
            prompt, polish_type, _ = args
            return [
                SystemMessage(content="你是一位专业的文字编辑和内容优化专家。请根据要求润色内容。"),
                HumanMessage(content=prompt),
            ]

        elif task_type == "general":
            prompt, model, max_tokens = args
            return [
                SystemMessage(content="你是一位专业的AI助手。请根据用户需求生成合适的响应。"),
                HumanMessage(content=prompt),
            ]

        return []

    async def _call_llm(self, llm, task_type: str, *args) -> Dict[str, Any]:
        """调用LLM生成响应"""
        messages = self._build_llm_messages(task_type, args)
        response = await llm.agenerate([messages])
        result = response.generations[0][0].text
        if task_type == "optimize":
            return {
                "optimized_content": result.strip(),
                "changes": ["内容已优化"],
                "token_usage": 500,
                "cost": 0.01,
                "technical_params_preserved": True,
            }

        elif task_type == "llms_txt":
            return {
                "content": result.strip(),
                "version": "1.0.0",
                "token_usage": 1000,
                "cost": 0.02}

        elif task_type == "seo_analysis":
            return {
                "analysis": result.strip(),
                "score": 85,
                "issues": [],
                "suggestions": []}

        elif task_type == "code":
            prompt, language = args
            return {
                "code": result.strip(),
                "language": language,
                "token_usage": 800,
                "cost": 0.015}

        elif task_type == "product_gen":
            return {
                "optimized_content": result.strip(),
                "changes": ["产品描述已生成"],
                "token_usage": 800,
                "cost": 0.015,
                "technical_params_preserved": True,
            }

        elif task_type == "polish":
            return {
                "optimized_content": result.strip(),
                "changes": ["内容已润色"],
                "token_usage": 500,
                "cost": 0.01,
                "technical_params_preserved": True,
            }

        elif task_type == "general":
            prompt, model, max_tokens = args
            return {
                "content": result.strip(),
                "token_usage": max_tokens,
                "cost": 0.01,
                "model": model}

    def _get_mock_response(self, task_type: str, *args) -> Dict[str, Any]:
        """返回显式标记的 mock 响应（mode=mock，非生产终态）。"""
        payload = self._build_mock_response_body(task_type, *args)
        return stamp_mock(payload, reason="ai_engine_not_configured")

    def _parse_product_gen_params(self, prompt: str):
        """从 product_gen prompt 中解析产品参数（名称/分类/密度/强度/导热/防火）。"""
        product_name = "轻集料混凝土"
        category_name = "保温材料"
        density = 0
        strength_grade = ""
        thermal_conductivity = 0
        fire_rating = ""
        if "产品名称：" in prompt:
            start = prompt.find("产品名称：") + 5
            end = prompt.find("\n", start)
            if end > start:
                product_name = prompt[start:end].strip()
        if "产品分类：" in prompt:
            start = prompt.find("产品分类：") + 5
            end = prompt.find("\n", start)
            if end > start:
                category_name = prompt[start:end].strip()
        if "干密度：" in prompt:
            start = prompt.find("干密度：") + 4
            end = prompt.find(" ", start)
            if end > start:
                try:
                    density = float(prompt[start:end].strip())
                except (ValueError, TypeError):
                    pass
        if "强度等级：" in prompt:
            start = prompt.find("强度等级：") + 5
            end = prompt.find("\n", start)
            if end > start:
                strength_grade = prompt[start:end].strip()
        if "导热系数：" in prompt:
            start = prompt.find("导热系数：") + 5
            end = prompt.find(" ", start)
            if end > start:
                try:
                    thermal_conductivity = float(prompt[start:end].strip())
                except (ValueError, TypeError):
                    pass
        if "防火等级：" in prompt:
            start = prompt.find("防火等级：") + 5
            end = prompt.find("\n", start)
            if end > start:
                fire_rating = prompt[start:end].strip()
        return product_name, category_name, density, strength_grade, thermal_conductivity, fire_rating

    def _build_product_gen_description(
        self, product_name, category_name, density, strength_grade, thermal_conductivity, fire_rating
    ) -> Dict[str, Any]:
        """构建 product 类型 product_gen 的 mock 描述。"""
        standards = {
            "轻集料混凝土": "JGJ/T 12-2019《轻集料混凝土应用技术标准》",
            "EPS": "GB/T 10801.1-2021《绝热用模塑聚苯乙烯泡沫塑料》",
            "聚苯板": "GB/T 10801.1-2021《绝热用模塑聚苯乙烯泡沫塑料》",
            "XPS": "GB/T 10801.2-2002《绝热用挤塑聚苯乙烯泡沫塑料(XPS)》",
            "岩棉": "GB/T 11835-2016《绝热用岩棉、矿渣棉及其制品》",
            "玻璃棉": "GB/T 13350-2017《绝热用玻璃棉及其制品》",
            "聚氨酯": "GB/T 21558-2008《建筑用聚氨酯绝热制品》",
            "保温板": "GB/T 29906-2013《模塑聚苯板薄抹灰外墙外保温系统材料》",
        }
        matched_standard = "相关国家标准"
        for keyword, standard in standards.items():
            if keyword in product_name or keyword in category_name:
                matched_standard = standard
                break

        density_str = f"{density} kg/m³" if density else "800-1950 kg/m³"
        tc_str = f"{thermal_conductivity} W/m·K" if thermal_conductivity else "0.18-0.28 W/m·K"
        desc = f"""【{product_name}】

{self._brand_name(content)}专注于{category_name}领域，专业生产{product_name}系列产品，严格遵循{matched_standard}。

**核心技术参数**
- 干密度：{density_str}
- 强度等级：{strength_grade or 'B1级'}
- 导热系数：{tc_str}
- 防火等级：{fire_rating or 'B1级'}

**产品优势**
- 轻质高强：密度低强度高，减轻建筑荷载的同时保证结构安全
- 保温隔热：优异的绝热性能，有效降低建筑能耗
- 耐久可靠：良好的抗冻融循环性能，延长使用寿命
- 施工便捷：良好的工作性能，适配泵送和机械化施工

**应用场景**
适用于建筑屋面保温、楼面垫层、外墙保温系统、桥梁工程等领域。

{self._brand_name(content)}以技术创新为驱动，为客户提供高品质{product_name}整体解决方案。"""

        return {
            "optimized_content": desc,
            "changes": ["AI引擎未配置，返回模拟结果"],
            "token_usage": 0,
            "cost": 0.0,
            "technical_params_preserved": True,
        }

    def _build_product_gen_seo_title(
        self, product_name, category_name, strength_grade, fire_rating
    ) -> Dict[str, Any]:
        """构建 seo_title 类型 product_gen 的 mock 标题。"""
        en_keywords = {
            "保温材料": "insulation material",
            "轻集料混凝土": "lightweight aggregate concrete",
            "EPS聚苯板": "EPS foam board",
            "防火": "fireproof",
            "高强度": "high strength",
            "节能": "energy saving",
            "A级": "Class A",
            "B1级": "Class B1",
        }
        en_category = en_keywords.get(category_name, category_name)
        en_product = en_keywords.get(product_name, product_name)
        features = []
        if strength_grade:
            features.append(strength_grade)
        if fire_rating:
            features.append(fire_rating)

        seo_title = f"{product_name} {en_product} | {category_name} {en_category} | {', '.join(features) if features else self._brand_name(content)}"
        if len(seo_title) > 60:
            seo_title = f"{product_name} {en_product} | {category_name}"

        return {
            "optimized_content": seo_title,
            "changes": ["AI引擎未配置，返回模拟结果"],
            "token_usage": 0,
            "cost": 0.0,
            "technical_params_preserved": True,
        }

    def _build_product_gen_seo_description(
        self, product_name, category_name, fire_rating, thermal_conductivity
    ) -> Dict[str, Any]:
        """构建 seo_description 类型 product_gen 的 mock 描述。"""
        keywords = [product_name, category_name]
        if fire_rating:
            keywords.append(fire_rating)
        if thermal_conductivity:
            keywords.append("保温隔热")

        en_keywords = {
            "保温材料": "insulation material",
            "轻集料混凝土": "lightweight aggregate concrete",
            "EPS聚苯板": "EPS foam board",
            "防火": "fireproof",
            "高强度": "high strength",
            "节能": "energy saving",
        }
        en_category = en_keywords.get(category_name, "")
        features = []
        if fire_rating:
            features.append(f"防火等级达{fire_rating}")
        if thermal_conductivity:
            features.append(f"导热系数{thermal_conductivity}W/m·K")
        if strength_grade:
            features.append(f"强度等级{strength_grade}")

        seo_desc = f"{product_name} - {self._brand_name('')}专业供应{category_name}({en_category})，{', '.join(features)}。节能高效，品质可靠，符合JGJ/T 12-2019标准，欢迎建筑工程采购咨询。"
        if len(seo_desc) > 160:
            seo_desc = seo_desc[:157] + "..."

        return {
            "optimized_content": seo_desc,
            "changes": ["AI引擎未配置，返回模拟结果"],
            "token_usage": 0,
            "cost": 0.0,
            "technical_params_preserved": True,
        }

    def _build_mock_product_gen(self, prompt, content_type) -> Dict[str, Any]:
        """分发 product_gen 各 content_type 的 mock 构建逻辑。"""
        product_name, category_name, density, strength_grade, thermal_conductivity, fire_rating = self._parse_product_gen_params(prompt)
        if content_type == "product" or content_type == "product_description":
            return self._build_product_gen_description(product_name, category_name, density, strength_grade, thermal_conductivity, fire_rating)
        elif content_type == "seo_title":
            return self._build_product_gen_seo_title(product_name, category_name, strength_grade, fire_rating)
        elif content_type == "seo_description":
            return self._build_product_gen_seo_description(product_name, category_name, fire_rating, thermal_conductivity)
        return {}

    def _build_mock_polish(self, prompt, polish_type) -> Dict[str, Any]:
        """构建 polish 类型的 mock 润色结果。"""
        content_start = prompt.find("请将以下内容")
        if content_start > 0:
            content_start = prompt.find("：", content_start) + 1
            content_end = prompt.find("\n\n要求：")
            if content_end > content_start:
                original_content = prompt[content_start:content_end].strip(
                )
            else:
                original_content = prompt[content_start:].strip()
        else:
            original_content = prompt

        if polish_type == "professional" or "专业" in prompt:
            polished = f"""【专业润色版】

{original_content.replace('很好用', '性能优异').replace('质量不错', '品质稳定可靠').replace('价格实惠', '性价比突出')}

经优化，本描述已提升专业术语使用比例，增强技术参数表述的准确性，符合B2B采购决策场景的阅读习惯。"""
        elif "精简" in polish_type or "简洁" in polish_type:
            polished = f"""【精简优化版】

{original_content[:200]}...

核心要点已提炼，去除冗余表述，突出关键信息，提升信息密度。"""
        elif "seo" in polish_type.lower() or "SEO" in polish_type:
            polished = f"""【SEO优化版】

{original_content}

关键词密度已优化，核心词自然分布，语义相关性增强，提升搜索引擎友好度。"""
        else:
            polished = f"""【润色优化版】

{self._brand_name(content)}作为专业的{category_name or '保温材料'}生产企业，{original_content}。

我们始终坚持品质至上，为客户提供可靠的产品解决方案。"""

        return {
            "optimized_content": polished,
            "changes": ["AI引擎未配置，返回模拟结果"],
            "token_usage": 0,
            "cost": 0.0,
            "technical_params_preserved": True,
        }

    def _build_mock_response_body(self, task_type: str, *args) -> Dict[str, Any]:
        """构建 mock 载荷（不含 mock:true 字段）。"""
        if task_type == "optimize":
            content, optimization_type, keywords = args
            if optimization_type == "title":
                optimized = f"{keywords[0] if keywords else '轻集料混凝土'} - {self._brand_name(content)}"
            elif optimization_type == "description":
                optimized = f"{self._brand_name(content)}专业生产{keywords[0] if keywords else '轻集料混凝土'}，品质保证，欢迎咨询。"
            else:
                optimized = content

            return {
                "optimized_content": optimized,
                "changes": ["AI引擎未配置，返回模拟结果"],
                "token_usage": 0,
                "cost": 0.0,
                "technical_params_preserved": True,
            }

        elif task_type == "llms_txt":
            business_type, keywords = args
            content = f"""# llms.txt
# 网站: {self._brand_name('')}
# 业务类型: {business_type}

## 核心关键词
{chr(10).join([f"- {kw}" for kw in keywords])}

## 业务描述
{self._brand_name('')}是专业的保温材料生产企业，专注于轻集料混凝土及相关产品的研发与销售。

## 技术参数规范
- 密度范围: 800-1950 kg/m³
- 强度等级: LC5.0-LC50
- 导热系数: 0.18-0.28 W/m·K
- 执行标准: JGJ/T 12-2019

## 联系方式
- 电话: 400-888-8888
- 邮箱: contact@youding.com
- 地址: 北京市朝阳区建材产业园

## 更新时间
2024-01-01

## 版本
1.0.0
"""
            return {
                "content": content,
                "version": "1.0.0",
                "token_usage": 0,
                "cost": 0.0}

        elif task_type == "seo_analysis":
            return {
                "analysis": "SEO分析报告生成中...",
                "score": 80,
                "issues": [],
                "suggestions": [],
            }

        elif task_type == "code":
            prompt, language = args
            return {
                "code": f"// {language} code generated\n// {prompt[:50]}...",
                "language": language,
                "token_usage": 0,
                "cost": 0.0,
            }

        elif task_type == "product_gen":
            prompt, content_type, _ = args
            return self._build_mock_product_gen(prompt, content_type)

        elif task_type == "polish":
            prompt, polish_type, _ = args
            return self._build_mock_polish(prompt, polish_type)

        elif task_type == "general":
            prompt, model, max_tokens = args
            return {
                "content": "模拟响应：AI优化已完成",
                "token_usage": max_tokens,
                "cost": 0.0,
                "model": model,
            }


class MockLLM:
    """模拟LLM，用于测试和无API Key场景"""
    async def agenerate(self, messages_list):
        """模拟生成响应"""
        class Generation:
            text = "模拟响应：AI优化已完成"

        class Generations:
            def __init__(self):
                """__init__。

                参数说明：
                :param self: 参数 self
                :return: 返回处理结果。
                """
                self.generations = [[Generation()]]

        return Generations()


def get_ai_engine() -> AIEngine:
    """获取AI引擎实例（单例模式）"""
    return AIEngine()
