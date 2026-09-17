# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RADAR-07 / AI-03：Hermes ops vs 租户 customer AI 场景分流快照。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.ai_invocation_service import (
    CUSTOMER_SCENARIO_DEFAULT,
    LANE_CUSTOMER,
    LANE_OPS,
    OPS_SCENARIO_DEFAULT,
    OPS_SCENARIO_MAP,
    resolve_lane_scenario,
)


def build_ai_lane_snapshot(db: Session | None = None) -> dict[str, Any]:
    """build_ai_lane_snapshot。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    ops_samples = list(OPS_SCENARIO_MAP.keys())[:6]
    customer_samples = ["inference", "article", "market_research", "article_to_video_script"]
    has_key = False
    try:
        from app.services.ai_key_probe import ai_key_status
        if db is not None:
            has_key = bool(ai_key_status(db).get("has_real_key"))
    except Exception:
        pass

    return {
        "radar_07": {
            "ecc_llm_scenario": "hermes_tech_radar",
            "resolved_ops_scenario": resolve_lane_scenario("hermes_tech_radar", lane=LANE_OPS),
        },
        "lanes": {
            LANE_OPS: {
                "default": OPS_SCENARIO_DEFAULT,
                "scenario_map": OPS_SCENARIO_MAP,
                "resolved_samples": {
                    s: resolve_lane_scenario(s, lane=LANE_OPS) for s in ops_samples
                },
            },
            LANE_CUSTOMER: {
                "default": CUSTOMER_SCENARIO_DEFAULT,
                "resolved_samples": {
                    s: resolve_lane_scenario(s, lane=LANE_CUSTOMER) for s in customer_samples
                },
            },
        },
        "has_real_key": has_key,
        "doc": "docs/geo/tech-radar.md",
    }
