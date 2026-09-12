"""增长跑盘预设模板。"""

from __future__ import annotations

from typing import Any

GROWTH_WORKFLOW_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "id": "full_diagnosis",
        "label": "全链路诊断",
        "goal": "热词扫描 → 选词 → 草稿 → 质检 → 引流监测 → 结论",
        "hint": "适合首次使用或周度复盘",
        "mode": "full",
    },
    {
        "id": "quality_only",
        "label": "质检 + 监测",
        "goal": "对已有正文做合规/SEO/GEO 质检，并刷新引流监测",
        "hint": "请填写待检正文，跳过自动选词",
        "mode": "quality_only",
    },
    {
        "id": "keyword_scan",
        "label": "热词洞察",
        "goal": "扫描热词库并给出主攻词建议",
        "hint": "不生成草稿，适合选题阶段",
        "mode": "keyword_only",
    },
    {
        "id": "traffic_audit",
        "label": "引流通道审计",
        "goal": "刷新 20+ 监测通道快照并输出探针缺口",
        "hint": "仅跑引流监测与汇总",
        "mode": "traffic_only",
    },
)


def list_presets() -> list[dict[str, Any]]:
    """实现 列出presets 的功能。
    
    :return: 返回 list[dict[str, Any]] 结果
    """
    return [dict(p) for p in GROWTH_WORKFLOW_PRESETS]


def preset_by_id(preset_id: str | None) -> dict[str, Any] | None:
    """实现 presetbyID 的功能。
    
    :param preset_id: 参数 preset_id（类型: str | None）
    :return: 返回 dict[str, Any] | None 结果
    """
    if not preset_id:
        return None
    for p in GROWTH_WORKFLOW_PRESETS:
        if p["id"] == preset_id:
            return dict(p)
    return None
