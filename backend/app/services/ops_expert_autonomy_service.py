# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""专家自治：自动修补（小事）+ 站会总结 + 通知 Owner（大事）。"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("uj-admin.ops_expert_autonomy")

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    env = os.getenv("YOUDING_REPO_ROOT", "").strip()
    if env:
        return Path(env)
    return _REPO_ROOT


def _read_json(path: Path) -> dict[str, Any] | None:
    """_read_json。

    参数说明：
    :param path: 参数 path
    :return: 返回处理结果。
    """
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8-sig")
        return json.loads(raw)
    except Exception:
        return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """_write_json。

    参数说明：
    :param path: 参数 path
    :param data: 参数 data
    :return: 返回处理结果。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _webhook_url() -> str:
    """_webhook_url。
    :return: 返回处理结果。
    """
    for key in (
        "FEISHU_WEBHOOK_URL",
        "HERMES_ALERT_WEBHOOK_URL",
        "OPS_READINESS_WEBHOOK_URL",
    ):
        val = os.getenv(key, "").strip()
        if val:
            return val
    try:
        from app.core.config import settings
        return (
            (settings.FEISHU_WEBHOOK_URL or "").strip()
            or (settings.HERMES_ALERT_WEBHOOK_URL or "").strip()
            or (getattr(settings, "OPS_READINESS_WEBHOOK_URL", None) or "")
        )
    except Exception:
        return ""


def _http_probe(url: str) -> bool:
    """_http_probe。

    参数说明：
    :param url: 参数 url
    :return: 返回处理结果。
    """
    try:
        with httpx.Client(timeout=6.0) as client:
            r = client.get(url)
            return r.status_code == 200
    except Exception:
        return False


def _run_powershell(script_rel: str, *args: str) -> dict[str, Any]:
    """_run_powershell。

    参数说明：
    :param script_rel: 参数 script_rel
    :param *args: 参数 *args
    :return: 返回处理结果。
    """
    root = _repo_root()
    script = root / script_rel.replace("/", os.sep)
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return {
            "ok": proc.returncode == 0,
            "exit": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-400:],
            "stderr_tail": (proc.stderr or "")[-200:],
        }
    except Exception as exc:
        return {"ok": False, "exit": -1, "error": str(exc)[:200]}


def _sync_sre_lane_after_remediate(daily: dict[str, Any], health: dict[str, Any]) -> dict[str, Any]:
    """探针双绿后，将 expert-daily 中 SRE Lane 与 daily-health 对齐（诚实，非假绿）。"""
    if not health.get("ok"):
        return daily
    lanes = daily.get("lanes")
    if not isinstance(lanes, list):
        return daily
    changed = False
    for row in lanes:
        if not isinstance(row, dict) or row.get("id") != "sre":
            continue
        if row.get("ok"):
            continue
        row["ok"] = True
        row["exit"] = 0
        row["report_snapshot"] = health
        changed = True
    if not changed:
        return daily
    daily = dict(daily)
    daily["lanes"] = lanes
    daily["pass_count"] = sum(1 for r in lanes if isinstance(r, dict) and r.get("ok"))
    daily["lane_count"] = len(lanes)
    daily["fail_count"] = sum(1 for r in lanes if isinstance(r, dict) and not r.get("ok"))
    daily["ok"] = daily["fail_count"] == 0
    return daily


def auto_remediate(*, daily: dict[str, Any] | None = None) -> dict[str, Any]:
    """小事自动修：目前以 SRE 拉起 dev 栈为主。"""
    root = _repo_root()
    daily = daily or _read_json(root / "docs/ops/expert-daily-latest.json") or {}
    charter = _read_json(root / ".project/expert-autonomy-charter.json") or {}
    actions: list[dict[str, Any]] = []
    lanes = daily.get("lanes") or []
    sre_fail = any(
        isinstance(row, dict) and row.get("id") == "sre" and not row.get("ok")
        for row in lanes
    )
    health = _read_json(root / "docs/ops/daily-health-latest.json") or {}
    health_bad = not health.get("ok", True)
    if sre_fail or health_bad:
        r1 = _run_powershell("scripts/ops-daily-health.ps1", "-AutoStart")
        actions.append({"action": "ops-daily-health-autostart", **r1})
        if not r1.get("ok"):
            r2 = _run_powershell("scripts/launch-dev-admin-safe.ps1")
            actions.append({"action": "launch-dev-admin-safe", **r2})

    after_health = _http_probe("http://127.0.0.1:8001/api/v1/health")
    after_admin = _http_probe("http://127.0.0.1:5173/login")
    auto_fixed = bool(actions) and after_health and after_admin
    if auto_fixed and sre_fail:
        health = _read_json(root / "docs/ops/daily-health-latest.json") or health
        daily = _sync_sre_lane_after_remediate(daily, health)
        _write_json(root / "docs/ops/expert-daily-latest.json", daily)

    out = {
        "ok": True,
        "personality": charter.get("personality", "diligent"),
        "actions": actions,
        "after_probe": {"backend_health": after_health, "admin_login": after_admin},
        "auto_fixed": auto_fixed,
        "daily_synced": auto_fixed and sre_fail,
    }
    _write_json(root / "docs/ops/expert-auto-remediate-latest.json", out)
    return out


def _local_today_key() -> str:
    """_local_today_key。
    :return: 返回处理结果。
    """
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def _run_honesty_gate() -> dict[str, Any]:
    """_run_honesty_gate。
    :return: 返回处理结果。
    """
    root = _repo_root()
    script = root / "scripts" / "validate-ops-honesty.py"
    if not script.is_file():
        return {"ok": True, "findings": [], "skipped": True}
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "YOUDING_REPO_ROOT": str(root)},
        )
        report = _read_json(root / "docs/ops/ops-honesty-latest.json") or {}
        report["exit_code"] = proc.returncode
        return report
    except Exception as exc:
        return {"ok": False, "findings": [{"id": "honesty_gate_error", "severity": "P0", "message": str(exc)[:200]}]}


def _honesty_preflight(daily: dict[str, Any]) -> list[dict[str, Any]]:
    """Standup 写入前先算诚实冲突，避免假绿。"""
    issues: list[dict[str, Any]] = []
    today = _local_today_key()
    run_kind = daily.get("run_kind") or "unknown"
    if run_kind != "full_roster":
        issues.append(
            {
                "id": "no_full_roster_today",
                "severity": "P1",
                "message": f"今日无 full_roster 扫描（run_kind={run_kind}），不得宣称 7 专家已巡检",
            }
        )
    if daily.get("day") != today:
        issues.append(
            {
                "id": "daily_stale",
                "severity": "P1",
                "message": f"expert-daily-latest 日期={daily.get('day')} 非今日 {today}",
            }
        )
    return issues


def _backlog_from_lanes(daily: dict[str, Any]) -> list[dict[str, Any]]:
    """真实待办：记录但不宣称已修。"""
    items: list[dict[str, Any]] = []
    for row in daily.get("lanes") or []:
        if not isinstance(row, dict):
            continue
        snap = row.get("report_snapshot") or {}
        if row.get("id") == "security_no_fake":
            p1 = int(snap.get("p1_count") or 0)
            p2 = int(snap.get("p2_count") or 0)
            if p1 > 0 or p2 > 0:
                items.append(
                    {
                        "id": "no_fake_backlog",
                        "expert": row.get("expert"),
                        "p1_count": p1,
                        "p2_count": p2,
                        "message": f"假交付扫描 P1={p1} P2={p2}（真实存在，未宣称已修）",
                    }
                )
    return items


def _classify_owner_review(
    daily: dict[str, Any],
    *,
    remediate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """_classify_owner_review。

    参数说明：
    :param daily: 参数 daily
    :param remediate: 参数 remediate
    :return: 返回处理结果。
    """
    items: list[dict[str, Any]] = []
    remediate = remediate or {}
    sre_suppressed = bool(
        remediate.get("auto_fixed")
        and (remediate.get("after_probe") or {}).get("backend_health")
        and (remediate.get("after_probe") or {}).get("admin_login")
    )
    for row in daily.get("lanes") or []:
        if not isinstance(row, dict):
            continue
        if not row.get("ok"):
            if row.get("id") == "sre" and sre_suppressed:
                continue
            items.append(
                {
                    "id": f"lane_fail_{row.get('id')}",
                    "severity": "high",
                    "expert": row.get("expert"),
                    "lane_id": row.get("id"),
                    "focus": row.get("focus"),
                    "message": f"Lane FAIL: {row.get('id')} — {row.get('focus')}",
                }
            )
        snap = row.get("report_snapshot") or {}
        if row.get("id") == "security_no_fake":
            p0 = int(snap.get("p0_count") or 0)
            if p0 > 0:
                items.append(
                    {
                        "id": "no_fake_p0",
                        "severity": "critical",
                        "expert": "Security Engineer",
                        "message": f"假交付 P0={p0}，需 Owner 过目后授权修代码",
                        "p0_count": p0,
                    }
                )
        if row.get("id") == "backend_preflight" and snap.get("ok") is False:
            items.append(
                {
                    "id": "preflight_fail",
                    "severity": "medium",
                    "expert": "DevOps",
                    "message": "生产预检未通过，请 Owner 确认 .env / 部署项",
                }
            )
    return items


def _resolve_standup_metrics(
    daily: dict[str, Any] | None,
    remediate: dict[str, Any] | None,
) -> dict[str, Any]:
    """解析站会基础指标：日期、运行类型、Lane 通过统计。"""
    root = _repo_root()
    daily = daily or _read_json(root / "docs/ops/expert-daily-latest.json") or {}
    remediate = remediate or _read_json(root / "docs/ops/expert-auto-remediate-latest.json") or {}
    day = daily.get("day") or _local_today_key()
    run_kind = daily.get("run_kind") or "unknown"
    roster_today = run_kind == "full_roster" and day == _local_today_key()
    lanes = daily.get("lanes") or []
    pass_count = daily.get("pass_count")
    if pass_count is None and lanes:
        pass_count = sum(1 for r in lanes if isinstance(r, dict) and r.get("ok"))
    lane_count = daily.get("lane_count") or len(lanes)
    daily_ok = daily.get("ok")
    if daily_ok is None and lanes:
        daily_ok = all(isinstance(r, dict) and r.get("ok") for r in lanes)
    return {
        "daily": daily,
        "remediate": remediate,
        "day": day,
        "run_kind": run_kind,
        "roster_today": roster_today,
        "pass_count": pass_count,
        "lane_count": lane_count,
        "daily_ok": daily_ok,
    }


def _collect_owner_review(
    daily: dict[str, Any],
    remediate: dict[str, Any],
) -> list[dict[str, Any]]:
    """合并 Lane 审查项与诚实门禁预检项，生成「请您过目」列表。"""
    owner_review = _classify_owner_review(daily, remediate=remediate)
    for issue in _honesty_preflight(daily):
        owner_review.append(
            {
                "id": issue["id"],
                "severity": "high" if issue["severity"] == "P1" else issue["severity"],
                "expert": "Ops Honesty Gate",
                "message": issue["message"],
            }
        )
    return owner_review


def _build_standup_markdown(
    *,
    day: str,
    run_kind: str,
    roster_today: bool,
    lane_count: int,
    pass_count: int,
    daily_ok: bool,
    auto_actions: list[dict[str, Any]],
    auto_fixed: bool,
    probe: dict[str, Any],
    backlog: list[dict[str, Any]],
    owner_review: list[dict[str, Any]],
) -> str:
    """生成站会 Markdown 全文。"""
    scan_line = (
        f"- 全量 {lane_count} Lane: {'今日已跑' if roster_today else '今日未跑或数据过期'} (run_kind={run_kind}, day={day})"
    )
    if roster_today:
        scan_line += f"\n- Lane 通过: {pass_count}/{lane_count}\n- 扫描结果: {'全绿' if daily_ok else '有 FAIL'}"
    else:
        scan_line += f"\n- 上次 Lane 快照: {pass_count}/{lane_count}（仅供参考，不可当今日结论）"

    lines = [
        f"# 专家每日站会 · {_local_today_key()}",
        "",
        "## 扫描摘要（诚实）",
        scan_line,
        "",
        "## 已自动处理（小事，有探针证据）",
    ]
    if auto_actions:
        for a in auto_actions:
            status = "OK" if a.get("ok") else "FAIL"
            lines.append(f"- [{status}] {a.get('action')}")
        lines.append(f"- 探针: backend={probe.get('backend_health')} admin={probe.get('admin_login')}")
        if auto_fixed:
            lines.append("- 结论: auto_fixed=是（探针双绿）")
        elif auto_actions:
            lines.append("- 结论: auto_fixed=否（未宣称已修好）")
    else:
        lines.append("- 无自动修补动作")

    if backlog:
        lines.extend(["", "## 真实待办（已记录，未宣称已修）"])
        for item in backlog:
            lines.append(f"- {item.get('message')}")

    lines.extend(["", "## 请您过目（大事 / 诚实冲突）"])
    if owner_review:
        for item in owner_review:
            sev = item.get("severity", "high")
            lines.append(f"- **[{sev.upper()}]** {item.get('message')}")
    elif roster_today and daily_ok:
        lines.append("- 无大事。今日全量扫描通过，Owner 可忽略。")
    elif roster_today and auto_fixed and not owner_review:
        lines.append("- 无大事。SRE 已自动拉起且探针双绿，当日 FAIL 已同步修复。")
    else:
        lines.append("- 不得报假绿：今日全量扫描未确认，请等 08:00 任务或手动跑 expert-daily。")

    lines.extend(
        [
            "",
            "## 下一轮",
            "- 08:00 计划任务跑 full_roster（LOCALAPPDATA 启动器，避免中文路径 267011）",
            "- FAIL Lane 优先由对应专家在 Cursor 修代码",
            "",
            f"归档: docs/ops/daily-runs/{day}.json",
            "诚实门禁: docs/ops/ops-honesty-latest.json",
        ]
    )
    return "\n".join(lines)


def _build_standup_notify(
    *,
    roster_today: bool,
    pass_count: int,
    lane_count: int,
    daily_ok: bool,
    auto_fixed: bool,
    owner_review: list[dict[str, Any]],
    backlog: list[dict[str, Any]],
) -> str:
    """生成站会飞书通知文本。"""
    text_notify = (
        f"【优丁专家站会 {_local_today_key()}】\n"
        f"全量扫描: {'今日已跑' if roster_today else '今日未跑/过期'}\n"
    )
    if roster_today:
        text_notify += f"Lane: {pass_count}/{lane_count} {'全绿' if daily_ok else '有FAIL'}\n"
    text_notify += f"自动修(探针证实): {'是' if auto_fixed else '否'}\n"
    text_notify += f"请您过目: {len(owner_review)} 项\n"
    if owner_review:
        for item in owner_review[:5]:
            text_notify += f"· [{item.get('severity')}] {item.get('message')}\n"
    elif roster_today and daily_ok:
        text_notify += "· 无大事。\n"
    elif roster_today and auto_fixed and not owner_review:
        text_notify += "· 无大事（SRE 已自动修复）。\n"
    else:
        text_notify += "· 不得报假绿，全量扫描未确认。\n"
    if backlog:
        text_notify += f"· 待办 backlog: {len(backlog)} 项（真实记录）\n"
    text_notify += "详情: docs/ops/expert-standup-latest.md"
    return text_notify


def _persist_standup(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """写盘站会 JSON/MD 并跑诚实门禁，返回最终 payload。"""
    _write_json(root / "docs/ops/expert-standup-latest.json", payload)
    (root / "docs/ops/expert-standup-latest.md").write_text(payload["markdown"], encoding="utf-8")
    honesty = _run_honesty_gate()
    payload["honesty_gate"] = honesty
    if not honesty.get("ok"):
        payload["needs_owner"] = True
        _write_json(root / "docs/ops/expert-standup-latest.json", payload)
    return payload


def build_standup(*, daily: dict[str, Any] | None = None, remediate: dict[str, Any] | None = None) -> dict[str, Any]:
    """生成专家每日站会：汇总自动修复、真实待办与 Owner 待过目事项。"""
    metrics = _resolve_standup_metrics(daily, remediate)
    daily = metrics["daily"]
    remediate = metrics["remediate"]
    day = metrics["day"]
    run_kind = metrics["run_kind"]
    roster_today = metrics["roster_today"]
    pass_count = metrics["pass_count"]
    lane_count = metrics["lane_count"]
    daily_ok = metrics["daily_ok"]
    owner_review = _collect_owner_review(daily, remediate)
    backlog = _backlog_from_lanes(daily)
    auto_actions = remediate.get("actions") or []
    auto_fixed = remediate.get("auto_fixed") or False
    probe = remediate.get("after_probe") or {}
    md = _build_standup_markdown(
        day=day,
        run_kind=run_kind,
        roster_today=roster_today,
        lane_count=lane_count,
        pass_count=pass_count,
        daily_ok=daily_ok,
        auto_actions=auto_actions,
        auto_fixed=auto_fixed,
        probe=probe,
        backlog=backlog,
        owner_review=owner_review,
    )
    needs_owner = bool(owner_review) or not roster_today
    text_notify = _build_standup_notify(
        roster_today=roster_today,
        pass_count=pass_count,
        lane_count=lane_count,
        daily_ok=daily_ok,
        auto_fixed=auto_fixed,
        owner_review=owner_review,
        backlog=backlog,
    )
    payload = {
        "day": _local_today_key(),
        "roster_day": day,
        "run_kind": run_kind,
        "roster_today": roster_today,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "daily_ok": daily_ok if roster_today else None,
        "pass_count": pass_count,
        "lane_count": lane_count,
        "auto_fixed": auto_fixed,
        "auto_actions": auto_actions,
        "backlog": backlog,
        "owner_review": owner_review,
        "owner_review_count": len(owner_review),
        "needs_owner": needs_owner,
        "markdown": md,
        "notify_text": text_notify,
    }
    return _persist_standup(_repo_root(), payload)


def notify_owner(*, standup: dict[str, Any] | None = None) -> dict[str, Any]:
    """notify_owner。

    参数说明：
    :param standup: 参数 standup
    :return: 返回处理结果。
    """
    standup = standup or _read_json(_repo_root() / "docs/ops/expert-standup-latest.json") or {}
    url = _webhook_url()
    if not url:
        return {"sent": False, "reason": "no_webhook_configured", "standup_day": standup.get("day")}

    text = standup.get("notify_text") or "专家站会：无摘要"
    payload = {"msg_type": "text", "content": {"text": text[:4000]}}
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload)
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        ok = resp.status_code == 200 and (
            data.get("code") in (None, 0) or data.get("StatusCode") == 0 or data.get("ok") is True
        )
        return {"sent": ok, "status_code": resp.status_code, "response": data}
    except Exception as exc:
        logger.warning("expert standup notify failed: %s", exc)
        return {"sent": False, "error": str(exc)[:200]}


def run_full_cycle(*, notify: bool = True) -> dict[str, Any]:
    """run_full_cycle。

    参数说明：
    :param notify: 参数 notify
    :return: 返回处理结果。
    """
    remediate = auto_remediate()
    standup = build_standup(remediate=remediate)
    notification = notify_owner(standup=standup) if notify else {"sent": False, "skipped": True}
    return {"remediate": remediate, "standup": standup, "notification": notification}
