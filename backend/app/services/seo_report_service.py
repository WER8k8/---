# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SEO 报告 HTML 导出（可浏览器打印为 PDF）。"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape as html_escape
from typing import Any


def _safe_str(value: Any, default: str = "—") -> str:
    """将任意值安全转义为 HTML 文本。"""
    if value is None:
        return default
    return html_escape(str(value)) if str(value).strip() else default


def build_seo_report_html(metrics: dict[str, Any], *, site_url: str = "") -> str:
    """build_seo_report_html。

    参数说明：
    :param metrics: 参数 metrics
    :param site_url: 参数 site_url
    :return: 返回处理结果。
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    keywords = metrics.get("total_keywords", 0)
    ranked = metrics.get("ranked_keywords", 0)
    top = metrics.get("top_ranking", 0)
    traffic = metrics.get("traffic_estimate", "—")
    score = metrics.get("audit_score", metrics.get("score", "—"))
    issues = metrics.get("issues", 0)
    warnings = metrics.get("warnings", 0)
    rows = ""
    for item in metrics.get("top_keywords") or []:
        if isinstance(item, dict):
            rows += (
                f"<tr><td>{_safe_str(item.get('keyword', ''), '')}</td>"
                f"<td>{_safe_str(item.get('rank'))}</td>"
                f"<td>{_safe_str(item.get('volume'))}</td></tr>"
            )

    safe_site_url = html_escape(site_url or "（未指定）")
    safe_traffic = _safe_str(traffic)
    safe_score = _safe_str(score)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SEO 运营报告</title>
<style>
body{{font-family:"Microsoft YaHei",Arial,sans-serif;max-width:920px;margin:0 auto;padding:24px;color:#1e293b}}
h1{{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}}
.stat{{display:inline-block;padding:12px 18px;margin:6px;background:#f8fafc;border-radius:8px}}
.stat b{{font-size:22px;color:#2563eb;display:block}}
table{{width:100%;border-collapse:collapse;margin:16px 0}}
th,td{{padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:left}}
th{{background:#f1f5f9}}
@media print{{.no-print{{display:none}}}}
</style></head><body>
<p class="no-print"><button onclick="window.print()">打印 / 另存为 PDF</button></p>
<h1>SEO 运营报告</h1>
<p>站点：{safe_site_url} · 生成时间：{now}</p>
<div>
  <div class="stat"><span>关键词总数</span><b>{keywords}</b></div>
  <div class="stat"><span>有排名词</span><b>{ranked}</b></div>
  <div class="stat"><span>Top 排名</span><b>{top}</b></div>
  <div class="stat"><span>预估流量</span><b>{safe_traffic}</b></div>
  <div class="stat"><span>体检得分</span><b>{safe_score}</b></div>
  <div class="stat"><span>问题/警告</span><b>{issues}/{warnings}</b></div>
</div>
<h2>重点关键词</h2>
<table><thead><tr><th>关键词</th><th>排名</th><th>搜索量</th></tr></thead>
<tbody>{rows or '<tr><td colspan="3">暂无数据</td></tr>'}</tbody></table>
</body></html>"""
