# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""附属工作模式契约门禁：双平面 + DSH 非必经 + 黄金路径 L1 可解析.

运行（backend/ 下）：
    ./.venv/Scripts/python.exe scripts/verify_annex_work_mode.py
退出码 0 = 通过。
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.hermes import planner_service  # noqa: E402
from app.services.hermes.annex_work_mode import (  # noqa: E402
    classify_plane,
    golden_path_for_executors,
    preferred_decompose_source,
    work_mode_report,
)
from app.schemas.hermes_orchestration import IntentEvent  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


async def _main() -> int:
    print("【附属工作模式契约 · HER-P0-1】")
    report = work_mode_report()
    check("DSH 非每单必经", report["dsh_required_every_task"] is False)
    check("任务默认 L1_template", report["default_task_source"] == "L1_template")
    check("双平面：列表=交互", classify_plane("客户列表") == "interactive")
    check("双平面：PI=任务", classify_plane("生成PI形式发票") == "task")
    check("L1 直通 preferred", preferred_decompose_source("履约") == "L1_template")

    print("【黄金路径 L1 解析】")
    ev_a = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gate-a",
        channel="web",
        intent="fulfillment",
        payload={"message": "履约订单 PI 发货跟单", "name": "Gate Buyer", "product": "board"},
    )
    g_a, s_a = await planner_service.decompose(ev_a, db=None)
    ex_a = {n.executor for n in g_a.nodes}
    check("GP-A source=L1", s_a == "L1_template", s_a)
    check("GP-A 含 goodjob_crm", "goodjob_crm" in ex_a, str(sorted(ex_a)))
    check("GP-A 命中黄金路径定义", (golden_path_for_executors(ex_a) or {}).get("id") == "GP-A")

    ev_b = IntentEvent(
        event_id=str(uuid.uuid4()),
        tenant_id="t-gate-b",
        channel="web",
        intent="social_outreach",
        payload={"message": "社媒拓客 WhatsApp 触达"},
    )
    g_b, s_b = await planner_service.decompose(ev_b, db=None)
    ex_b = {n.executor for n in g_b.nodes}
    check("GP-B source=L1", s_b == "L1_template", s_b)
    check("GP-B 含 trade_ai_agent", "trade_ai_agent" in ex_b, str(sorted(ex_b)))

    print("【分层位置】")
    layers = [x["layer"] for x in report["layer_stack"]]
    check(
        "插件在 Hermes 之下且并列",
        layers.index("hermes") < layers.index("executors_parallel")
        and set(report["annex_executors"]) == {"trade_ai_agent", "goodjob_crm"},
        " -> ".join(layers),
    )

    print("-" * 50)
    if FAILS:
        print(f"结果: 失败 {len(FAILS)} 项: {FAILS}")
        return 1
    print("结果: 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
