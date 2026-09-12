#!/usr/bin/env python3
"""功能模块进度 — 黑色块进度条（█ 已完成 ░ 未完成）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_JSON = ROOT / "docs" / "module-progress.json"
BACKLOG = ROOT / "docs" / "dev-backlog-sprint.json"
SNAPSHOT = ROOT / "docs" / "module-progress-latest.txt"
ADMIN_JSON = ROOT / "frontend" / "admin" / "src" / "data" / "module-progress.json"


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def black_bar(done: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "░" * width
    filled = min(width, max(0, round(width * done / total)))
    return "█" * filled + "░" * (width - filled)


def sprint_from_backlog() -> tuple[int, int]:
    if not BACKLOG.is_file():
        return 0, 0
    data = json.loads(BACKLOG.read_text(encoding="utf-8"))
    tasks = data.get("tasks", [])
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    return done, total


def render(data: dict) -> str:
    sp = data.get("sprint_scheduled", {})
    sd, st = sprint_from_backlog()
    if sd and st:
        sp = {**sp, "done": sd, "total": st}

    modules = data.get("modules", [])
    mod_done = sum(m.get("done", 0) for m in modules)
    mod_total = sum(m.get("total", 0) for m in modules)
    mod_pct = 100 * mod_done / mod_total if mod_total else 0

    lines = [
        "",
        "=== 进度总览（黑色条：█ 已完成  ░ 未完成）===",
        "",
        f"【排期研发】{sp.get('label', 'Sprint')}",
        f"  {black_bar(sp['done'], sp['total'])}  {sp['done']}/{sp['total']} ({100*sp['done']/sp['total']:.0f}%)" if sp.get("total") else "  (无数据)",
        f"  未完成 {max(0, sp.get('total', 0) - sp.get('done', 0))} 项" if sp.get("total") else "",
        "",
        f"【产品功能模块】合计权重 {mod_done}/{mod_total} ({mod_pct:.0f}%)",
        f"  {black_bar(mod_done, mod_total)}",
        f"  还差约 {mod_total - mod_done} 个权重点（共 {len(modules)} 个模块）",
        "",
        "—— 各功能模块 ——",
    ]

    for m in modules:
        d, t = m.get("done", 0), m.get("total", 10)
        pct = 100 * d / t if t else 0
        remain = t - d
        gap = m.get("gap", "")
        lines.append(f"{m['name']}")
        lines.append(f"  {black_bar(d, t)}  {d}/{t} ({pct:.0f}%)  还差 {remain}")
        if gap:
            lines.append(f"  └ {gap}")

    swarm = data.get("swarm_squads") or {}
    squads = swarm.get("squads") or []
    if squads:
        lines.append("")
        lines.append(f"【蜂群小队】{swarm.get('label', '并行开发')}")
        if swarm.get("sprint_id"):
            lines.append(f"  Sprint: {swarm['sprint_id']} · 更新 {swarm.get('updated_at', '—')}")
        total_tasks = 0
        done_tasks = 0
        for sq in squads:
            tasks = sq.get("tasks") or []
            if tasks:
                t_total = len(tasks)
                t_done = sum(1 for x in tasks if x.get("status") == "done")
            else:
                t_total = sq.get("total", 0)
                t_done = sq.get("done", 0)
            total_tasks += t_total
            done_tasks += t_done
            remain = t_total - t_done
            pct = 100 * t_done / t_total if t_total else 0
            owner = sq.get("owner", "")
            prefix = f"[{owner}] " if owner else ""
            lines.append(f"{prefix}{sq.get('name', sq.get('id', '?'))}")
            lines.append(
                f"  {black_bar(t_done, t_total)}  {t_done}/{t_total} ({pct:.0f}%)  未完成 {remain} 项"
            )
            if tasks:
                pending = [x["title"] for x in tasks if x.get("status") != "done"]
                for title in pending:
                    lines.append(f"    ○ {title}")
        swarm_remain = total_tasks - done_tasks
        lines.append(
            f"  合计 {black_bar(done_tasks, total_tasks)}  {done_tasks}/{total_tasks}  未完成 {swarm_remain} 项"
        )

    blockers = data.get("pm_blockers", [])
    if blockers:
        lines.append("")
        lines.append("【PM 阻塞（不计入条但影响商用）】")
        for b in blockers:
            lines.append(f"  ○ {b}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    _configure_stdout()
    if not MODULE_JSON.is_file():
        print(f"ERROR: missing {MODULE_JSON}", file=sys.stderr)
        return 1
    data = json.loads(MODULE_JSON.read_text(encoding="utf-8"))
    text = render(data)
    print(text)
    SNAPSHOT.write_text(text, encoding="utf-8")
    ADMIN_JSON.parent.mkdir(parents=True, exist_ok=True)
    ADMIN_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
