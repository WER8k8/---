# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""公开技术资料引用 — 国标/专利摘要等脱敏改写，供 GEO 内容注入可验证参数。

仅处理用户粘贴或已授权的公开文本；去掉申请人、完整专利号、联系方式，保留技术事实。
"""

from __future__ import annotations

import re
from typing import Any

# 需脱敏的模式
_APPLICANT_PATTERNS = (
    r"(?:申请人|专利权人|发明人)[:：]\s*[^\n；;。]{2,40}",
    r"(?:Applicant|Inventor)[:：]\s*[^\n;.]{2,60}",
)
_PATENT_NO_PATTERNS = (
    r"CN\d{9,12}[.\.]?\d?",
    r"ZL\s*\d{4}\s*\d{7,10}[.\.]?\d?",
    r"专利号[:：]\s*[A-Z0-9.\-]{8,24}",
)
_CONTACT_PATTERNS = (
    r"1[3-9]\d{9}",
    r"[\w.-]+@[\w.-]+\.\w+",
    r"(?:地址|Address)[:：][^\n]{6,80}",
)
_COMPANY_SUFFIX = re.compile(
    r"(?:有限公司|股份有限公司|集团|科技|建材|材料)(?:的)?(?:一种|用于)?"
)


def desensitize_public_technical_text(raw: str) -> dict[str, Any]:
    """脱敏公开技术文本，返回清洗正文 + 移除项统计。"""
    text = (raw or "").strip()
    if not text:
        return {"text": "", "removed": {}, "facts": []}

    removed: dict[str, int] = {"applicant": 0, "patent_no": 0, "contact": 0, "company": 0}
    for pat in _APPLICANT_PATTERNS:
        text, n = re.subn(pat, "【技术方案参考】", text, flags=re.I)
        removed["applicant"] += n

    for pat in _PATENT_NO_PATTERNS:
        text, n = re.subn(pat, "【公开文献编号已隐】", text, flags=re.I)
        removed["patent_no"] += n

    for pat in _CONTACT_PATTERNS:
        text, n = re.subn(pat, "", text)
        removed["contact"] += n

    text, n = _COMPANY_SUFFIX.subn("某型", text)
    removed["company"] += n
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    facts = extract_geo_technical_facts(text)
    return {
        "text": text,
        "removed": removed,
        "facts": facts,
        "desensitized": True,
    }


def extract_geo_technical_facts(text: str) -> list[str]:
    """从脱敏文本提取可写入 GEO 的可验证技术点（参数、标准、性能）。"""
    facts: list[str] = []
    patterns = [
        (r"(?:密度|导热系数|抗压强度|吸水率|防火等级)[:：]?\s*[^\n；;。]{4,60}", "param"),
        (r"(?:GB/T|JGJ|JC|ASTM|EN)\s*[-\d./]+[^\n；;。]{0,40}", "standard"),
        (r"\d+\.?\d*\s*(?:W/(?:m·K|m\^2·K)|kg/m³|MPa|mm|℃|%|kPa)", "numeric"),
        (r"(?:A1|A2|B1|B2)(?:级)?(?:\s*[^\n；;。]{0,20})?", "fire"),
    ]
    seen: set[str] = set()
    for pat, _kind in patterns:
        for m in re.finditer(pat, text, re.I):
            snippet = m.group(0).strip(" ，,;；")
            if len(snippet) >= 4 and snippet not in seen:
                seen.add(snippet)
                facts.append(snippet)
    return facts[:12]


def build_technical_reference_block(
    references: list[str] | None = None,
    *,
    category: str = "建材",
    max_facts: int = 6,
) -> str:
    """合并多段公开资料 → GEO Prompt 用技术事实块（已脱敏，不含权利要求原文照搬）。"""
    if not references:
        return ""

    all_facts: list[str] = []
    for ref in references:
        if not (ref or "").strip():
            continue
        pack = desensitize_public_technical_text(ref)
        all_facts.extend(pack.get("facts") or [])

    if not all_facts:
        return ""

    unique: list[str] = []
    seen: set[str] = set()
    for f in all_facts:
        key = f[:40]
        if key not in seen:
            seen.add(key)
            unique.append(f)
        if len(unique) >= max_facts:
            break

    lines = [
        f"【{category}公开技术事实 — 已脱敏，写作时改写表述，勿逐字复制专利权利要求】",
        *[f"- {fact}" for fact in unique],
        "写作要求：用项目口语改写以上参数；可写「参照公开行业文献」而不列具体专利号与公司名。",
    ]
    return "\n".join(lines)


def public_reference_prompt_suffix(reference_block: str) -> str:
    """实现 publicreferencepromptsuffix 的功能。
    
    :param reference_block: 参数 reference_block（类型: str）
    :return: 返回 str 结果
    """
    if not reference_block.strip():
        return ""
    return (
        "\n\n【技术事实素材（脱敏）】\n"
        f"{reference_block}\n"
        "将以上参数自然融入正文与 FAQ，增加 Princeton GEO 统计引用密度；禁止恢复申请人/专利号。"
    )
