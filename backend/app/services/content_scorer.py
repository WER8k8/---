"""内容质量评分引擎 — 多维规则打分"""

import re
from typing import Dict, List, Tuple


def _score_word_count(word_count: int, details: list) -> int:
    """字数维度评分 (0-25)。"""
    if word_count < 300:
        details.append("内容过短，建议 ≥800 字")
        return 5
    elif word_count < 800:
        details.append("内容偏短，建议扩充至 800 字以上")
        return 15
    elif word_count <= 2000:
        details.append("字数适中")
        return 25
    elif word_count <= 4000:
        details.append("内容充实")
        return 20
    else:
        details.append("内容较长，可考虑拆分")
        return 15


def _score_keywords(body: str, keywords: List[str], word_count: int, details: list) -> int:
    """关键词维度评分 (0-25)：覆盖率 + 密度。"""
    kw_score = 0
    if keywords:
        body_lower = body.lower()
        matched = [kw for kw in keywords if kw.lower() in body_lower]
        kw_coverage = len(matched) / len(keywords) * 100 if keywords else 0
        if kw_coverage >= 80:
            kw_score += 15
        elif kw_coverage >= 50:
            kw_score += 10
        else:
            kw_score += 5

        # 关键词密度
        total_kw_count = sum(body_lower.count(kw.lower()) for kw in keywords)
        density = total_kw_count / max(word_count, 1) * 100
        if 1 <= density <= 3:
            kw_score += 10
            details.append(f"关键词密度 {density:.1f}%，良好")
        elif density < 1:
            kw_score += 5
            details.append(f"关键词密度偏低 ({density:.1f}%)")
        else:
            kw_score += 3
            details.append(f"关键词密度偏高 ({density:.1f}%)，可能被判定为堆砌")
    else:
        kw_score = 10  # 无关键词时给基础分
        details.append("未提供目标关键词")
    return kw_score


def _score_structure(title: str, body: str, details: list) -> Tuple[int, int]:
    """结构维度评分 (0-20)，返回 (分数, 段落数)。"""
    struct_score = 0
    has_h1 = bool(re.search(r'# |<h1', body))
    has_h2 = bool(re.search(r'## |<h2', body))
    has_h3 = bool(re.search(r'### |<h3', body))
    paragraphs = [p for p in body.split('\n\n') if len(p.strip()) > 30]
    para_count = len(paragraphs)
    if has_h1:
        struct_score += 3
    if has_h2:
        struct_score += 5
    if has_h3:
        struct_score += 2

    if para_count >= 5:
        struct_score += 8
    elif para_count >= 3:
        struct_score += 5
    else:
        struct_score += 2

    if title and len(title) >= 5 and len(title) <= 60:
        struct_score += 2
        details.append("标题长度合适")
    else:
        details.append("标题需优化（5-60 字为佳）")

    return struct_score, para_count


def _score_readability(body: str, details: list) -> int:
    """可读性维度评分 (0-20)。"""
    readability = 10
    sentences = re.split(r'[。！？.!?\n]', body)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if sentences:
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        if 20 <= avg_len <= 40:
            readability += 8
            details.append("句子长度适中，可读性好")
        elif avg_len < 20:
            readability += 5
            details.append("句子偏短")
        else:
            readability += 3
            details.append("句子偏长，建议拆分")

    has_bullet = bool(re.search(r'[-*•]\s|<li>|<ul>|<ol>', body))
    has_bold = bool(re.search(r'\*\*.*?\*\*|<strong>|<b>', body))
    if has_bullet:
        readability += 1
    if has_bold:
        readability += 1
    return min(readability, 20)


def _score_media(body: str) -> int:
    """多媒体维度评分 (0-10)。"""
    media_score = 0
    has_image = bool(re.search(r'!\[|<img', body))
    has_list = bool(re.search(r'[-*•]\s|<li>', body))
    has_table = bool(re.search(r'\|.*\|.*\|', body))
    if has_image:
        media_score += 5
    if has_list:
        media_score += 3
    if has_table:
        media_score += 2
    return media_score


def score_content(title: str, body: str, keywords: List[str] = None) -> Dict:
    """
    评分维度（满分 100）：
    - 字数分 (0-25): 800-2000 字为佳
    - 关键词分 (0-25): 关键词覆盖率和密度
    - 结构分 (0-20): 标题层级、段落分布
    - 可读性分 (0-20): 句子长度、标点使用
    - 多媒体分 (0-10): 图片、列表、表格
    """
    scores = {}
    details = []
    word_count = len(body)
    scores["word"] = _score_word_count(word_count, details)
    scores["keyword"] = _score_keywords(body, keywords, word_count, details)
    struct_score, para_count = _score_structure(title, body, details)
    scores["structure"] = struct_score
    scores["readability"] = _score_readability(body, details)
    scores["media"] = _score_media(body)
    total = sum(scores.values())
    grade = _grade(total)
    return {
        "total_score": total,
        "grade": grade["letter"],
        "grade_label": grade["label"],
        "dimensions": scores,
        "details": details,
        "word_count": word_count,
        "paragraph_count": para_count,
    }


def _grade(score: int) -> dict:
    """_grade。

    参数说明：
    :param score: 参数 score
    :return: 返回处理结果。
    """
    if score >= 85:
        return {"letter": "A", "label": "优秀"}
    elif score >= 70:
        return {"letter": "B", "label": "良好"}
    elif score >= 50:
        return {"letter": "C", "label": "一般"}
    else:
        return {"letter": "D", "label": "需优化"}


def batch_score(articles: List[dict]) -> List[dict]:
    """批量评分"""
    results = []
    for art in articles:
        r = score_content(
            art.get("title", ""),
            art.get("body", art.get("content", "")),
            art.get("keywords", []),
        )
        r["article_id"] = art.get("id")
        r["article_title"] = art.get("title")
        results.append(r)
    return results
