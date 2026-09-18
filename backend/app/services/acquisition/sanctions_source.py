# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-4 真制裁/风险名单源适配层。

来源（按优先级）：
    1. 本地名单文件 SANCTIONS_LIST_PATH（CSV/JSON，可离线审计）
    2. 环境变量 SANCTIONS_LIST_INLINE（JSON 数组，演示/联调）
    3. 远程 URL SANCTIONS_LIST_URL（OFAC/UN/EU 导出物；失败诚实 error）

匹配：公司名/邮箱/域名 子串（大小写不敏感）；命中 → blocked/watch。
原则：未配置任何源 → status=not_configured，绝不假装「已合规」。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


def _load_local_list() -> tuple[list[dict[str, Any]], str]:
    path = (os.getenv("SANCTIONS_LIST_PATH") or "").strip()
    if path and Path(path).exists():
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        items = _parse_list_text(text)
        return items, f"file:{Path(path).name}"
    inline = (os.getenv("SANCTIONS_LIST_INLINE") or "").strip()
    if inline:
        try:
            data = json.loads(inline)
            if isinstance(data, list):
                return [_norm_entry(x) for x in data if x], "env:inline"
        except Exception:
            pass
    # 默认种子：开发用「已知风险特征」样本，明确标注 seed_demo
    seed = [
        {"name": "Sanctioned Demo Trading LLC", "aliases": ["SDT Trading"], "reason": "demo_blocked", "source": "seed_demo"},
        {"name": "Watchlist Example FZE", "aliases": [], "reason": "demo_watch", "source": "seed_demo", "level": "watch"},
        {"email": "blocked-sanction@example-sanctions.test", "reason": "demo_blocked_email", "source": "seed_demo"},
    ]
    return seed, "seed_demo"


def _parse_list_text(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
            return [_norm_entry(x) for x in data if isinstance(x, dict)]
        except Exception:
            return []
    # CSV: name,aliases,email,domain,reason,level
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#") or line.lower().startswith("name"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if not parts[0]:
            continue
        rows.append(_norm_entry({
            "name": parts[0],
            "aliases": [parts[1]] if len(parts) > 1 and parts[1] else [],
            "email": parts[2] if len(parts) > 2 else "",
            "domain": parts[3] if len(parts) > 3 else "",
            "reason": parts[4] if len(parts) > 4 else "list_hit",
            "level": parts[5] if len(parts) > 5 else "blocked",
        }))
    return rows


def _norm_entry(x: Any) -> dict[str, Any]:
    if not isinstance(x, dict):
        return {}
    aliases = x.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    return {
        "name": str(x.get("name") or x.get("Name") or ""),
        "aliases": [str(a) for a in aliases],
        "email": str(x.get("email") or ""),
        "domain": str(x.get("domain") or ""),
        "reason": str(x.get("reason") or x.get("program") or "list_hit"),
        "level": str(x.get("level") or "blocked"),
        "source": str(x.get("source") or "list"),
    }


def _try_remote_list() -> tuple[list[dict[str, Any]], str]:
    url = (os.getenv("SANCTIONS_LIST_URL") or "").strip()
    if not url:
        return [], ""
    try:
        import httpx

        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url)
        if resp.status_code >= 300:
            return [], f"remote_error:{resp.status_code}"
        items = _parse_list_text(resp.text)
        return items, f"remote:{url[:80]}"
    except Exception as exc:  # noqa: BLE001
        return [], f"remote_error:{str(exc)[:80]}"


def load_sanctions_list() -> dict[str, Any]:
    items, source = _load_local_list()
    if not items or source.startswith("seed_demo"):
        remote, remote_src = _try_remote_list()
        if remote:
            return {"configured": True, "source": remote_src, "items": remote, "count": len(remote)}
    configured = source not in ("seed_demo",) and bool(items)
    return {
        "configured": configured,
        "source": source,
        "items": items,
        "count": len(items),
        "note": (
            "本地/远程名单已加载"
            if configured
            else "当前为开发种子名单或未配置真实源 — 未接入外部名单 API，结果以人工核对为准；生产请设 SANCTIONS_LIST_PATH 或 SANCTIONS_LIST_URL"
        ),
    }


def screen_subject(
    *,
    name: str = "",
    email: str = "",
    company: str = "",
    domain: str = "",
    extra: Optional[list[str]] = None,
) -> dict[str, Any]:
    """名单筛查：返回 blocked/watch/clear/not_configured。"""
    loaded = load_sanctions_list()
    items = list(loaded.get("items") or [])
    hay_parts = [name, email, company, domain, *(extra or [])]
    hay = " ".join(str(p or "") for p in hay_parts).lower()
    hay_email = (email or "").lower()
    hay_domain = (domain or "").lower()

    hits = []
    for it in items:
        reasons = []
        level = (it.get("level") or "blocked").lower()
        name_hit = (it.get("name") or "").lower()
        if name_hit and name_hit in hay:
            reasons.append(f"name:{it.get('name')}")
        for alias in it.get("aliases") or []:
            a = str(alias).lower()
            if a and a in hay:
                reasons.append(f"alias:{alias}")
        em = (it.get("email") or "").lower()
        if em and em == hay_email:
            reasons.append(f"email:{em}")
        dom = (it.get("domain") or "").lower()
        if dom and dom and (dom == hay_domain or dom in hay):
            reasons.append(f"domain:{dom}")
        if reasons:
            hits.append({
                "level": "blocked" if level in ("blocked", "deny", "sdn") else "watch",
                "reason": it.get("reason") or "list_hit",
                "matched": reasons,
                "source": it.get("source") or loaded.get("source"),
            })

    if not loaded.get("configured") and loaded.get("source") == "seed_demo":
        # 未配真源时：仅种子命中算 blocked；否则 not_configured + 提示
        if not hits:
            return {
                "result": "not_configured",
                "level": "unknown",
                "hits": [],
                "source": loaded.get("source"),
                "plain": "未配置真实制裁名单源 — 结果不可当作「已合规」，需人工核对。",
                "next_action": "配置 SANCTIONS_LIST_PATH 或 SANCTIONS_LIST_URL 后重扫。",
            }
    if any(h["level"] == "blocked" for h in hits):
        return {
            "result": "blocked",
            "level": "blocked",
            "hits": hits,
            "source": loaded.get("source"),
            "plain": "名单命中（高风险）— 禁止自动 PI/自动发送，须合规复核。",
            "next_action": "冻结自动动作；人工确认是否误报。",
        }
    if hits:
        return {
            "result": "watch",
            "level": "watch",
            "hits": hits,
            "source": loaded.get("source"),
            "plain": "名单观察命中 — 可继续跟进，但收款/PI 需人审。",
            "next_action": "提高定金、核实账户，PI 保持人审。",
        }
    return {
        "result": "clear",
        "level": "clear",
        "hits": [],
        "source": loaded.get("source"),
        "configured": loaded.get("configured"),
        "plain": (
            f"名单筛查通过（源：{loaded.get('source')}）"
            if loaded.get("configured")
            else "未发现命中（源为开发种子/未配置真源时不可当作合规证明）"
        ),
        "next_action": "到期后按重扫周期再筛。",
    }


def list_source_status() -> dict[str, Any]:
    loaded = load_sanctions_list()
    return {
        "configured": bool(loaded.get("configured")),
        "source": loaded.get("source"),
        "count": loaded.get("count"),
        "note": loaded.get("note"),
        "env_path": bool((os.getenv("SANCTIONS_LIST_PATH") or "").strip()),
        "env_url": bool((os.getenv("SANCTIONS_LIST_URL") or "").strip()),
        "env_inline": bool((os.getenv("SANCTIONS_LIST_INLINE") or "").strip()),
        "plain_summary": (
            f"制裁名单源：{loaded.get('source')}，条目 {loaded.get('count')}"
            if loaded.get("configured")
            else f"制裁名单源未就绪（{loaded.get('source')}）— 仅作提醒，不宣称合规"
        ),
    }
