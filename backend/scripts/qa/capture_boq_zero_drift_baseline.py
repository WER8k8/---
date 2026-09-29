# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块2 零漂移「黄金基线」采集脚本（只读，不改任何生产代码）。

目的
----
锁定「未配置 Industry Profile 时，BOQ 核价引擎逐字段行为」的不可篡改基线，
供模块2 改动落盘后用**同一组入参**重跑并与基线逐字段 diff（HS-1 零漂移判据）。

关键设计（为什么这份基线不可争议）
----------------------------------
- 采用两路对照：
  * ``result`` = **git HEAD 已提交版本**的 boq_calculator.py 输出 → 真正的「改动前黄金基线」；
  * ``result_worktree`` = 采集时刻工作区版本的输出 → 仅作在途对照（可能已被改动）。
  二者若不一致，说明工作区已相对 HEAD 漂移，本脚本会显式列出漂移字段。
- 采集**前后各记录一次** git HEAD / status / 关键文件 md5，任意一项变化即 ``reliable=false``。
- 抽样方式与 seed 全部落盘，可复现。

用法::

    cd backend
    ./.venv/Scripts/python.exe scripts/qa/capture_boq_zero_drift_baseline.py \
        --out "../docs/模块2-零漂移基线-2026-09-27.json"

硬约束：只读生产代码；不写 app/、不改既有测试、不改迁移、不提交 git。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import itertools
import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent

# ── 被监控的关键文件（内容变化即视为代码被改动） ──────────────────
WATCHED_FILES = [
    "backend/app/services/boq_calculator.py",
    "backend/app/services/boq_pipeline_service.py",
    "backend/app/services/industry_profile_service.py",
]

DB_URL = "postgresql://youding:youding@localhost:5433/youding_dev"
DEFAULT_OUT = REPO_ROOT / "docs" / "模块2-零漂移基线-2026-09-27.json"

# ── 入参维度 ────────────────────────────────────────────────────
MATERIAL_TYPES = ["marble", "granite", "ceramic", "wood", "metal"]
# 覆盖 MOQ 档 1000/3000 边界、<50 小批量加价分支
QUANTITIES = [10, 50, 100, 999, 1000, 1001, 2999, 3000, 5000]
THICKNESSES = [10, 20, 30]  # !=20 触发厚度乘数
GRADES = ["premium", "first_choice", "standard", "commercial", "b", "未知等级"]
SURFACES = ["polished", "honed", "flamed", "未知表面"]
EDGES = ["eased", "beveled", "ogee", "未知磨边"]
CERTIFICATIONS = [None, "ce", "iso9001", "sgs", "greenguard", "iso14001"]
INCOTERMS = ["FOB", "CIF", "DDP"]
SWITCH_KEYS = [
    "customization",
    "logo_printing",
    "inspection_required",
    "insurance_required",
    "small_batch_surcharge",
]
# 管道可达但**不在计算器基价表**内的材料（run_calculation 经 _material_of 会产出 porcelain）
EXTRA_MATERIALS = ["porcelain", "铝复合板", "unknown_material"]

SEED = 20260927
RANDOM_CASES = 500


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return (out.stdout or "").strip()


def snapshot_code_state() -> dict:
    state = {
        "git_head": git("rev-parse", "HEAD"),
        "git_status": git("status", "--porcelain"),
        "files": {},
    }
    for rel in WATCHED_FILES:
        p = REPO_ROOT / rel
        state["files"][rel] = {
            "exists": p.exists(),
            "md5": _md5(p) if p.exists() else None,
            "size": p.stat().st_size if p.exists() else None,
            "sha256": sha256_file(p) if p.exists() else None,
        }
    return state


# ── 加载两路计算器 ──────────────────────────────────────────────
def _load_module_from_source(name: str, source_path: Path):
    spec = importlib.util.spec_from_file_location(name, str(source_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_head_calculator() -> tuple[object, str]:
    """从 git HEAD 提取 boq_calculator.py 到临时文件并加载（真正的改动前版本）。"""
    head_sha = git("rev-parse", "HEAD")
    src = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", "HEAD:backend/app/services/boq_calculator.py"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if src.returncode != 0 or not src.stdout:
        raise RuntimeError(f"无法从 HEAD 提取 boq_calculator.py: {src.stderr}")
    tmp = Path(tempfile.mkdtemp(prefix="boq_head_"))
    tmp_file = tmp / "boq_calculator_head.py"
    tmp_file.write_text(src.stdout, encoding="utf-8")
    mod = _load_module_from_source("boq_calculator_head", tmp_file)
    return mod, head_sha


def load_worktree_calculator():
    sys.path.insert(0, str(BACKEND_ROOT))
    import importlib
    mod = importlib.import_module("app.services.boq_calculator")
    return mod


# ── 入参用例构造 ────────────────────────────────────────────────
def _baseline_params() -> dict:
    return {
        "material_type": "ceramic",
        "quantity_sqm": 1000,
        "incoterms": "FOB",
        "thickness_mm": 20,
        "material_grade": "standard",
        "surface_finish": "polished",
        "edge_profile": "eased",
    }


def build_cases() -> tuple[list[dict], dict]:
    """返回 (cases, sampling_meta)。cases 每项含 section 标记。"""
    cases: list[dict] = []
    counts: dict[str, int] = {}

    # A. 单维遍历覆盖：每个维度每个取值至少出现一次（其它维取基线）
    def add_single(dim, values):
        for v in values:
            p = _baseline_params()
            p[dim] = v
            cases.append({"section": "A_axis_coverage", "params": p})
        counts["A_axis_coverage"] = counts.get("A_axis_coverage", 0) + len(values)

    add_single("material_type", MATERIAL_TYPES + EXTRA_MATERIALS)
    add_single("quantity_sqm", QUANTITIES)
    add_single("thickness_mm", THICKNESSES)
    add_single("material_grade", GRADES)
    add_single("surface_finish", SURFACES)
    add_single("edge_profile", EDGES)
    add_single("certification", CERTIFICATIONS)
    add_single("incoterms", INCOTERMS)

    # B. 开关组合：5 个布尔开关的 32 种组合（quantity 取 100 同时命中/不命中 MOQ，
    #    小批量分支在 qty=10 时才可达，故另补小批量开关组）
    for bits in itertools.product([False, True], repeat=len(SWITCH_KEYS)):
        p = _baseline_params()
        p["quantity_sqm"] = 100
        for k, b in zip(SWITCH_KEYS, bits):
            p[k] = b
        cases.append({"section": "B_switch_matrix", "params": p})
    # 小批量（<50）分支 × small_batch_surcharge
    for q in (10, 50, 49):
        for sb in (True, False):
            p = _baseline_params()
            p["quantity_sqm"] = q
            p["small_batch_surcharge"] = sb
            cases.append({"section": "B_switch_matrix", "params": p})
    counts["B_switch_matrix"] = 32 + 6

    # C. 随机抽样（固定 seed）：从核心维笛卡尔空间中均匀抽取 RANDOM_CASES 组
    core_dims = [
        ("material_type", MATERIAL_TYPES + EXTRA_MATERIALS),
        ("quantity_sqm", QUANTITIES),
        ("thickness_mm", THICKNESSES),
        ("material_grade", GRADES),
        ("surface_finish", SURFACES),
        ("edge_profile", EDGES),
        ("certification", CERTIFICATIONS),
        ("incoterms", INCOTERMS),
    ]
    total_space = 1
    for _, vals in core_dims:
        total_space *= len(vals)
    rng = random.Random(SEED + 1)
    picks = rng.sample(range(total_space), min(RANDOM_CASES, total_space))
    for flat in picks:
        idx = flat
        params = _baseline_params()
        for name, vals in reversed(core_dims):
            idx, r = divmod(idx, len(vals))
            params[name] = vals[r]
        # 随机挂 5 个布尔开关
        for k in SWITCH_KEYS:
            params[k] = rng.random() < 0.5
        cases.append({"section": "C_random_sample", "params": params})
    counts["C_random_sample"] = len(picks)

    # D. 错误路径 & 边界
    err = [
        {"quantity_sqm": 100, "incoterms": "FOB"},                       # 缺 material_type
        {"material_type": "ceramic", "incoterms": "FOB"},                # 缺 quantity_sqm
        {"material_type": "ceramic", "quantity_sqm": 100},               # 缺 incoterms
        {},                                                              # 全缺
        {"material_type": "", "quantity_sqm": 100, "incoterms": "FOB"},  # 空串 material_type
        {"material_type": "ceramic", "quantity_sqm": 0, "incoterms": "FOB"},   # 数量 0
        {"material_type": "ceramic", "quantity_sqm": -5, "incoterms": "FOB"},  # 负数量
        {"material_type": "ceramic", "quantity_sqm": 10_000_000, "incoterms": "FOB"},  # 超大数量
        {"material_type": "CERAMIC", "quantity_sqm": 100, "incoterms": "cif"},  # 大小写
        {"material_type": "ceramic", "quantity_sqm": "100", "incoterms": "FOB"},  # 字符串数量
        {"material_type": "porcelain", "quantity_sqm": 100, "incoterms": "FOB"},  # 表外材料
        {"material_type": "ceramic", "quantity_sqm": 100, "incoterms": "EXW"},    # 未知 incoterm
    ]
    for p in err:
        cases.append({"section": "D_error_edge", "params": p})
    counts["D_error_edge"] = len(err)

    meta = {
        "method": (
            "A 单维轴覆盖 + B 布尔开关全组合(2^5=32, 另补 <50 小批量 6 组) "
            "+ C 从核心维笛卡尔空间固定 seed 均匀抽样 + D 错误/边界路径"
        ),
        "seed": SEED,
        "random_cases_requested": RANDOM_CASES,
        "core_space_size": total_space,
        "section_counts": counts,
        "total_cases": len(cases),
        "dims": {
            "material_type": MATERIAL_TYPES + EXTRA_MATERIALS,
            "quantity_sqm": QUANTITIES,
            "thickness_mm": THICKNESSES,
            "material_grade": GRADES,
            "surface_finish": SURFACES,
            "edge_profile": EDGES,
            "certification": CERTIFICATIONS,
            "incoterms": INCOTERMS,
            "switches": SWITCH_KEYS,
        },
    }
    return cases, meta


# ── 管道层常量快照 ──────────────────────────────────────────────
def dump_constants(head_mod, wt_mod) -> dict:
    sys.path.insert(0, str(BACKEND_ROOT))
    pipe = None
    pipe_err = None
    try:
        from app.services import boq_pipeline_service as pipe
    except Exception as exc:  # noqa: BLE001
        pipe_err = f"{type(exc).__name__}: {exc}"

    def grab(mod, name):
        return getattr(mod, name, None)

    # 计算器内联基价表（函数内字面量 → 用 _get_base_price 反推）
    calc = wt_mod.BOQCalculator()
    inline_prices = {}
    for m in MATERIAL_TYPES + EXTRA_MATERIALS:
        try:
            inline_prices[m] = calc._get_base_price(m)
        except Exception as exc:  # noqa: BLE001
            inline_prices[m] = f"<err:{exc}>"

    constants = {
        "boq_calculator": {
            "MATERIAL_DENSITY": grab(wt_mod, "_MATERIAL_DENSITY"),
            "SURFACE_FEES": grab(wt_mod, "_SURFACE_FEES"),
            "EDGE_FEES": grab(wt_mod, "_EDGE_FEES"),
            "GRADE_MULTIPLIER": grab(wt_mod, "_GRADE_MULTIPLIER"),
            "BOQ_PARAMS": grab(wt_mod, "BOQ_PARAMS"),
            "inline_material_base_prices_probed": inline_prices,
            "note_base_price": "基价为 calculate / _get_base_price 内联字面量，此处用 _get_base_price() 反推",
            "default_moq_tiers": [
                {"min_quantity_sqm": 1000, "discount_rate": 0.05},
                {"min_quantity_sqm": 3000, "discount_rate": 0.08},
            ],
            "note_moq": "默认 moq_tiers 为 calculate 内联字面量；来源行见文件（模块2 前为 if qty>=3000/1000 硬编码）",
            "head_vs_worktree": {
                "_get_base_price_fallback": "见 file_diff 中 _get_base_price 实现；采集脚本已记录两路输出差异",
            },
        },
        "boq_pipeline_service": (
            {
                "MATERIAL_TOKENS": grab(pipe, "_MATERIAL_TOKENS"),
                "UNIT_ALIASES_sample": dict(list(grab(pipe, "_UNIT_ALIASES").items())[:10]),
            }
            if pipe is not None
            else {"__import_error__": pipe_err}
        ),
    }
    return constants


def _diff_fields(a: dict, b: dict) -> list[str]:
    """比较两组 calculate 输出，返回不同的字段路径列表。"""
    diffs: list[str] = []

    def walk(pa: str, x, y):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                walk(f"{pa}.{k}" if pa else str(k), x.get(k), y.get(k))
        elif x != y:
            diffs.append(f"{pa}: head={x!r} worktree={y!r}")

    walk("", a, b)
    return diffs


# ── 运行矩阵 ────────────────────────────────────────────────────
def run_matrix(head_mod, wt_mod, cases: list[dict]) -> tuple[list[dict], list[dict]]:
    head_calc = head_mod.BOQCalculator()
    wt_calc = wt_mod.BOQCalculator()
    results: list[dict] = []
    drift: list[dict] = []
    for i, c in enumerate(cases):
        params = c["params"]
        try:
            r_head = head_calc.calculate(dict(params))
        except Exception as exc:  # noqa: BLE001
            r_head = {"__exception__": f"{type(exc).__name__}: {exc}"}
        try:
            r_wt = wt_calc.calculate(dict(params))
        except Exception as exc:  # noqa: BLE001
            r_wt = {"__exception__": f"{type(exc).__name__}: {exc}"}
        entry = {
            "i": i,
            "section": c["section"],
            "params": params,
            "result": r_head,              # 黄金基线 = git HEAD 版本
            "result_worktree": r_wt,       # 在途对照
        }
        results.append(entry)
        d = _diff_fields(r_head, r_wt)
        if d:
            drift.append({"i": i, "section": c["section"], "params": params, "diffs": d})
    return results, drift


# ── DB 快照 ─────────────────────────────────────────────────────
def db_snapshot() -> dict:
    import sqlalchemy as sa
    eng = sa.create_engine(DB_URL)
    snap: dict = {"url": DB_URL.replace("youding:youding", "***:***")}
    with eng.connect() as c:
        snap["server_version"] = c.execute(sa.text("show server_version")).scalar()
        snap["alembic_version"] = [tuple(r) for r in c.execute(sa.text("select * from alembic_version"))]
        snap["alembic_heads_count"] = len(snap["alembic_version"])
        snap["public_table_count"] = c.execute(sa.text(
            "select count(*) from information_schema.tables "
            "where table_schema='public' and table_type='BASE TABLE'"
        )).scalar()
        snap["industry_profiles_row_count"] = c.execute(sa.text(
            "select count(*) from industry_profiles"
        )).scalar()
        snap["industry_profiles_rows"] = [
            {"code": r[0], "version": r[1], "status": r[2]}
            for r in c.execute(sa.text(
                "select code, version, status from industry_profiles order by code, version"
            ))
        ]
        bm = c.execute(sa.text(
            "select boq_rules from industry_profiles "
            "where code='building_materials' order by version desc limit 1"
        )).scalar()
        snap["building_materials_boq_rules_keys"] = (
            sorted(bm.keys()) if isinstance(bm, dict) else None
        )
        snap["building_materials_boq_rules"] = bm
    return snap


def run_existing_tests() -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_industry_profile.py", "-q"],
        cwd=str(BACKEND_ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600,
    )
    return proc.stdout + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr.strip() else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()

    before = snapshot_code_state()
    head_mod, head_sha = load_head_calculator()
    wt_mod = load_worktree_calculator()

    head_has_profile = "industry_profile" in inspect.signature(
        head_mod.BOQCalculator.calculate
    ).parameters
    wt_has_profile = "industry_profile" in inspect.signature(
        wt_mod.BOQCalculator.calculate
    ).parameters

    cases, sampling = build_cases()
    results, drift = run_matrix(head_mod, wt_mod, cases)

    after = snapshot_code_state()

    # 判定可信度：git head/status/文件 md5 前后一致
    reliable = (
        before["git_head"] == after["git_head"]
        and before["git_status"] == after["git_status"]
        and before["files"] == after["files"]
    )

    tests_out = "" if args.skip_tests else run_existing_tests()

    final = snapshot_code_state()
    reliable = reliable and (
        after["git_head"] == final["git_head"]
        and after["files"] == final["files"]
    )

    doc = {
        "captured_at": _utcnow_iso(),
        "purpose": "模块2 Industry Profile 去行业化 —— HS-1 零漂移黄金基线",
        "baseline_semantics": (
            "result 字段 = git HEAD 已提交版本 boq_calculator.py 的输出（真正的改动前基线）；"
            "result_worktree 字段 = 采集时刻工作区版本输出（可能已在途改动，仅作对照）"
        ),
        "git_head_before": before["git_head"],
        "git_status_before": before["git_status"],
        "git_head_after": final["git_head"],
        "git_status_after": final["git_status"],
        "file_hashes_before": before["files"],
        "file_hashes_after": final["files"],
        "reliable": reliable,
        "head_calculator_has_industry_profile_param": head_has_profile,
        "worktree_calculator_has_industry_profile_param": wt_has_profile,
        "baseline_source": f"git HEAD {head_sha} : backend/app/services/boq_calculator.py",
        "sampling": sampling,
        "calculator_cases": results,
        "head_vs_worktree_drift": {
            "drift_case_count": len(drift),
            "drift_cases": drift,
        },
        "pipeline_constants": dump_constants(head_mod, wt_mod),
        "db_snapshot": db_snapshot(),
        "existing_test_output": tests_out,
    }

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "out": str(out_path),
        "reliable": reliable,
        "git_head_before": before["git_head"],
        "git_head_after": final["git_head"],
        "status_identical": before["git_status"] == final["git_status"],
        "files_identical": before["files"] == final["files"],
        "head_has_profile_param": head_has_profile,
        "worktree_has_profile_param": wt_has_profile,
        "total_cases": sampling["total_cases"],
        "head_vs_worktree_drift_cases": len(drift),
        "seed": sampling["seed"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
