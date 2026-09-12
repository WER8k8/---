"""复核关卡 ReviewGate（总纲 §6.4-2）。

职责：清洗通过后的第二道关。自动复核（打分≥阈值→自动通过）+
低分/高风险→人工复核；复核三态：通过 / 驳回 / 修改重提（§6.4-2）。
打分器可插拔：S3 接线时注册 content_scorer / eeat_scorer（§6.4-2 复用），
本骨架内置长度/结构启发式打分，保证 S1 可独立验收。
高风险类别（价格承诺/法规断言/医疗）一律强制人审（§6.4 接线：视频高风险必人审；
邮件首封开发信必人审由各链路在 meta.force_human 传入）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

AUTO_PASS = "auto_pass"          # 打分达标 → 自动通过
HUMAN_REVIEW = "human_review"    # 低分或高风险 → 人工复核

DECISION_APPROVED = "approved"
DECISION_REJECTED = "rejected"
DECISION_REVISE = "revise"
VALID_DECISIONS = frozenset({DECISION_APPROVED, DECISION_REJECTED, DECISION_REVISE})

DEFAULT_THRESHOLD = 70.0  # §6.4-2：≥阈值自动过（S3 起阈值走 skills 表版本化+Canary）

# 打分器签名: (content: str, meta: dict) -> float (0-100)
Scorer = Callable[[str, Dict], float]

_scorers: Dict[str, Scorer] = {}


def register_scorer(name: str, scorer: Scorer) -> None:
    """注册外部打分器（content_scorer/eeat_scorer 等，S3 接线）。"""
    _scorers[name] = scorer


def _heuristic_score(content: str, meta: Dict) -> float:
    """内置启发式：长度充分 + 有段落结构 + 无占位（占位已在清洗关拦截）。"""
    text = (content or "").strip()
    score = 0.0
    score += min(40.0, len(text) / 8.0)            # 长度分，封顶 40（≈320 字满分）
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    score += min(30.0, len(paragraphs) * 15.0)     # 结构分，封顶 30
    if meta.get("has_cta") or "联系" in text or "contact" in text.lower():
        score += 15.0                              # 转化引导分
    if len(text) > 100:
        score += 15.0                              # 信息量分
    return min(100.0, score)


@dataclass
class ReviewVerdict:
    route: str                 # auto_pass | human_review
    score: float
    threshold: float
    reasons: List[str] = field(default_factory=list)
    scorer_versions: Dict[str, str] = field(default_factory=dict)


class ReviewGate:
    """复核关：路由决策（自动过/转人审）+ 人工三态判定校验。"""
    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param threshold: 参数 threshold
        :return: 返回处理结果。
        """
        self.threshold = threshold

    def decide(self, content: str, meta: Optional[Dict] = None) -> ReviewVerdict:
        """decide。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        meta = meta or {}
        reasons: List[str] = []
        versions: Dict[str, str] = {}
        # 强制人审通道（链路级红线：首封开发信/高风险视频等）
        if meta.get("force_human"):
            return ReviewVerdict(
                route=HUMAN_REVIEW, score=0.0, threshold=self.threshold,
                reasons=["force_human: 链路规则要求必人审"],
            )
        if meta.get("high_risk"):
            reasons.append("high_risk: 高风险类别强制人审")

        # 打分：外部打分器均值优先，无则内置启发式
        scores: List[float] = []
        for name, scorer in _scorers.items():
            try:
                scores.append(float(scorer(content, meta)))
                versions[name] = "ok"
            except Exception:
                versions[name] = "fault"
                reasons.append(f"scorer_fault:{name}（故障期间不放行自动过）")
        if scores:
            score = sum(scores) / len(scores)
        else:
            score = _heuristic_score(content, meta)
            versions["heuristic"] = "builtin-1.0"

        if meta.get("high_risk") or reasons:
            return ReviewVerdict(
                route=HUMAN_REVIEW, score=score, threshold=self.threshold,
                reasons=reasons or ["high_risk"], scorer_versions=versions,
            )
        if score >= self.threshold:
            return ReviewVerdict(
                route=AUTO_PASS, score=score, threshold=self.threshold,
                reasons=[f"score {score:.1f} >= threshold {self.threshold}"],
                scorer_versions=versions,
            )
        return ReviewVerdict(
            route=HUMAN_REVIEW, score=score, threshold=self.threshold,
            reasons=[f"score {score:.1f} < threshold {self.threshold}"],
            scorer_versions=versions,
        )

    @staticmethod
    def validate_decision(decision: str) -> str:
        """人工复核三态校验（§6.4-2：通过/驳回/修改重提）。"""
        if decision not in VALID_DECISIONS:
            raise ValueError(
                f"非法复核决定 {decision!r}，必须为 {sorted(VALID_DECISIONS)}"
            )
        return decision
