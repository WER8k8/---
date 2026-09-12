"""Hermes 存在第一准则 — 排名效果优先于一切运维动作。

流量入口分散（百度 / 豆包 / 360 / 无头浏览器 / 各厂大模型），机制各异且蒸馏频繁；
Hermes 驱动 ECC 专家 **每日** 攻坚探测、战术更新与回归告警，保证 GEO/搜索排名信号不跌。
"""

from __future__ import annotations

from typing import Any, Final

RANK_FIRST_VERSION: Final[str] = "2026-06-v1"

RANK_FIRST_PRINCIPLE: Final[str] = (
    "Hermes 的第一存在意义：保证租户在分散流量入口下的排名与 AI 推荐效果。"
    "无排名信号 → 无电话 → 无开户与续费；其它运维动作不得挤占每日排名攻坚带宽。"
)

DAILY_RANK_DUTIES: Final[tuple[str, ...]] = (
    "multi_engine_recommend_probe",  # 豆包/通义/DeepSeek 等 recommend 探针
    "geo_tactics_radar",  # 外网 GEO 论文与平台 changelog（Tavily + 公开 RSS）
    "platform_discovery_gap",  # catalog vs live 适配器，扩面优先级
    "rank_guard_regression",  # 收录率 / SEO 分 / probe 通过率 vs 昨日
    "ecc_expert_readonly_review",  # ECC 专家只读评审高影响变更，不自动热更生产
    "remediation_suggest_only",  # 输出补强建议，人审后执行发布/改稿
)

FORBIDDEN_WITHOUT_RANK_CHECK: Final[tuple[str, ...]] = (
    "全量内容重写",
    "生产 Schema 热更",
    "对外承诺新平台已上线",
)

CONSTITUTION_RELATION: Final[str] = (
    "与 maintenance_constitution 并存：排名攻坚仅使用 read_probe / write_patrol_snapshot / "
    "emit_alert / suggest_remediation；禁止自动发布与自动改库。"
)


def rank_first_payload() -> dict[str, Any]:
    """rank_first_payload。
    :return: 返回处理结果。
    """
    return {
        "version": RANK_FIRST_VERSION,
        "principle": RANK_FIRST_PRINCIPLE,
        "daily_duties": list(DAILY_RANK_DUTIES),
        "forbidden_without_rank_check": list(FORBIDDEN_WITHOUT_RANK_CHECK),
        "constitution_relation": CONSTITUTION_RELATION,
        "schedule_cron": "0 7 * * * Asia/Shanghai",
        "owner": "Hermes Agent → ECC 专家面板（产品/GEO/QA/安全）",
    }
