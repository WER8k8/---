# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""E-6 混沌/压测基线：dispatch 幂等与并发诚实率（不依赖外部负载工具）。

原则：
    · 本地可跑：重复 materialize/claim/dispatch 路径
    · 记录耗时、失败诚实率；不吞错误
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Callable


def run_dispatch_baseline(
    *,
    ops_store: Any,
    n: int = 20,
    make_card: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """跟单卡写路径基线：materialize 幂等 + 耗时。"""
    n = max(1, min(200, int(n)))
    ids = [f"INQ-BASE-{uuid.uuid4().hex[:8]}" for _ in range(n)]
    lat_ms: list[float] = []
    errors = 0
    t0 = time.perf_counter()
    for iid in ids:
        s = time.perf_counter()
        try:
            if make_card:
                make_card(iid)
            else:
                ops_store.materialize(tenant_id="demo", inquiry_id=iid, stage="new")
                ops_store.record_touch(iid, channel="baseline", summary="压测触达", next_action="下一步")
        except Exception:
            errors += 1
        lat_ms.append((time.perf_counter() - s) * 1000)
    # 幂等：重复 materialize 不应炸
    idem_err = 0
    for iid in ids[: min(5, n)]:
        try:
            ops_store.materialize(tenant_id="demo", inquiry_id=iid, stage="new")
        except Exception:
            idem_err += 1
    total_ms = (time.perf_counter() - t0) * 1000
    lat_ms.sort()
    p50 = lat_ms[len(lat_ms) // 2] if lat_ms else 0
    p95 = lat_ms[int(len(lat_ms) * 0.95) - 1] if len(lat_ms) >= 2 else (lat_ms[0] if lat_ms else 0)
    honesty = 1.0 if errors == 0 else 1 - (errors / n)
    return {
        "ok": errors == 0 and idem_err == 0,
        "n": n,
        "errors": errors,
        "idempotent_errors": idem_err,
        "total_ms": round(total_ms, 2),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "honesty_rate": round(honesty, 3),
        "plain_summary": (
            f"基线 {n} 次跟单卡写：p50={p50:.2f}ms p95={p95:.2f}ms，错误 {errors}，幂等错误 {idem_err}。"
            + ("全部诚实成功。" if errors == 0 and idem_err == 0 else "有失败，见 errors。")
        ),
        "hint": "内存基线；PG/worker 全链压测需在开发栈上另跑。",
    }


def run_claim_collision_baseline(*, claim_fn: Any, inquiry_id: str) -> dict[str, Any]:
    """撞单路径基线：无 confirm 不得抢走。"""
    t0 = time.perf_counter()
    r1 = claim_fn(inquiry_id=inquiry_id, user_id="alice", tenant_id="demo", confirm_force=False)
    r2 = claim_fn(inquiry_id=inquiry_id, user_id="bob", tenant_id="demo", confirm_force=False)
    blocked = (r2.get("ok") is False) or (r2.get("code") in ("collision", "already_owner"))
    ms = (time.perf_counter() - t0) * 1000
    return {
        "ok": bool(blocked),
        "first_code": r1.get("code"),
        "second_code": r2.get("code"),
        "ms": round(ms, 2),
        "plain_summary": (
            "撞单基线：第二人无 confirm 未抢走（符合红线）。"
            if blocked
            else f"撞单基线失败：second={r2.get('code')}（应被 collision 拦住）"
        ),
    }
