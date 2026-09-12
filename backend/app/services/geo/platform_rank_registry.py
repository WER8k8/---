"""平台 × GEO 排名权重注册表 — 排名优先准则下的发布顺序。

平台越多、且覆盖 AI/搜索训练源，GEO 引用面越广；本模块为「先上高权重、再扩探索」提供排序。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.publish_capability_registry import (
    STUB_PLATFORM_DISPLAY_NAMES,
    TEXT_ADAPTER_PLATFORM_NAMES,
)

AdapterStatus = Literal["live", "stub", "exploration"]

# geo_weight: 对国内/出口 AI 引用与搜索反哺的相对贡献（0~1，非官方算法）
# rank_priority: 越小越先发布（排名优先）
_PLATFORM_PROFILES: tuple[tuple[str, float, AdapterStatus, str, str, int], ...] = (
    ("百家号", 0.92, "live", "cn", "article", 10),
    ("知乎", 0.90, "live", "cn", "article", 12),
    ("头条号", 0.88, "live", "cn", "article", 14),
    ("微信公众号", 0.95, "live", "cn", "article", 8),
    ("CSDN", 0.72, "live", "cn", "article", 40),
    ("微博", 0.70, "live", "cn", "article", 45),
    ("小红书", 0.85, "live", "cn", "article", 18),
    ("搜狐号", 0.82, "exploration", "cn", "article", 20),
    ("网易号", 0.80, "exploration", "cn", "article", 22),
    ("企鹅号", 0.78, "exploration", "cn", "article", 24),
    ("一点资讯", 0.65, "exploration", "cn", "article", 50),
    ("大鱼号", 0.62, "exploration", "cn", "article", 52),
    ("简书", 0.55, "exploration", "cn", "article", 55),
    ("哔哩哔哩", 0.75, "stub", "cn", "long_video", 28),
    ("抖音", 0.88, "stub", "cn", "short_video", 16),
    ("快手", 0.76, "stub", "cn", "short_video", 30),
    ("微信视频号", 0.90, "stub", "cn", "short_video", 15),
    ("1688", 0.86, "exploration", "cn", "article", 26),
    ("慧聪网", 0.74, "exploration", "cn", "article", 32),
    ("LinkedIn", 0.88, "live", "global", "article", 11),
    ("YouTube", 0.85, "stub", "global", "long_video", 17),
    ("TikTok", 0.87, "stub", "global", "short_video", 19),
    ("Facebook", 0.72, "live", "global", "article", 35),
    ("Instagram", 0.78, "live", "global", "short_video", 25),
    ("X", 0.68, "live", "global", "article", 38),
    ("Alibaba.com", 0.84, "exploration", "global", "article", 21),
    ("Made-in-China.com", 0.80, "exploration", "global", "article", 23),
    ("Global Sources", 0.72, "exploration", "global", "article", 36),
    ("Reddit", 0.60, "stub", "global", "article", 48),
    ("Medium", 0.58, "exploration", "global", "article", 54),
)


@dataclass(frozen=True)
class PlatformRankProfile:
    name: str
    geo_weight: float
    adapter_status: AdapterStatus
    region: str
    content_type: str
    rank_priority: int
    @property
    def rank_score(self) -> float:
        """综合分：权重高 + 已 live 优先；stub/exploration 降权但不排除。"""
        status_factor = {"live": 1.0, "stub": 0.55, "exploration": 0.35}.get(
            self.adapter_status, 0.3
        )
        return round(self.geo_weight * status_factor, 4)


def _sync_adapter_status(name: str, declared: AdapterStatus) -> AdapterStatus:
    """实现 同步adapter状态 的功能。
    
    :param name: 参数 name（类型: str）
    :param declared: 参数 declared（类型: AdapterStatus）
    :return: 返回 AdapterStatus 结果
    """
    if name in TEXT_ADAPTER_PLATFORM_NAMES:
        return "live"
    if name in STUB_PLATFORM_DISPLAY_NAMES:
        return "stub"
    return declared


def all_platform_rank_profiles() -> list[PlatformRankProfile]:
    """实现 all平台排名profiles 的功能。
    
    :return: 返回 list[PlatformRankProfile] 结果
    """
    out: list[PlatformRankProfile] = []
    for name, weight, status, region, ctype, priority in _PLATFORM_PROFILES:
        out.append(
            PlatformRankProfile(
                name=name,
                geo_weight=weight,
                adapter_status=_sync_adapter_status(name, status),
                region=region,
                content_type=ctype,
                rank_priority=priority,
            )
        )
    return sorted(out, key=lambda p: p.rank_priority)


def publish_order_for_ranking(
    *,
    region: str | None = None,
    live_only: bool = False,
    limit: int = 8,
) -> list[str]:
    """排名优先：返回建议发布平台名（先 live 高权重，再 stub 视频矩阵）。"""
    profiles = all_platform_rank_profiles()
    if region in ("cn", "global"):
        profiles = [p for p in profiles if p.region == region]
    profiles.sort(key=lambda p: (-p.rank_score, p.rank_priority))
    if live_only:
        profiles = [p for p in profiles if p.adapter_status == "live"]
    return [p.name for p in profiles[: max(1, limit)]]


def revenue_loop_kpi_labels() -> dict[str, str]:
    """排名 → 电话 → 开户 → 收益 闭环指标说明（租户/超管看板文案）。"""
    return {
        "geo_probe_pass_rate": "大模型推荐位通过率",
        "platform_live_count": "已接入可发平台数",
        "inquiry_count_30d": "近30天询盘/电话",
        "tenant_conversion": "询盘→开户转化",
        "mrr_delta": "续费与裂变收益",
        "north_star": "有排名信号才有电话，有电话才有开户与循环收益",
    }
