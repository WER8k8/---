# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RADAR-08：技术雷达 Markdown 日报导出。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    return Path(__file__).resolve().parents[4]


def export_tech_radar_markdown(radar: dict[str, Any] | None) -> dict[str, Any]:
    """export_tech_radar_markdown。

    参数说明：
    :param radar: 参数 radar
    :return: 返回处理结果。
    """
    if not radar:
        return {"ok": False, "reason": "empty_radar"}
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# GEO 技术雷达 · {date}",
        "",
        f"- 抓取时间：{radar.get('fetched_at') or '—'}",
        f"- 高影响：{radar.get('high_impact_count', 0)}",
        f"- 专家否决：{radar.get('expert_fail_count', 0)}",
        "",
        "## 候选",
        "",
    ]
    for c in (radar.get("candidates") or [])[:25]:
        title = c.get("title") or c.get("url") or "—"
        impact = c.get("impact") or "—"
        verdict = c.get("expert_verdict") or "—"
        lines.append(f"- **{title}** · 影响 `{impact}` · 专家 `{verdict}`")
        if c.get("url"):
            lines.append(f"  - {c['url']}")
    body = "\n".join(lines) + "\n"
    out_dir = _repo_root() / "docs" / "geo" / "tech-radar"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}.md"
    path.write_text(body, encoding="utf-8")
    return {"ok": True, "path": str(path.relative_to(_repo_root())), "bytes": len(body.encode())}
