# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""挣钱项目看板 — 从大赛轮次、专家归因收入、L4 审核历史聚合，禁止写死假数。"""

from __future__ import annotations

from typing import Any


def _attach_employee_lessons(
    employees: list[dict[str, Any]],
    *,
    extra_role_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """_attach_employee_lessons。

    参数说明：
    :param employees: 参数 employees
    :param extra_role_ids: 参数 extra_role_ids
    :return: 返回处理结果。
    """
    from app.services.hermes.greedy_contest_memory_service import get_role_memory
    seen: set[str] = set()
    order: list[str] = []
    for emp in employees:
        rid = str(emp.get("role_id") or "")
        if rid and rid not in seen:
            seen.add(rid)
            order.append(rid)
    for rid in extra_role_ids or []:
        rid = str(rid or "").strip()
        if rid and rid not in seen:
            seen.add(rid)
            order.append(rid)

    lesson_by_role: dict[str, list[str]] = {}
    for rid in order:
        try:
            mem = get_role_memory(rid)
            lesson_by_role[rid] = [str(x) for x in (mem.get("lessons") or []) if x][:5]
        except Exception:
            lesson_by_role[rid] = []

    out: list[dict[str, Any]] = []
    for emp in employees:
        rid = str(emp.get("role_id") or "")
        lessons = lesson_by_role.get(rid) or []
        row = dict(emp)
        row["lessons"] = lessons
        row["latest_lesson"] = lessons[0] if lessons else None
        out.append(row)
    return out


def _build_lessons_digest(
    employees: list[dict[str, Any]],
    *,
    leaderboard_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """_build_lessons_digest。

    参数说明：
    :param employees: 参数 employees
    :param leaderboard_rows: 参数 leaderboard_rows
    :return: 返回处理结果。
    """
    from app.services.hermes.greedy_contest_memory_service import get_mojin_memory, get_role_memory
    mojin = get_mojin_memory()
    mojin_lessons = [str(x) for x in (mojin.get("lessons") or []) if x][:8]
    by_employee: list[dict[str, Any]] = []
    for emp in employees[:8]:
        lessons = list(emp.get("lessons") or [])
        if not lessons:
            continue
        by_employee.append(
            {
                "role_id": emp.get("role_id"),
                "name": emp.get("name"),
                "emoji": emp.get("emoji"),
                "lessons": lessons[:3],
                "latest_lesson": lessons[0],
            }
        )

    # 补充：有心得但未进贡献榜的专家（按 lessons_count / 擂台分）
    contrib_ids = {str(e.get("role_id")) for e in employees}
    extras: list[dict[str, Any]] = []
    for row in sorted(
        leaderboard_rows,
        key=lambda x: (-int(x.get("lessons_count") or 0), -int(x.get("score_arena") or 0)),
    ):
        rid = str(row.get("role_id") or "")
        if not rid or rid in contrib_ids:
            continue
        if int(row.get("lessons_count") or 0) <= 0:
            continue
        try:
            mem = get_role_memory(rid)
            lessons = [str(x) for x in (mem.get("lessons") or []) if x][:3]
        except Exception:
            lessons = []
        if not lessons:
            continue
        extras.append(
            {
                "role_id": rid,
                "name": row.get("name") or rid.split("/")[-1],
                "emoji": row.get("emoji"),
                "lessons": lessons,
                "latest_lesson": lessons[0],
            }
        )
        if len(extras) >= 4:
            break

    combined: list[str] = []
    seen_text: set[str] = set()
    for block in [mojin_lessons] + [e.get("lessons") or [] for e in by_employee] + [e.get("lessons") or [] for e in extras]:
        for text in block:
            t = str(text).strip()
            if not t or t in seen_text:
                continue
            seen_text.add(t)
            combined.append(t)
            if len(combined) >= 10:
                break
        if len(combined) >= 10:
            break

    return {
        "mojin_lessons": mojin_lessons,
        "by_employee": by_employee,
        "extra_voices": extras,
        "highlights": combined,
        "loops_completed": int(mojin.get("loops_completed") or 0),
    }


def _build_evolution_directions(
    *,
    projects: list[dict[str, Any]],
    employees: list[dict[str, Any]],
    lessons_digest: dict[str, Any],
    summary: dict[str, Any],
    rounds: list[dict[str, Any]],
) -> dict[str, Any]:
    """_build_evolution_directions。

    参数说明：
    :param projects: 参数 projects
    :param employees: 参数 employees
    :param lessons_digest: 参数 lessons_digest
    :param summary: 参数 summary
    :param rounds: 参数 rounds
    :return: 返回处理结果。
    """
    directions: list[dict[str, Any]] = []
    rounds_n = int(summary.get("rounds_tracked") or 0)
    highlights: list[str] = list(lessons_digest.get("highlights") or [])
    if rounds_n <= 0 and not highlights:
        return {
            "headline": "先跑闭环，再谈进化",
            "directions": [
                {
                    "priority": "P0",
                    "theme": "启动首轮搞钱闭环",
                    "action": "在摸金总控执行「跑一轮闭环」，让 AI 员工留下部署记录与 lessons",
                    "signals": ["rounds_tracked=0", "lessons=0"],
                }
            ],
            "next_loop_hints": [
                "优先选 L3/L4 可交付 SKU（互动 demo / 矩阵帖）",
                "闭环结束后回到本页刷新看板",
            ],
            "data_source": "contest_memory",
        }

    directions, low_completion, mojin_lessons = _accumulate_evolution_directions(
        projects, employees, lessons_digest, summary, highlights,
    )
    directions.sort(key=lambda d: (0 if d.get("priority") == "P0" else 1 if d.get("priority") == "P1" else 2))
    headline = "下一轮进化：复制有效 SKU + 专家心得"
    if low_completion:
        headline = "下一轮进化：先补完成率，再放大收入"
    elif not projects and highlights:
        headline = "下一轮进化：按已沉淀心得优化编排"

    hints: list[str] = []
    if projects:
        hints.append(f"优先 SKU：{projects[0].get('label')}")
    if employees:
        hints.append(f"默认专家：{employees[0].get('name')}")
    if mojin_lessons:
        hints.append(f"摸金备忘：{str(mojin_lessons[0])[:80]}")
    if not hints:
        hints.append("跑完闭环后刷新本页，进化方向会自动更新")

    return {
        "headline": headline,
        "directions": directions[:6],
        "next_loop_hints": hints[:4],
        "data_source": "contest_memory",
    }


def get_project_earnings_board(*, leaderboard_limit: int = 80) -> dict[str, Any]:
    """get_project_earnings_board。

    参数说明：
    :param leaderboard_limit: 参数 leaderboard_limit
    :return: 返回处理结果。
    """
    from app.services.hermes.greedy_contest_memory_service import get_contest_leaderboard
    from app.services.hermes.greedy_publish_queue_service import get_publish_review_history
    from app.services.hermes.role_economics_service import list_publish_sku_catalog
    lb = get_contest_leaderboard(limit=max(10, min(leaderboard_limit, 100)))
    rows_by_id = {str(r.get("role_id")): r for r in (lb.get("leaderboard") or []) if r.get("role_id")}
    catalog = list_publish_sku_catalog()
    rounds = list(lb.get("recent_rounds") or [])
    history = get_publish_review_history(limit=50)
    sku_stats: dict[str, dict[str, Any]] = {}
    sku_stats = _aggregate_sku_stats(rounds, rows_by_id)
    review_stats = _aggregate_review_stats(history)
    projects = _build_project_rows(sku_stats, catalog, review_stats)
    top_employees = _build_top_employees(lb, rounds)
    top_employees = _attach_employee_lessons(top_employees)
    lessons_digest = _build_lessons_digest(top_employees, leaderboard_rows=list(lb.get("leaderboard") or []))
    completions = [float(p["completion_pct"]) for p in projects if p.get("completion_pct") is not None]
    total_rev = sum(int(p.get("revenue_cny_minor") or 0) for p in projects)
    summary = {
        "total_revenue_cny_minor": total_rev,
        "avg_completion_pct": round(sum(completions) / len(completions), 1) if completions else None,
        "active_project_count": len(projects),
        "rounds_tracked": len(rounds),
    }
    evolution = _build_evolution_directions(
        projects=projects,
        employees=top_employees,
        lessons_digest=lessons_digest,
        summary=summary,
        rounds=rounds,
    )
    return {
        "projects": projects,
        "top_employees": top_employees,
        "lessons_digest": lessons_digest,
        "evolution": evolution,
        "summary": summary,
        "data_source": "contest_memory",
    }

def _aggregate_sku_stats(
    rounds: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """_aggregate_sku_stats。

    参数说明：
    :return: 返回 sku_stats 聚合结果。
    """
    sku_stats: dict[str, dict[str, Any]] = {}
    for rnd in rounds:
        if not isinstance(rnd, dict):
            continue
        kpi = rnd.get("kpi_pct")
        participants = [str(x) for x in (rnd.get("participants") or []) if x]
        skus = [str(x) for x in (rnd.get("skus") or []) if x]
        for sku in skus:
            st = sku_stats.setdefault(
                sku,
                {"rounds": 0, "kpi_sum": 0.0, "kpi_count": 0, "participants": set(), "revenue_minor": 0},
            )
            st["rounds"] += 1
            if kpi is not None:
                try:
                    st["kpi_sum"] += float(kpi)
                    st["kpi_count"] += 1
                except (TypeError, ValueError):
                    pass
            st["participants"].update(participants)

        if not skus or not participants:
            continue
        round_rev = sum(int((rows_by_id.get(rid) or {}).get("revenue_attributed_cny_minor") or 0) for rid in participants)
        if round_rev <= 0:
            continue
        share = round_rev // len(skus)
        for sku in skus:
            if sku in sku_stats:
                sku_stats[sku]["revenue_minor"] += share
    return sku_stats


def _aggregate_review_stats(
    history: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """_aggregate_review_stats。

    参数说明：
    :return: 返回 review_stats 聚合结果。
    """
    review_stats: dict[str, dict[str, int]] = {}
    for item in history:
        if not isinstance(item, dict):
            continue
        sku = str(item.get("sku") or "").strip()
        if not sku:
            continue
        rs = review_stats.setdefault(sku, {"approved": 0, "rejected": 0})
        action = str(item.get("action") or "")
        if action == "approve":
            rs["approved"] += 1
        elif action == "reject":
            rs["rejected"] += 1
    return review_stats


def _build_project_rows(
    sku_stats: dict[str, dict[str, Any]],
    catalog: dict[str, Any],
    review_stats: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """_build_project_rows。

    参数说明：
    :return: 返回 projects 列表。
    """
    projects: list[dict[str, Any]] = []
    for sku, st in sku_stats.items():
        meta = catalog.get(sku) or {}
        rev = int(st.get("revenue_minor") or 0)
        rounds_n = int(st.get("rounds") or 0)
        if rounds_n <= 0 and rev <= 0:
            continue

        kpi_count = int(st.get("kpi_count") or 0)
        completion_from_kpi = round(st["kpi_sum"] / kpi_count, 1) if kpi_count else None
        rs = review_stats.get(sku, {})
        review_total = int(rs.get("approved") or 0) + int(rs.get("rejected") or 0)
        completion_from_review = (
            round(100.0 * rs["approved"] / review_total, 1) if review_total > 0 else None
        )
        if completion_from_review is not None:
            completion_pct = completion_from_review
            completion_source = "publish_review"
        elif completion_from_kpi is not None:
            completion_pct = completion_from_kpi
            completion_source = "loop_kpi"
        else:
            completion_pct = None
            completion_source = None

        projects.append(
            {
                "sku": sku,
                "label": meta.get("label") or sku,
                "revenue_cny_minor": rev,
                "rounds": rounds_n,
                "participant_count": len(st.get("participants") or []),
                "completion_pct": completion_pct,
                "completion_source": completion_source,
                "primary_roles": list(meta.get("primary_roles") or []),
            }
        )

    projects.sort(key=lambda x: (-int(x.get("revenue_cny_minor") or 0), -int(x.get("rounds") or 0)))
    return projects


def _build_top_employees(
    lb: dict[str, Any],
    rounds: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """_build_top_employees。

    参数说明：
    :return: 返回 top_employees 列表（已排序并截断）。
    """
    top_employees: list[dict[str, Any]] = []
    for r in lb.get("leaderboard") or []:
        rid = str(r.get("role_id") or "")
        if not rid:
            continue
        rev = int(r.get("revenue_attributed_cny_minor") or 0)
        deployments = int(r.get("deployments") or 0)
        if rev <= 0 and deployments <= 0:
            continue
        proj_skus: set[str] = set()
        for rnd in rounds:
            if rid in [str(x) for x in (rnd.get("participants") or [])]:
                proj_skus.update(str(x) for x in (rnd.get("skus") or []) if x)
        top_employees.append(
            {
                "role_id": rid,
                "name": r.get("name") or rid.split("/")[-1],
                "emoji": r.get("emoji"),
                "revenue_cny_minor": rev,
                "deployments": deployments,
                "project_count": len(proj_skus),
                "project_skus": list(proj_skus)[:6],
                "contest_tier": r.get("contest_tier"),
            }
        )
    top_employees.sort(key=lambda x: (-int(x.get("revenue_cny_minor") or 0), -int(x.get("deployments") or 0)))
    top_employees = top_employees[:10]
    return top_employees


def _accumulate_evolution_directions(
    projects: list[dict[str, Any]],
    employees: list[dict[str, Any]],
    lessons_digest: dict[str, Any],
    summary: dict[str, Any],
    highlights: list[str],
) -> tuple[list[dict[str, Any]], list[Any], list[Any]]:
    """_accumulate_evolution_directions。

    参数说明：
    :return: 返回 (directions, low_completion, mojin_lessons)。
    """
    low_completion = [
        p for p in projects if p.get("completion_pct") is not None and float(p["completion_pct"]) < 50
    ]
    if low_completion:
        labels = "、".join(str(p.get("label") or p.get("sku")) for p in low_completion[:3])
        directions.append(
            {
                "priority": "P0",
                "theme": "补齐低完成率项目",
                "action": f"下一轮优先优化：{labels}（L4 审核或闭环 KPI 未达标）",
                "signals": [f"completion<{p.get('completion_pct')}% @ {p.get('sku')}" for p in low_completion[:3]],
            }
        )

    if projects:
        top = projects[0]
        directions.append(
            {
                "priority": "P1",
                "theme": "放大已验证 SKU",
                "action": f"继续押注「{top.get('label')}」— 当前归因 {top.get('revenue_cny_minor', 0) / 100:.2f} 元 / {top.get('rounds')} 轮",
                "signals": [f"sku={top.get('sku')}", f"rounds={top.get('rounds')}"],
            }
        )

    if employees:
        lead = employees[0]
        lesson = lead.get("latest_lesson")
        if lesson:
            directions.append(
                {
                    "priority": "P1",
                    "theme": "复制 Top 专家打法",
                    "action": f"让 {lead.get('name')} 带队下一循环：{str(lesson)[:120]}",
                    "signals": [f"role={lead.get('role_id')}", "latest_lesson"],
                }
            )
        elif int(lead.get("deployments") or 0) > 0:
            directions.append(
                {
                    "priority": "P2",
                    "theme": "固化高部署专家编排",
                    "action": f"下一循环默认纳入 {lead.get('name')}（部署 {lead.get('deployments')} 次）",
                    "signals": [f"deployments={lead.get('deployments')}"],
                }
            )

    mojin_lessons = list(lessons_digest.get("mojin_lessons") or [])
    if mojin_lessons:
        directions.append(
            {
                "priority": "P1",
                "theme": "摸金校尉全局心得",
                "action": str(mojin_lessons[0])[:160],
                "signals": ["mojin_lesson"],
            }
        )

    avg = summary.get("avg_completion_pct")
    if avg is not None and float(avg) >= 80 and projects:
        directions.append(
            {
                "priority": "P2",
                "theme": "扩 SKU 矩阵",
                "action": "平均完成率已高，下一轮可并行 2–3 个 deliverable SKU 做 A/B",
                "signals": [f"avg_completion={avg}%"],
            }
        )

    if not directions and highlights:
        directions.append(
            {
                "priority": "P1",
                "theme": "按心得微调编排",
                "action": highlights[0][:160],
                "signals": ["lessons_highlight"],
            }
        )
    return directions, low_completion, mojin_lessons

