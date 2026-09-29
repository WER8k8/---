# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块2 HS-1 零漂移**判据**：用基线的 593 组入参重跑当前工作区计算器，逐字段 diff。

用法::

    cd backend
    ./.venv/Scripts/python.exe scripts/qa/verify_boq_zero_drift.py

- 基线：`docs/模块2-零漂移基线-2026-09-27.json`（其中 `calculator_cases[i].result`
  为 git HEAD 改动前版本的输出）。
- 判定：**未传 industry_profile** 时，当前代码输出须与基线**逐字段 0 差异**。
- 退出码 0 = 零漂移通过；1 = 存在漂移（列出差异字段与用例）。

只读：不修改任何生产代码。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent
DEFAULT_BASELINE = REPO_ROOT / "docs" / "模块2-零漂移基线-2026-09-27.json"


def _diff(pa: str, x, y, out: list[str]) -> None:
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            _diff(f"{pa}.{k}" if pa else str(k), x.get(k), y.get(k), out)
    elif x != y:
        out.append(f"{pa}: baseline={x!r} current={y!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    ap.add_argument("--max-show", type=int, default=15)
    args = ap.parse_args()

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    cases = baseline["calculator_cases"]

    sys.path.insert(0, str(BACKEND_ROOT))
    from app.services.boq_calculator import BOQCalculator

    calc = BOQCalculator()
    failures: list[dict] = []
    for c in cases:
        params = c["params"]
        expected = c["result"]
        try:
            got = calc.calculate(dict(params))
        except Exception as exc:  # noqa: BLE001
            got = {"__exception__": f"{type(exc).__name__}: {exc}"}
        d: list[str] = []
        _diff("", expected, got, d)
        if d:
            failures.append({
                "i": c["i"], "section": c["section"],
                "material_type": params.get("material_type"),
                "quantity_sqm": params.get("quantity_sqm"),
                "diffs": d,
            })

    total = len(cases)
    passed = total - len(failures)
    print("=" * 72)
    print(f"HS-1 零漂移核对：{passed}/{total} 通过，{len(failures)} 失败")
    print(f"基线：{args.baseline}")
    print(f"基线来源：{baseline.get('baseline_source')}")
    print("=" * 72)

    if failures:
        by_mat: dict[str, int] = {}
        field_cnt: dict[str, int] = {}
        for f in failures:
            by_mat[str(f["material_type"])] = by_mat.get(str(f["material_type"]), 0) + 1
            for s in f["diffs"]:
                field_cnt[s.split(":")[0]] = field_cnt.get(s.split(":")[0], 0) + 1
        print(f"失败按材料：{by_mat}")
        print(f"失败字段 TOP：{sorted(field_cnt.items(), key=lambda t: -t[1])[:10]}")
        print("-" * 72)
        for f in failures[: args.max_show]:
            print(f"[case {f['i']} | {f['section']} | {f['material_type']} q={f['quantity_sqm']}]")
            for s in f["diffs"][:6]:
                print(f"    {s}")
        if len(failures) > args.max_show:
            print(f"... 其余 {len(failures) - args.max_show} 例略")
        return 1

    print("零漂移通过：当前代码在未传 industry_profile 时与基线逐字段一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
