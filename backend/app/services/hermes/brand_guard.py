"""对外文案脱敏：禁止第三方 Agent 产品商标进入用户可见字段。"""

from __future__ import annotations

import re
from typing import Any

# 用户可见 API / 副驾回复中替换（大小写不敏感）
_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"DeerFlow\s*2\.0?", re.I), "市场研究"),
    (re.compile(r"DeerFlow", re.I), "市场研究"),
    (re.compile(r"AccioWork", re.I), "获客执行"),
    (re.compile(r"Accio\s*Work", re.I), "获客执行"),
    (re.compile(r"\bAccio\b"), "获客助手"),
    (re.compile(r"\bUBrain\b", re.I), "卖货副驾"),
    (re.compile(r"\bUBrain-X\b", re.I), "卖货副驾"),
    (re.compile(r"LangGraph", re.I), "任务编排"),
    (re.compile(r"LangChain", re.I), "智能引擎"),
    (re.compile(r"字节跳动|字节系", re.I), ""),
    (re.compile(r"阿里巴巴|阿里国际站|阿里系", re.I), "B2B平台"),
    (re.compile(r"\bHermes\b", re.I), "智能建站"),
    (re.compile(r"\bECC\b"), "设计专家"),
    (re.compile(r"deerflow_[a-z_]+", re.I), "research_task"),
    (re.compile(r"accio_[a-z_]+", re.I), "sales_task"),
)

# 内部日志/DB 字段名可保留；仅 sanitize 字符串值
_SKIP_KEYS = frozenset(
    {
        "framework",
        "mode",
        "source",
        "north_star",
        "catalog_version",
        "intent",
        "skill_id",
        "api",
        "id",
        "job_id",
        "pipeline_run_id",
        "ticket_id",
    }
)


def sanitize_public_copy(text: str) -> str:
    """sanitize_public_copy。

    参数说明：
    :param text: 参数 text
    :return: 返回处理结果。
    """
    if not text:
        return text
    out = text
    for pattern, repl in _REPLACEMENTS:
        out = pattern.sub(repl, out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def sanitize_public_data(data: Any, *, depth: int = 0) -> Any:
    """递归脱敏 dict/list/str（跳过已知内部键名的键）。"""
    if depth > 12:
        return data
    if isinstance(data, str):
        return sanitize_public_copy(data)
    if isinstance(data, list):
        return [sanitize_public_data(x, depth=depth + 1) for x in data]
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            key = str(k)
            if key in ("accio_actions",):
                cleaned["next_actions"] = sanitize_public_data(v, depth=depth + 1)
                continue
            if key in ("accio_core",):
                cleaned["execution_skills"] = sanitize_public_data(v, depth=depth + 1)
                continue
            if key in ("accio_analog",):
                cleaned["capability_label"] = sanitize_public_data(v, depth=depth + 1)
                continue
            if key == "version" and isinstance(v, str):
                cleaned[key] = sanitize_public_copy(v.replace("-accio", "").replace("accio", "")) or "v1"
                continue
            if key in ("deerflow_next_prompt",):
                cleaned["assistant_prompt"] = sanitize_public_data(v, depth=depth + 1)
                continue
            if key in _SKIP_KEYS and isinstance(v, str):
                cleaned[key] = v
                continue
            cleaned[key] = sanitize_public_data(v, depth=depth + 1)
        return cleaned
    return data
