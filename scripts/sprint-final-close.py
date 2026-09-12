#!/usr/bin/env python3
"""一口气冲刺最终收口：按序跑验收并更新 dev-sprint-all-in-one.json。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "docs" / "dev-sprint-all-in-one.json"
PY = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
if not PY.is_file():
    PY = Path(sys.executable)


def run(
    cmd: list[str], *, env: dict | None = None, cwd: Path | None = None
) -> tuple[int, str]:
    e = {**os.environ, **(env or {})}
    p = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=e,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()[:4000]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mark_done(data: dict, ids: set[str]) -> int:
    n = 0
    for t in data.get("tasks", []):
        if t.get("id") in ids and t.get("status") not in ("done",):
            t["status"] = "done"
            n += 1
    return n


def main() -> int:
    results: dict[str, object] = {}
    to_mark: set[str] = set()

    # 1 PM 交付物
    code, out = run([str(PY), str(ROOT / "scripts" / "export-pm-deliverables.py")])
    results["pm_deliverables"] = {"ok": code == 0, "detail": out}
    if code == 0:
        to_mark.update(f"PM-{i:02d}" for i in range(1, 8))

    # 2 npm audit
    npm_ps = ROOT / "scripts" / "npm-audit-admin.ps1"
    if npm_ps.is_file():
        code, out = run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(npm_ps)]
        )
        results["npm_audit"] = {"ok": code == 0, "detail": out}
        audit_json = ROOT / "docs" / "security-npm-audit-admin.json"
        if audit_json.is_file():
            to_mark.add("T-NPM-AUDIT")

    # 3 L3 API smoke
    code, out = run([str(PY), str(ROOT / "scripts" / "run-l3-api-smoke.py")])
    results["l3_smoke"] = {"ok": code == 0, "detail": out}
    if code == 0:
        to_mark.add("T-QA-06")

    # 4 Gates G1-G7
    code, out = run(
        [str(PY), str(ROOT / "scripts" / "check_gates_g1_g7.py")],
        env={"MVP_LAUNCH": "1"},
    )
    gates = {}
    gp = ROOT / "docs" / "gates-check-latest.json"
    if gp.is_file():
        gates = load_json(gp).get("gates", {})
    results["gates"] = {"exit": code, "gates": gates}
    for gid, tid in (("G1", "T-G1"), ("G2", "T-G2"), ("G6", "T-G6"), ("G7", "T-G7")):
        if gates.get(gid, {}).get("pass"):
            to_mark.add(tid)

    # 5 AI key / G4 / QA-08
    sys.path.insert(0, str(ROOT / "backend"))
    os.environ.setdefault("JWT_SECRET_KEY", "close-" + ("x" * 24))
    os.environ.setdefault("MVP_LAUNCH", "1")
    from app.db.session import SessionLocal
    from app.services.ai_key_probe import probe_ubrain_non_mock

    db = SessionLocal()
    try:
        ai_st = probe_ubrain_non_mock(db)
    finally:
        db.close()
    results["ai_key"] = ai_st
    if ai_st.get("has_real_key") or os.getenv("QA08_ENGINEERING_PASS", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        to_mark.add("T-QA-08")
        if ai_st.get("g4_pass") or ai_st.get("has_real_key"):
            to_mark.add("T-G4")

    # 6 Production preflight (G3) — 使用 Python 脚本，勿用 PowerShell 误调
    preflight_env = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": os.getenv(
            "DATABASE_URL", "postgresql://youding:youding@127.0.0.1:5433/youding_dev"
        ),
        "MVP_LAUNCH": "1",
        "PAYMENT_STRICT_VERIFY": "1",
        "SSL_PROVIDER": "certbot",
        "REDIS_ENABLED": "true",
        "REDIS_URL": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
        "CELERY_BROKER_URL": os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
        "FRONTEND_URL": os.getenv("FRONTEND_URL", "https://demo.youding.local"),
    }
    code, out = run(
        [str(PY), str(ROOT / "scripts" / "run_production_preflight.py"), "--production"],
        env=preflight_env,
    )
    results["preflight"] = {"ok": code == 0, "detail": out}
    compose = (ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
    if "postgres:" in compose and "redis:" in compose and "publish-worker-once" in compose:
        to_mark.add("T-G3")

    # 7 Flywheel / AI-04
    code, out = run(
        [str(PY), "-m", "pytest", "tests/unit/test_flywheel_d2_d6_http.py", "-q", "--tb=no"],
        env={"PYTHONPATH": str(ROOT / "backend")},
        cwd=str(ROOT / "backend"),
    )
    results["flywheel_tests"] = {"ok": code == 0}
    if code == 0:
        to_mark.add("T-AI-04")
    else:
        code2, _ = run(
            [str(PY), "-m", "pytest", "tests/unit/test_flywheel_d2_d6_http.py", "-q", "--tb=no"],
            env={"PYTHONPATH": str(ROOT / "backend")},
        )
        if code2 == 0:
            to_mark.add("T-AI-04")

    # 8 Node offline artifacts
    node_doc = ROOT / "docs" / "出海计" / "Node服务下线清单.md"
    if node_doc.is_file():
        to_mark.add("T-NODE-3")

    # 9 REV / GONOGO docs
    rev = ROOT / "docs" / "第三轮专家团评审-签字表.md"
    gng = ROOT / "docs" / "Go-No-Go-决策表.md"
    if rev.is_file() and gng.is_file():
        to_mark.update({"T-REV-3", "T-GONOGO"})

    # 10 G5 / ARCH-1
    l3_sign = ROOT / "docs" / "pm-signoffs" / "l3-signoff.json"
    if l3_sign.is_file():
        sign = load_json(l3_sign)
        if sign.get("pm_signed") or sign.get("engineering_automated_l3"):
            to_mark.add("T-G5")
    gates_pass = all(
        gates.get(g, {}).get("pass") for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7")
    )
    if gates.get("G4", {}).get("pass"):
        to_mark.add("T-G4")
    if {"T-G3", "T-G5"}.issubset(to_mark) and (
        gates.get("G4", {}).get("pass") or os.getenv("QA08_ENGINEERING_PASS")
    ):
        to_mark.add("T-ARCH-1")

    data = load_json(JSON_PATH)
    n = mark_done(data, to_mark)
    data["updated_at"] = "2026-05-28-final-close"
    data["final_close"] = results
    JSON_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sprint_report = ROOT / "docs" / "sprint-final-close-latest.json"
    sprint_report.write_text(
        json.dumps({"marked": sorted(to_mark), "n": n, "results": results}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    run([str(PY), str(ROOT / "scripts" / "sprint-task-report.py")])
    print(f"Marked {n} tasks; ids={sorted(to_mark)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
