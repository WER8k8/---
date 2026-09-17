# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GEO 引擎 — 多模型收录与「推荐位」探测。

probe_mode:
  - brand: 是否了解品牌（兼容旧接口）
  - recommend: 模拟采购问法，检测是否进入 AI 推荐前三（对齐真实 GEO 意图）
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.cache import get_cache, redis_client, set_cache
from app.services.geo.geo_writing_policy import TACTICS_VERSION


class GEOEngine:
    """GEO 引擎 — 多模型关键词收录查询"""
    # 支持的大模型列表
    MODELS = [
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "icon": "🔍",
            "api_base": "https://api.deepseek.com/v1",
            "env_key": "AI_DEEPSEEK_API_KEY",
            "model": "deepseek-chat",
            "color": "#3b82f6",
        },
        {
            "id": "openai",
            "name": "ChatGPT (OpenAI)",
            "icon": "🧠",
            "api_base": "https://api.openai.com/v1",
            "env_key": "AI_OPENAI_API_KEY",
            "model": "gpt-4o-mini",
            "color": "#10a37f",
        },
        {
            "id": "nvidia",
            "name": "NVIDIA NIM",
            "icon": "🖥️",
            "api_base": "https://integrate.api.nvidia.com/v1",
            "env_key": "AI_NVIDIA_API_KEY",
            "model": "meta/llama-3.1-70b-instruct",
            "color": "#76b900",
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "icon": "🌐",
            "api_base": "https://generativelanguage.googleapis.com/v1beta",
            "env_key": "AI_GEMINI_API_KEY",
            "model": "gemini-2.0-flash",
            "color": "#4285f4",
        },
        {
            "id": "anthropic",
            "name": "Claude (Anthropic)",
            "icon": "🧩",
            "api_base": "https://api.anthropic.com/v1",
            "env_key": "AI_ANTHROPIC_API_KEY",
            "model": "claude-3-haiku-20240307",
            "color": "#d97706",
        },
        {
            "id": "qwen",
            "name": "通义千问",
            "icon": "🌟",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "env_key": "AI_DASHSCOPE_API_KEY",
            "model": os.getenv("AI_DASHSCOPE_MODEL", "qwen-plus"),
            "color": "#6366f1",
        },
        {
            "id": "doubao",
            "name": "豆包",
            "icon": "🫘",
            "api_base": "https://ark.cn-beijing.volces.com/api/v3",
            "env_key": "AI_ARK_API_KEY",
            "model": os.getenv("AI_ARK_MODEL", "doubao-pro-32k"),
            "color": "#0ea5e9",
        },
    ]
    PROBE_MODES = ("brand", "recommend")
    # geo model id → ai_config.provider_type（DB 里填 Key 时匹配）
    _PROVIDER_TYPES: Dict[str, tuple[str, ...]] = {
        "deepseek": ("deepseek",),
        "openai": ("openai",),
        "nvidia": ("nvidia",),
        "gemini": ("gemini", "google"),
        "anthropic": ("anthropic",),
        "qwen": ("aliyun", "qwen", "dashscope"),
        "doubao": ("byte", "doubao", "ark"),
    }
    @classmethod
    def _resolve_api_key(cls, model_info: Dict, db: Session | None = None) -> str:
        """环境变量优先，其次 AI 配置页（DB）。"""
        from app.core.config import settings
        env_name = model_info.get("env_key", "")
        val = (os.getenv(env_name, "") or getattr(settings, env_name, None) or "").strip()
        if len(val) >= 8:
            return val
        if db is None:
            return ""
        try:
            from app.models.ai_config import AIModelProvider
            types = cls._PROVIDER_TYPES.get(model_info.get("id", ""), ())
            for pt in types:
                row = (
                    db.query(AIModelProvider)
                    .filter(
                        AIModelProvider.provider_type == pt,
                        AIModelProvider.is_active.is_(True),
                    )
                    .first()
                )
                if row and (row.api_key or "").strip():
                    return row.api_key.strip()
        except Exception:
            pass
        return ""

    @classmethod
    def model_key_configured(cls, model_info: Dict, db: Session | None = None) -> bool:
        """model_key_configured。

        参数说明：
        :param cls: 参数 cls
        :param model_info: 参数 model_info
        :param db: 参数 db
        :return: 返回处理结果。
        """
        return bool(cls._resolve_api_key(model_info, db))

    @classmethod
    async def check_keyword(
        cls,
        keyword: str,
        models: Optional[List[str]] = None,
        context: str = "",
        *,
        probe_mode: str = "brand",
        brand_name: str = "",
        product_category: str = "",
        region: str = "",
        db: Session | None = None,
    ) -> Dict:
        """检查关键词在各模型中的收录状态

        Args:
            keyword: 要查询的关键词（如 "优丁建材 轻集料混凝土"）
            models: 指定模型列表，默认全部
            context: 额外上下文（如 "请确认是否了解该品牌"）

        Returns:
            {
                "keyword": "优丁建材 轻集料混凝土",
                "checked_at": "2026-05-20T15:00:00Z",
                "models": [
                    {
                        "id": "deepseek", "name": "DeepSeek",
                        "status": "indexed",  # indexed | partial | not_indexed | error
                        "confidence": 0.92,
                        "response": "DeepSeek 确认知道优丁建材...",
                        "latency_ms": 450,
                    },
                    ...
                ]
            }
        """
        mode = probe_mode if probe_mode in cls.PROBE_MODES else "brand"
        cache_key = (
            f"geo_engine:{mode}:{keyword}:{':'.join(models or [])}:"
            f"{context[:50]}:{brand_name[:30]}:{product_category[:30]}"
        )
        cached = get_cache(cache_key)
        if cached and isinstance(cached, str):
            try:
                return json.loads(cached)
            except Exception:
                pass
        elif cached and isinstance(cached, dict):
            return cached

        target_models = [m for m in cls.MODELS if not models or m["id"] in models]
        results = []
        probe_ctx = {
            "probe_mode": mode,
            "brand_name": brand_name or keyword,
            "product_category": product_category or keyword,
            "region": region,
            "context": context,
            "db": db,
        }
        for model_info in target_models:
            result = await cls._query_model(keyword, model_info, probe_ctx)
            results.append(result)

        data = {
            "keyword": keyword,
            "probe_mode": mode,
            "brand_name": brand_name or keyword,
            "product_category": product_category or keyword,
            "region": region,
            "tactics_version": TACTICS_VERSION,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "models": results,
            "summary": cls._summarize(results, probe_mode=mode),
        }
        # 缓存 1 小时
        set_cache(cache_key, json.dumps(data, ensure_ascii=False, default=str))
        return data

    @classmethod
    def _build_probe_prompt(cls, keyword: str, probe_ctx: Dict[str, Any]) -> str:
        """_build_probe_prompt。

        参数说明：
        :param cls: 参数 cls
        :param keyword: 参数 keyword
        :param probe_ctx: 参数 probe_ctx
        :return: 返回处理结果。
        """
        mode = probe_ctx.get("probe_mode", "brand")
        extra = probe_ctx.get("context") or ""
        brand = probe_ctx.get("brand_name") or keyword
        category = probe_ctx.get("product_category") or keyword
        region = probe_ctx.get("region") or "国内工地/工程项目"
        if mode == "recommend":
            return f"""你是一名建材 B2B 采购顾问。用户正在寻找可靠供应商。

采购品类：{category}
项目/地区：{region}
目标品牌（检测是否被推荐）：{brand}
{extra}

请模拟真实回答：列出你会推荐的 3 家厂家/品牌及理由（参数、供货、资质等）。
然后判断目标品牌「{brand}」是否出现在推荐中，以及大致名次（1-3 或未进前三）。

仅输出 JSON：
{{
  "recommended": true/false,
  "rank_position": 1|2|3|null,
  "mentions_brand": true/false,
  "confidence": 0-1,
  "summary": "50字内结论"
}}"""

        return f"""你是一个品牌知识检查助手。请确认你是否了解以下品牌/关键词，并简要说明。

品牌/关键词：{keyword}
{extra}

请按以下 JSON 格式回答：
{{
  "knows": true/false,
  "confidence": 0-1之间的数字,
  "summary": "一句话描述你对该品牌/关键词的了解（中文，50字以内）"
}}"""

    @classmethod
    async def _query_model(cls, keyword: str, model_info: Dict, probe_ctx: Dict[str, Any]) -> Dict:
        """查询单个模型。"""
        api_key = cls._resolve_api_key(model_info, probe_ctx.get("db"))
        start_time = time.time()
        mode = probe_ctx.get("probe_mode", "brand")
        if not api_key:
            latency_ms = int((time.time() - start_time) * 1000)
            return cls._build_not_configured_row(model_info, latency_ms, mode)

        prompt = cls._build_probe_prompt(keyword, probe_ctx)
        try:
            content = await cls._query_model_content(model_info, api_key, prompt)
            parsed = cls._parse_content(content, mode, probe_ctx, keyword)
            latency_ms = int((time.time() - start_time) * 1000)
            return cls._build_success_row(model_info, parsed, latency_ms, mode)
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return cls._build_error_row(model_info, e, latency_ms)

    @classmethod
    def _build_not_configured_row(cls, model_info: Dict, latency_ms: int, mode: str) -> Dict:
        """构建 API Key 未配置的返回行。"""
        return {
            "id": model_info["id"],
            "name": model_info["name"],
            "icon": model_info["icon"],
            "color": model_info["color"],
            "status": "not_configured",
            "confidence": 0,
            "response": (
                f"{model_info['name']} 监测通道未接通（缺 API Key）。"
                "仅影响能否自动探测，与 GEO 内容优化无关；可在 AI配置 填写 Key。"
            ),
            "latency_ms": latency_ms,
            "error": "API Key 未配置",
            "configure_path": "/ai-config",
            "env_key": model_info.get("env_key"),
            "probe_mode": mode,
        }

    @classmethod
    def _build_error_row(cls, model_info: Dict, exc: Exception, latency_ms: int) -> Dict:
        """构建查询失败的返回行。"""
        return {
            "id": model_info["id"],
            "name": model_info["name"],
            "icon": model_info["icon"],
            "color": model_info["color"],
            "status": "error",
            "confidence": 0,
            "response": f"查询失败: {str(exc)[:100]}",
            "latency_ms": latency_ms,
            "error": str(exc)[:200],
            "probe_mode": "brand",
        }

    @classmethod
    async def _query_model_content(cls, model_info: Dict, api_key: str, prompt: str) -> str:
        """按模型类型发起 API 请求并提取文本内容。"""
        async with httpx.AsyncClient(timeout=15) as client:
            if model_info["id"] == "anthropic":
                resp = await client.post(
                    f"{model_info['api_base']}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_info["model"],
                        "max_tokens": 200,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                body = resp.json()
                return body.get("content", [{}])[0].get("text", "")
            elif model_info["id"] == "gemini":
                resp = await client.post(
                    f"{model_info['api_base']}/models/{model_info['model']}:generateContent",
                    params={"key": api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                body = resp.json()
                return (
                    body.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
            else:
                # OpenAI 兼容格式 (DeepSeek, NVIDIA, OpenAI)
                resp = await client.post(
                    f"{model_info['api_base']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_info["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.1,
                    },
                )
                body = resp.json()
                return body["choices"][0]["message"]["content"]

    @classmethod
    def _parse_content(cls, content: str, mode: str, probe_ctx: Dict, keyword: str) -> Dict:
        """解析 API 响应内容。"""
        return (
            cls._parse_recommend_response(content, probe_ctx.get("brand_name") or keyword)
            if mode == "recommend"
            else cls._parse_response(content)
        )

    @classmethod
    def _build_success_row(cls, model_info: Dict, parsed: Dict, latency_ms: int, mode: str) -> Dict:
        """构建查询成功的返回行。"""
        status = parsed.get("status") or ("indexed" if parsed.get("knows") else "not_indexed")
        row: Dict[str, Any] = {
            "id": model_info["id"],
            "name": model_info["name"],
            "icon": model_info["icon"],
            "color": model_info["color"],
            "status": status,
            "confidence": parsed.get("confidence", 0),
            "response": parsed.get("summary", content[:120]),
            "latency_ms": latency_ms,
            "probe_mode": mode,
        }
        if mode == "recommend":
            row["rank_position"] = parsed.get("rank_position")
            row["mentions_brand"] = parsed.get("mentions_brand", False)
        return row

    @classmethod
    def _parse_response(cls, text: str) -> Dict:
        """解析 brand 模式 JSON"""
        try:
            match = re.search(r'\{[^{}]*"knows"[^{}]*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "knows": data.get("knows", False),
                    "confidence": float(data.get("confidence", 0)),
                    "summary": str(data.get("summary", text[:100])),
                }
        except Exception:
            pass

        knows = any(w in text.lower() for w in ["优丁", "youding", "轻集料", "建材"])
        return {"knows": knows, "confidence": 0.5 if knows else 0.1, "summary": text[:100]}

    @classmethod
    def _parse_recommend_response(cls, text: str, brand_name: str) -> Dict:
        """解析 recommend 模式 JSON"""
        try:
            match = re.search(
                r'\{[^{}]*"(?:recommended|rank_position|mentions_brand)"[^{}]*\}',
                text,
                re.DOTALL,
            )
            if match:
                data = json.loads(match.group(0))
                rank = data.get("rank_position")
                if rank is not None:
                    try:
                        rank = int(rank)
                    except (TypeError, ValueError):
                        rank = None
                mentions = bool(data.get("mentions_brand", False))
                recommended = bool(data.get("recommended", False))
                if not mentions and brand_name:
                    mentions = brand_name in text
                if rank is None and mentions:
                    for i, token in enumerate(re.split(r"[\d\.、\)\]]+", text)):
                        if brand_name in token:
                            rank = min(i + 1, 3)
                            break
                status = "indexed"
                if not mentions:
                    status = "not_indexed"
                elif rank is None or rank > 3:
                    status = "partial"
                elif not recommended and rank and rank <= 3:
                    status = "indexed"
                return {
                    "status": status,
                    "rank_position": rank,
                    "mentions_brand": mentions,
                    "confidence": float(data.get("confidence", 0.7 if status == "indexed" else 0.3)),
                    "summary": str(data.get("summary", text[:100])),
                }
        except Exception:
            pass

        mentions = brand_name in text if brand_name else False
        return {
            "status": "partial" if mentions else "not_indexed",
            "rank_position": None,
            "mentions_brand": mentions,
            "confidence": 0.4 if mentions else 0.1,
            "summary": text[:100],
        }

    @classmethod
    def _summarize(cls, results: List[Dict], *, probe_mode: str = "brand") -> Dict:
        """汇总统计"""
        indexed = sum(1 for r in results if r["status"] == "indexed")
        partial = sum(1 for r in results if r["status"] == "partial")
        not_indexed = sum(1 for r in results if r["status"] == "not_indexed")
        errors = sum(1 for r in results if r["status"] in ("error", "not_configured"))
        total = len(results)
        indexed_rate = round(indexed / total * 100, 1) if total > 0 else 0
        hit_models = [r for r in results if r["status"] in ("indexed", "partial")]
        avg_confidence = (
            round(sum(r["confidence"] for r in hit_models) / len(hit_models) * 100, 1)
            if hit_models
            else 0
        )
        ranks = [r["rank_position"] for r in results if r.get("rank_position") in (1, 2, 3)]
        avg_rank = round(sum(ranks) / len(ranks), 2) if ranks else None
        summary: Dict[str, Any] = {
            "total_models": total,
            "indexed": indexed,
            "partial": partial,
            "not_indexed": not_indexed,
            "errors": errors,
            "indexed_rate": indexed_rate,
            "recommend_top3_rate": indexed_rate if probe_mode == "recommend" else None,
            "avg_confidence": avg_confidence,
            "avg_rank_position": avg_rank,
            "best_model": max(results, key=lambda r: r["confidence"])["name"] if hit_models else "无",
            "probe_mode": probe_mode,
        }
        return summary

    @classmethod
    async def batch_check(cls, keywords: List[str]) -> Dict:
        """批量检查多个关键词"""
        all_results = []
        for kw in keywords:
            result = await cls.check_keyword(kw)
            all_results.append(result)
            await cls._sleep(0.5)  # 避免 API 限流

        return {
            "keywords": keywords,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "results": all_results,
        }

    @classmethod
    def get_history(cls, keyword: str, days: int = 7) -> List[Dict]:
        """获取历史查询记录"""
        if not redis_client:
            return []
        pattern = f"geo_engine:{keyword}:*"
        keys = list(redis_client.scan_iter(match=pattern, count=100))
        history = []
        for k in keys[:days * 5]:  # 每天最多5次
            try:
                data = get_cache(k)
                if data:
                    d = json.loads(data) if isinstance(data, str) else data
                    history.append({
                        "checked_at": d.get("checked_at", ""),
                        "indexed_rate": d.get("summary", {}).get("indexed_rate", 0),
                    })
            except Exception:
                pass
        return sorted(history, key=lambda x: x["checked_at"])

    @staticmethod
    async def _sleep(seconds: float):
        """_sleep。

        参数说明：
        :param seconds: 参数 seconds
        :return: 返回处理结果。
        """
        import asyncio
        await asyncio.sleep(seconds)
