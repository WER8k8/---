"""清洗关卡 CleanseGate（总纲 §6.4-1）。

职责：发布物进入复核前的强制清洗检查；**未过不得进复核**（红线）。
聚合策略（§6.4-1）：结构化问题清单（code/severity/message），
严重级 error 存在 → 不通过；仅 warning → 通过但留痕。

内置基础检查（不依赖外部服务，S1 可独立验收）：
- non_empty：内容非空
- no_placeholder：占位符检测（{{...}} / [TODO] / 占位 / lorem ipsum）
- min_length：最小长度阈值

S3 接线项（§6.4-1 聚合）：把 `hermes/brand_guard.sanitize_public_copy`、
`compliance_scanner`、敏感词/事实断言/查重 注册为附加 checker
（register_checker），接线前本骨架已可拦截结构性问题。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

_PLACEHOLDER_RE = re.compile(
    r"\{\{[^}]*\}\}|\[TODO\]|\bTODO\b|占位|lorem\s+ipsum", re.IGNORECASE
)


@dataclass
class CleanseIssue:
    code: str
    severity: str  # error | warning
    message: str


@dataclass
class CleanseReport:
    passed: bool
    issues: List[CleanseIssue] = field(default_factory=list)
    checker_versions: Dict[str, str] = field(default_factory=dict)
    @property
    def errors(self) -> List[CleanseIssue]:
        """errors。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return [i for i in self.issues if i.severity == SEVERITY_ERROR]


# checker 签名: (content: str, meta: dict) -> List[CleanseIssue]
Checker = Callable[[str, Dict], List[CleanseIssue]]

_registry: Dict[str, Checker] = {}


def register_checker(name: str, checker: Checker, *, version: str = "1.0") -> None:
    """注册附加检查器（brand_guard / compliance_scanner 等，S3 接线用）。"""
    _registry[name] = checker


def _check_non_empty(content: str, meta: Dict) -> List[CleanseIssue]:
    """_check_non_empty。

    参数说明：
    :param content: 参数 content
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    if not content or not content.strip():
        return [CleanseIssue("non_empty", SEVERITY_ERROR, "内容为空")]
    return []


def _check_no_placeholder(content: str, meta: Dict) -> List[CleanseIssue]:
    """_check_no_placeholder。

    参数说明：
    :param content: 参数 content
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    hits = _PLACEHOLDER_RE.findall(content or "")
    if hits:
        return [
            CleanseIssue(
                "no_placeholder", SEVERITY_ERROR,
                f"检测到占位符 {len(hits)} 处：{', '.join(hits[:3])}",
            )
        ]
    return []


def _check_min_length(content: str, meta: Dict) -> List[CleanseIssue]:
    """_check_min_length。

    参数说明：
    :param content: 参数 content
    :param meta: 参数 meta
    :return: 返回处理结果。
    """
    min_len = int(meta.get("min_length", 50))
    if len((content or "").strip()) < min_len:
        return [
            CleanseIssue(
                "min_length", SEVERITY_WARNING,
                f"内容长度不足 {min_len} 字符，可能信息量不足",
            )
        ]
    return []


_BUILTIN: Dict[str, Checker] = {
    "non_empty": _check_non_empty,
    "no_placeholder": _check_no_placeholder,
    "min_length": _check_min_length,
}


class CleanseGate:
    """清洗关：内置检查 + 已注册的附加检查，全部执行后出结构化报告。"""
    def __init__(self, extra_checkers: Optional[Dict[str, Checker]] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param extra_checkers: 参数 extra_checkers
        :return: 返回处理结果。
        """
        self.extra = dict(extra_checkers or {})

    def run(self, content: str, meta: Optional[Dict] = None) -> CleanseReport:
        """run。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        meta = meta or {}
        issues: List[CleanseIssue] = []
        versions: Dict[str, str] = {}
        checkers: Dict[str, Checker] = {**_BUILTIN, **_registry, **self.extra}
        for name, checker in checkers.items():
            try:
                found = checker(content, meta) or []
                issues.extend(found)
                versions[name] = "ok"
            except Exception as e:  # 检查器自身故障不得放行
                issues.append(
                    CleanseIssue(
                        f"checker_fault:{name}", SEVERITY_ERROR,
                        f"检查器 {name} 执行异常：{type(e).__name__}",
                    )
                )
                versions[name] = "fault"
        passed = not any(i.severity == SEVERITY_ERROR for i in issues)
        return CleanseReport(passed=passed, issues=issues, checker_versions=versions)
