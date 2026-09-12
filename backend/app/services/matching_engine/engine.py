"""Product Finder 匹配引擎（纯函数，不依赖 FastAPI / SQLAlchemy）。

三层算法：
  第一层 硬条件过滤（Eligibility）：防火等级、导热系数上限，不满足即 REJECT。
  第二层 加权评分（0~100）：8 个维度加权求和。
  第三层 证据 + 解释：基于真实字段生成 evidence 与 explanation，给出 tier。

设计原则：
  - 纯函数 ``MatchingEngine.match(products, query)`` 接收「产品视图字典列表」与
    「查询字典」，返回结果字典，可被单测直接调用。
  - 任何判定都只能引用真实字段（fire_rating / thermal_conductivity /
    application_scenarios / technical_params / specifications / is_active 等）
    与用户输入，绝不编造认证、测试报告或不存在的字段值。
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 维度权重（之和为 1.0）
WEIGHTS: dict[str, float] = {
    "fireRating": 0.30,
    "standard": 0.20,
    "application": 0.15,
    "environment": 0.10,
    "market": 0.10,
    "installation": 0.05,
    "commercial": 0.05,
    "availability": 0.05,
}

# 防火等级序数（越高越优）。仅收录规划文档明确列出的等级。
FIRE_ORDER: dict[str, int] = {
    "A1": 8,
    "A2": 7,
    "B1": 6,
    "B2": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "E": 1,
    "F": 0,
}

# 无要求时的绝对等级评分（0~1）
FIRE_ORDER_ABS: dict[str, float] = {
    "A1": 1.0,
    "A2": 0.9,
    "B1": 0.8,
    "B2": 0.7,
    "B": 0.6,
    "C": 0.5,
    "D": 0.4,
    "E": 0.3,
    "F": 0.2,
}

# 环境关键词映射：类别 -> 触发词（小写）
_ENV_KEYWORDS: dict[str, list[str]] = {
    "高温": ["高温", "隔热", "耐火", "耐热", "热工", "thermal", "heat"],
    "防火": ["防火", "阻燃", "不燃", "fire"],
    "腐蚀": ["防腐", "耐腐蚀", "腐蚀", "酸碱", "抗化学", "chemical"],
    "潮湿": ["防潮", "防水", "耐水", "潮湿", "waterproof", "moisture"],
    "低温": ["耐寒", "低温", "防冻", "cold"],
    "震动": ["抗震", "减震", "seismic"],
}

# 安装方式关键词
_INSTALL_EASY: list[str] = ["粘贴", "干挂", "模块", "装配式", "易安装", "便捷", "卡扣", "拼接", "quick", "easy"]
_INSTALL_HARD: list[str] = ["浇筑", "湿作业", "复杂", "现场搅拌", "喷涂", "抹面"]

# 市场/出口线索
_MARKET_EXPORT_HINTS: list[str] = ["出口", "欧美", "欧盟", "海外", "europe", "usa", "北美", "中东", "东南亚"]

# specifications JSON 中可能出现的标准/认证键
_SPEC_STANDARD_KEYS: tuple[str, ...] = ("standard", "standards", "certification", "certifications", "cert", "norm")


# ---------------------------------------------------------------------------
# 文本 / 数值解析工具
# ---------------------------------------------------------------------------

def _norm(value: Optional[str]) -> str:
    """归一化字符串：去空格、转小写。"""
    if not value:
        return ""
    return str(value).strip().lower()


def _parse_fire_grade(value: Optional[str]) -> Optional[str]:
    """从产品/要求字符串解析防火等级 key（如 'A2'）。

    仅返回出现在 FIRE_ORDER 中的等级；未知等级返回 None（中性，不拒绝）。
    """
    if not value:
        return None
    clean = re.sub(r"[^A-Z0-9]", "", str(value).strip().upper())
    if not clean:
        return None
    m = re.match(r"^([A-F]+)(\d*)$", clean)
    if not m:
        return None
    key = clean if clean in FIRE_ORDER else None
    return key


def _parse_thermal(value: Optional[str]) -> Optional[float]:
    """从 '0.045 W/(m·K)'、'≤0.08' 等字符串中提取首个浮点数值。"""
    if not value:
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", str(value))
    if not nums:
        return None
    try:
        return float(nums[0])
    except ValueError:
        return None


def _tokenize(text: Optional[str]) -> set[str]:
    """生成可匹配 token 集合：拉丁词 + 中文二元组。"""
    tokens: set[str] = set()
    if not text:
        return tokens
    # 拉丁字母/数字词
    for m in re.findall(r"[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*", str(text)):
        tokens.add(m.lower())
    # 中文连续串 -> 单字（长度1）与二元组
    for run in re.findall(r"[\u4e00-\u9fff]+", str(text)):
        if len(run) == 1:
            tokens.add(run)
        else:
            for i in range(len(run) - 1):
                tokens.add(run[i : i + 2])
    return tokens


def _get_spec_standards(specs: Any) -> list[str]:
    """从 specifications JSON 中收集标准/认证候选字符串。"""
    candidates: list[str] = []
    if isinstance(specs, dict):
        for k in _SPEC_STANDARD_KEYS:
            v = specs.get(k)
            if v:
                candidates.append(str(v))
    return candidates


def _extract_text_standards(text: str) -> list[str]:
    """从文本中提取标准号片段，如 EN 13501、GB/T 25975、ASTM C552。"""
    return re.findall(
        r"(?:EN|GB|ASTM|ISO|BS|JIS|DIN)[\s]?[\w\.\-\/]+",
        text or "",
        re.IGNORECASE,
    )


# ---------------------------------------------------------------------------
# 各维度评分（输入真实字段，输出 0~1 子分 + 证据说明）
# ---------------------------------------------------------------------------

def _score_fire_rating(
    product_grade: Optional[str],
    product_ord: Optional[int],
    req_grade: Optional[str],
    req_ord: Optional[int],
) -> tuple[float, str]:
    """实现 评分firerating 的功能。
    
    :param product_grade: 参数 product_grade（类型: Optional[str]）
    :param product_ord: 参数 product_ord（类型: Optional[int]）
    :param req_grade: 参数 req_grade（类型: Optional[str]）
    :param req_ord: 参数 req_ord（类型: Optional[int]）
    :return: 返回 tuple[float, str] 结果
    """
    if req_ord is None:
        if product_grade is None:
            return 0.5, "防火等级未标注（中性）"
        sub = FIRE_ORDER_ABS.get(product_grade, 0.5)
        return sub, f"防火等级={product_grade}（绝对评分）"
    # 有要求
    if product_ord is None:
        return 0.5, f"防火等级未标注，要求{req_grade}（中性，未拒绝）"
    if product_ord >= req_ord:
        return 1.0, f"防火等级={product_grade}，满足/优于要求{req_grade}"
    diff = req_ord - product_ord
    sub = max(0.0, 0.7 - 0.15 * (diff - 1))
    return sub, f"防火等级={product_grade}，低于要求{req_grade}"


def _score_standard(
    specs: Any,
    tech_text: str,
    req_standard: Optional[str],
) -> tuple[float, str]:
    """实现 评分standard 的功能。
    
    :param specs: 参数 specs（类型: Any）
    :param tech_text: 参数 tech_text（类型: str）
    :param req_standard: 参数 req_standard（类型: Optional[str]）
    :return: 返回 tuple[float, str] 结果
    """
    candidates = _get_spec_standards(specs)
    candidates.extend(_extract_text_standards(tech_text))
    if req_standard:
        rs = _norm(req_standard)
        norm_candidates = [_norm(c) for c in candidates]
        if any(rs in nc or nc in rs for nc in norm_candidates):
            return 1.0, f"执行标准/认证命中要求「{req_standard}」"
        if candidates:
            return 0.5, f"标注标准[{', '.join(candidates[:3])}]，与要求「{req_standard}」不完全匹配"
        return 0.2, "未标注执行标准/认证"
    # 无要求：中性
    if candidates:
        return 0.5, f"执行标准/认证：{', '.join(candidates[:3]) or '已标注'}（无要求，中性）"
    return 0.5, "未提供标准要求（中性）"


def _score_application(
    app_text: Optional[str],
    tech_text: Optional[str],
    req_application: Optional[str],
) -> tuple[float, str]:
    """实现 评分application 的功能。
    
    :param app_text: 参数 app_text（类型: Optional[str]）
    :param tech_text: 参数 tech_text（类型: Optional[str]）
    :param req_application: 参数 req_application（类型: Optional[str]）
    :return: 返回 tuple[float, str] 结果
    """
    if not req_application or not req_application.strip():
        return 0.5, "未提供应用场景要求（中性）"
    req_tokens = _tokenize(req_application)
    if not req_tokens:
        return 0.5, "未提供应用场景要求（中性）"
    prod_text = f"{app_text or ''} {tech_text or ''}"
    prod_tokens = _tokenize(prod_text)
    if not prod_tokens:
        return 0.0, "产品未标注应用场景"
    matched = req_tokens & prod_tokens
    ratio = len(matched) / len(req_tokens)
    # 短语整体命中加权
    if _norm(req_application) in _norm(prod_text):
        ratio = max(ratio, 0.95)
    ratio = min(1.0, max(0.0, ratio))
    hits = sorted(matched)
    return ratio, f"应用场景匹配度 {ratio * 100:.0f}%（命中关键词：{', '.join(hits[:5]) or '无'}）"


def _infer_environments(text: str) -> list[str]:
    """实现 inferenvironments 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 list[str] 结果
    """
    found: list[str] = []
    low = _norm(text)
    for env, kws in _ENV_KEYWORDS.items():
        if any(k in low for k in kws):
            found.append(env)
    return found


def _score_environment(prod_text: str, req_environment: Optional[str]) -> tuple[float, str]:
    """实现 评分environment 的功能。
    
    :param prod_text: 参数 prod_text（类型: str）
    :param req_environment: 参数 req_environment（类型: Optional[str]）
    :return: 返回 tuple[float, str] 结果
    """
    inferred = _infer_environments(prod_text)
    if not req_environment:
        if inferred:
            return 0.6, f"推断适用环境：{', '.join(inferred)}（无要求，中性偏正）"
        return 0.5, "未提供环境要求（中性）"
    req = _norm(req_environment)
    req_cat = None
    for env, kws in _ENV_KEYWORDS.items():
        if req == env or any(k in req for k in kws):
            req_cat = env
            break
    if req_cat:
        if req_cat in inferred:
            return 0.9, f"适用环境命中要求「{req_environment}」（{', '.join(inferred)}）"
        if inferred:
            return 0.4, f"产品环境[{', '.join(inferred)}]与要求「{req_environment}」不完全匹配"
        return 0.3, f"产品未体现环境「{req_environment}」"
    if inferred:
        return 0.6, f"产品适用环境：{', '.join(inferred)}（要求未识别为已知类别）"
    return 0.5, "环境信息不足（中性）"


def _score_market(prod_text: str, req_country: Optional[str]) -> tuple[float, str]:
    """实现 评分market 的功能。
    
    :param prod_text: 参数 prod_text（类型: str）
    :param req_country: 参数 req_country（类型: Optional[str]）
    :return: 返回 tuple[float, str] 结果
    """
    low = _norm(prod_text)
    has_export = any(h in low for h in _MARKET_EXPORT_HINTS)
    if req_country:
        if has_export:
            return 0.7, f"产品标注出口/海外能力，目标市场「{req_country}」（中性偏正）"
        return 0.5, f"无国家/市场字段，目标市场「{req_country}」无法核验（中性）"
    return 0.5, "无国家/市场字段（中性）"


def _score_installation(prod_text: str, req_installation: Optional[str]) -> tuple[float, str]:
    """实现 评分installation 的功能。
    
    :param prod_text: 参数 prod_text（类型: str）
    :param req_installation: 参数 req_installation（类型: Optional[str]）
    :return: 返回 tuple[float, str] 结果
    """
    low = _norm(prod_text)
    easy = any(k in low for k in _INSTALL_EASY)
    hard = any(k in low for k in _INSTALL_HARD)
    if easy and not hard:
        base = 0.9
    elif hard and not easy:
        base = 0.3
    elif easy and hard:
        base = 0.6
    else:
        base = 0.5
    note: list[str] = []
    if easy:
        note.append("易安装")
    if hard:
        note.append("湿作业/复杂")
    label = "/".join(note) if note else "未知"
    if req_installation:
        rl = _norm(req_installation)
        if any(k in rl for k in _INSTALL_EASY) and easy:
            base = max(base, 0.95)
        elif any(k in rl for k in _INSTALL_HARD) and hard:
            base = max(base, 0.9)
        return base, f"施工方式：{label}（要求「{req_installation}」）"
    return base, f"施工方式：{label}"


def _score_commercial() -> tuple[float, str]:
    """实现 评分commercial 的功能。
    
    :return: 返回 tuple[float, str] 结果
    """
    return 0.5, "商务条款（MOQ/价格/货期）未标注（中性）"


def _score_availability(is_active: bool) -> tuple[float, str]:
    """实现 评分availability 的功能。
    
    :param is_active: 参数 is_active（类型: bool）
    :return: 返回 tuple[float, str] 结果
    """
    return (1.0 if is_active else 0.0), ("在售" if is_active else "已下架/停用")


# ---------------------------------------------------------------------------
# 引擎主入口
# ---------------------------------------------------------------------------

class MatchingEngine:
    """产品匹配引擎。纯函数，可单测，不依赖 Web 框架。"""
    @staticmethod
    def match(products: list[dict[str, Any]], query: dict[str, Any]) -> dict[str, Any]:
        """对产品列表执行 过滤 + 评分 + 证据生成。

        Args:
            products: 产品视图字典列表（含 id/name/slug/image_url/fire_rating/
                thermal_conductivity/technical_params/application_scenarios/
                advantages/specifications/category_id/is_active 等键）。
            query: 查询字典（含 application / fire_rating / max_thermal_conductivity /
                standard / environment / country / installation / top_n）。

        Returns:
            {
                "query": {...},
                "total_products": int,
                "matches": [ {...} ],
                "rejected": [ {...} ],
            }
        """
        req: dict[str, Any] = query or {}
        parsed = MatchingEngine._parse_query(req)
        req_grade = _parse_fire_grade(parsed["fire_req"]) if parsed["fire_req"] else None
        req_ord = FIRE_ORDER.get(req_grade) if req_grade else None  # type: ignore[arg-type]
        matches: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for p in products:
            reject_reason = MatchingEngine._reject_if_ineligible(
                p, parsed["fire_req"], req_ord, parsed["thermal_req"]
            )
            if reject_reason is not None:
                rejected.append(
                    {
                        "product_id": p.get("id"),
                        "name": p.get("name") or "",
                        "reason": reject_reason,
                    }
                )
                continue
            match = MatchingEngine._score_product(p, parsed, req_ord)
            matches.append(match)

        # 按综合分降序，取前 top_n
        matches.sort(key=lambda m: m["score"], reverse=True)
        matches = matches[: max(1, parsed["top_n"])]
        return {
            "query": {
                "application": req.get("application"),
                "fire_rating": req.get("fire_rating"),
                "max_thermal_conductivity": req.get("max_thermal_conductivity"),
                "standard": req.get("standard"),
                "environment": req.get("environment"),
                "country": req.get("country"),
                "installation": req.get("installation"),
                "top_n": req.get("top_n", 5),
            },
            "total_products": len(products),
            "matches": matches,
            "rejected": rejected,
        }

    @staticmethod
    def _parse_query(req: dict[str, Any]) -> dict[str, Any]:
        """解析查询参数为规范化 dict，供过滤与评分共用。"""
        return {
            "application": req.get("application"),
            "fire_req": req.get("fire_rating"),
            "thermal_req": req.get("max_thermal_conductivity"),
            "std_req": req.get("standard"),
            "env_req": req.get("environment"),
            "country_req": req.get("country"),
            "inst_req": req.get("installation"),
            "top_n": int(req.get("top_n") or 5),
        }

    @staticmethod
    def _reject_if_ineligible(
        p: dict[str, Any],
        fire_req: Any,
        req_ord: Optional[int],
        thermal_req: Any,
    ) -> Optional[str]:
        """第一层硬条件过滤：防火等级 / 导热系数，不满足返回拒绝原因。"""
        prod_grade = _parse_fire_grade(p.get("fire_rating"))
        prod_ord = FIRE_ORDER.get(prod_grade) if prod_grade else None  # type: ignore[arg-type]
        if req_ord is not None and prod_ord is not None and prod_ord < req_ord:
            return f"防火等级 {prod_grade or '未知'} 不满足要求 {fire_req}"
        if thermal_req is not None:
            prod_thermal = _parse_thermal(p.get("thermal_conductivity"))
            if prod_thermal is not None and prod_thermal > float(thermal_req):
                return f"导热系数 {prod_thermal} W/(m·K) 超过上限 {thermal_req}"
        return None

    @staticmethod
    def _score_product(
        p: dict[str, Any],
        parsed: dict[str, Any],
        req_ord: Optional[int],
    ) -> dict[str, Any]:
        """第二层加权评分：基于真实字段计算子分、综合分、证据与解释。"""
        pid = p.get("id")
        name = p.get("name") or ""
        prod_text = " ".join(
            [
                str(p.get("application_scenarios") or ""),
                str(p.get("technical_params") or ""),
                str(p.get("advantages") or ""),
            ]
        )
        specs = p.get("specifications") or {}
        prod_grade = _parse_fire_grade(p.get("fire_rating"))
        prod_ord = FIRE_ORDER.get(prod_grade) if prod_grade else None  # type: ignore[arg-type]
        fr_sub, fr_ev = _score_fire_rating(prod_grade, prod_ord, parsed["fire_req"], req_ord)
        std_sub, std_ev = _score_standard(specs, str(p.get("technical_params") or ""), parsed["std_req"])
        app_sub, app_ev = _score_application(
            p.get("application_scenarios"), p.get("technical_params"), parsed["application"]
        )
        env_sub, env_ev = _score_environment(prod_text, parsed["env_req"])
        mkt_sub, mkt_ev = _score_market(prod_text, parsed["country_req"])
        inst_sub, inst_ev = _score_installation(prod_text, parsed["inst_req"])
        com_sub, com_ev = _score_commercial()
        avail_sub, avail_ev = _score_availability(bool(p.get("is_active")))
        subs = {
            "fireRating": fr_sub,
            "standard": std_sub,
            "application": app_sub,
            "environment": env_sub,
            "market": mkt_sub,
            "installation": inst_sub,
            "commercial": com_sub,
            "availability": avail_sub,
        }
        total = sum(WEIGHTS[k] * subs[k] for k in WEIGHTS) * 100.0
        score = round(total, 2)
        tier = "推荐" if score >= 75 else ("备选" if score >= 55 else "不推荐")
        evidence = [
            f"防火：{fr_ev}（权重30%，子分{round(fr_sub * 100)}）",
            f"标准：{std_ev}（权重20%，子分{round(std_sub * 100)}）",
            f"应用：{app_ev}（权重15%）",
            f"环境：{env_ev}（权重10%）",
            f"市场：{mkt_ev}（权重10%）",
            f"安装：{inst_ev}（权重5%）",
            f"商务：{com_ev}（权重5%）",
            f"在售：{avail_ev}（权重5%）",
        ]
        explanation = MatchingEngine._build_explanation(
            name, score, tier, fr_ev, app_ev, std_ev
        )
        return {
            "product_id": pid,
            "name": name,
            "slug": p.get("slug"),
            "image_url": p.get("image_url"),
            "fire_rating": p.get("fire_rating"),
            "thermal_conductivity": p.get("thermal_conductivity"),
            "score": score,
            "tier": tier,
            "dimensions": {k: round(v * 100, 2) for k, v in subs.items()},
            "evidence": evidence,
            "explanation": explanation,
        }

    @staticmethod
    def _build_explanation(
        name: str,
        score: float,
        tier: str,
        fr_ev: str,
        app_ev: str,
        std_ev: str,
    ) -> str:
        """基于 evidence 确定性生成一句中文推荐理由（不调用 LLM）。"""
        fr_short = fr_ev.split("（")[0]
        app_short = app_ev.split("（")[0]
        parts = [
            f"「{name}」综合匹配度 {score} 分，评级「{tier}」",
            f"防火：{fr_short}",
            f"应用：{app_short}",
        ]
        if "命中" in std_ev:
            parts.append(f"标准：{std_ev.split('（')[0]}")
        return "；".join(parts) + "。"
