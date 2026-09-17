# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 租户 Research Brief 预制模板（Hermes×AnySearch 研究沉淀）。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_TEMPLATES_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "deerflow_research_brief_templates.json"
)


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    """_load_catalog。
    :return: 返回处理结果。
    """
    if not _TEMPLATES_PATH.is_file():
        return {"templates": []}
    with open(_TEMPLATES_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_brief_templates() -> list[dict[str, Any]]:
    """list_brief_templates。
    :return: 返回处理结果。
    """
    out: list[dict[str, Any]] = []
    for t in _load_catalog().get("templates") or []:
        out.append(
            {
                "id": t.get("id"),
                "title": t.get("title"),
                "lane": t.get("lane"),
                "message_default": t.get("message_default"),
                "benchmark_pct": t.get("benchmark_pct"),
            }
        )
    return out


def get_brief_template(template_id: str) -> dict[str, Any] | None:
    """get_brief_template。

    参数说明：
    :param template_id: 参数 template_id
    :return: 返回处理结果。
    """
    tid = (template_id or "").strip()
    if not tid:
        return None
    for t in _load_catalog().get("templates") or []:
        if t.get("id") == tid:
            return dict(t)
    return None


def match_brief_template(
    message: str,
    *,
    template_id: str | None = None,
) -> dict[str, Any] | None:
    """match_brief_template。

    参数说明：
    :param message: 参数 message
    :param template_id: 参数 template_id
    :return: 返回处理结果。
    """
    if template_id:
        return get_brief_template(template_id)
    msg = (message or "").strip().lower()
    if not msg:
        return None
    for t in _load_catalog().get("templates") or []:
        for phrase in t.get("trigger_phrases") or []:
            if phrase.lower() in msg:
                return dict(t)
        tid = str(t.get("id") or "")
        if tid and tid.lower() in msg:
            return dict(t)
    return None


def apply_brief_template(brief: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """将 Hermes 外网研究结论并入 DeerFlow Brief（不替换 M0 内信号）。"""
    prefix = template.get("executive_prefix") or f"【{template.get('title', '模板')}】"
    notes = template.get("executive_notes") or ""
    bench = template.get("benchmark_pct") or {}
    bench_line = ""
    if bench:
        parts = [f"{k}≈{v}%" for k, v in bench.items()]
        bench_line = " 能力对标估算：" + "、".join(parts[:5]) + "。"
    base_exec = brief.get("executive_summary") or ""
    brief["executive_summary"] = f"{prefix}{notes}{bench_line} {base_exec}".strip()
    existing_urls = {
        (f.get("url") or "").strip()
        for f in brief.get("findings") or []
        if isinstance(f, dict)
    }
    merged_findings = list(brief.get("findings") or [])
    for ext in template.get("external_findings") or []:
        if not isinstance(ext, dict):
            continue
        url = (ext.get("url") or "").strip()
        if url and url in existing_urls:
            continue
        merged_findings.append(ext)
        if url:
            existing_urls.add(url)
    brief["findings"] = merged_findings
    extra_actions = template.get("accio_actions_extra") or []
    base_actions = list(brief.get("accio_actions") or [])
    seen_skills = {a.get("skill_id") for a in base_actions if isinstance(a, dict)}
    for action in reversed(extra_actions):
        if not isinstance(action, dict):
            continue
        sid = action.get("skill_id")
        if sid in seen_skills:
            continue
        base_actions.insert(0, action)
        seen_skills.add(sid)
    brief["accio_actions"] = base_actions
    brief["template_id"] = template.get("id")
    brief["template_title"] = template.get("title")
    brief["template_lane"] = template.get("lane")
    brief["suggested_pm_tasks"] = template.get("suggested_pm_tasks") or []
    brief["framework"] = "deerflow_lite+hermes_template"
    brief["template_source"] = _load_catalog().get("source")
    brief["disclaimer"] = (
        str(brief.get("disclaimer") or "")
        + " 模板含 Hermes×AnySearch 外网摘要，执行前请人工核实引用时效。"
    ).strip()
    if brief.get("agents") and isinstance(brief["agents"], dict):
        brief["agents"]["researcher"] = dict(brief["agents"].get("researcher") or {})
        brief["agents"]["researcher"]["findings_count"] = len(merged_findings)
        brief["agents"]["researcher"]["template_applied"] = template.get("id")
    return brief
