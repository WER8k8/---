#!/usr/bin/env python3
"""从 pm-dev-task-progress.json 渲染横向进度条 → docs/pm-dev-progress-bars.md"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/pm-dev-task-progress.json"
OUT = ROOT / "docs/pm-dev-progress-bars.md"
TRACKER = ROOT / "docs/ecc-delivery-tracker.md"
MARKER_START = "<!-- DEV-PROGRESS-BARS:START -->"
MARKER_END = "<!-- DEV-PROGRESS-BARS:END -->"

CSS = """
<style>
.yd-progress-wrap { font-family: ui-sans-serif, system-ui, sans-serif; font-size: 13px; max-width: 100%; }
.yd-progress-row {
  display: flex; align-items: center; gap: 10px;
  margin: 8px 0; width: 100%; flex-wrap: nowrap;
}
.yd-progress-row .id { flex: 0 0 72px; font-weight: 600; color: #0f172a; }
.yd-progress-row .name { flex: 0 0 160px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.yd-progress-row .track {
  flex: 1 1 auto; min-width: 80px; height: 12px;
  background: #e2e8f0; border-radius: 6px; overflow: hidden;
}
.yd-progress-row .fill {
  height: 100%; border-radius: 6px;
  background: linear-gradient(90deg, #2563eb, #60a5fa);
}
.yd-progress-row .pct { flex: 0 0 44px; text-align: right; font-weight: 700; color: #1e40af; }
.yd-progress-row .owner { flex: 0 0 52px; font-size: 12px; color: #94a3b8; text-align: right; }
.yd-progress-summary {
  display: flex; align-items: center; gap: 10px; margin: 12px 0 4px;
  padding-top: 8px; border-top: 1px dashed #cbd5e1;
}
.yd-progress-summary .label { flex: 0 0 232px; font-weight: 600; color: #475569; }
.yd-progress-summary .track { flex: 1; height: 14px; background: #e2e8f0; border-radius: 7px; overflow: hidden; }
.yd-progress-summary .fill { height: 100%; background: linear-gradient(90deg, #059669, #34d399); border-radius: 7px; }
.yd-progress-summary .pct { flex: 0 0 44px; text-align: right; font-weight: 700; }
</style>
"""


def bar_text(pct: int, width: int = 48) -> str:
    pct = max(0, min(100, pct))
    filled = round(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


def html_row(t: dict) -> str:
    p = max(0, min(100, t["pct"]))
    tid = html.escape(t["id"])
    name = html.escape(t["name"])
    owner = html.escape(t["owner"])
    return (
        f'<div class="yd-progress-row">'
        f'<span class="id">{tid}</span>'
        f'<span class="name">{name}</span>'
        f'<div class="track"><div class="fill" style="width:{p}%"></div></div>'
        f'<span class="pct">{p}%</span>'
        f'<span class="owner">{owner}</span>'
        f"</div>"
    )


def html_summary(label: str, avg: int) -> str:
    return (
        f'<div class="yd-progress-summary">'
        f'<span class="label">{html.escape(label)}</span>'
        f'<div class="track"><div class="fill" style="width:{avg}%"></div></div>'
        f'<span class="pct">{avg}%</span>'
        f"</div>"
    )


def text_line(t: dict, width: int) -> str:
    p = t["pct"]
    return (
        f"{t['id']:<10} {t['name']:<22} "
        f"{bar_text(p, width)}  {p:>3}%  {t['owner']}"
    )


def sprint_block(sprint: dict, width: int, *, html_mode: bool) -> list[str]:
    tasks = sprint.get("tasks", [])
    incomplete = [t for t in tasks if t.get("pct", 0) < 100]
    if not incomplete:
        return []
    label = sprint.get("label", "")
    lines: list[str] = [f"### {label}", ""]
    if html_mode:
        lines.append('<div class="yd-progress-wrap">')
        for t in incomplete:
            lines.append(html_row(t))
        avg = int(sum(t["pct"] for t in incomplete) / len(incomplete))
        lines.append(html_summary(f"平均 · {len(incomplete)} 项未完成", avg))
        lines.append("</div>")
    else:
        lines.append("```text")
        lines.append(f"{'ID':<10} {'任务':<22} {'进度条'.ljust(width)}  pct  主责")
        for t in incomplete:
            lines.append(text_line(t, width))
        avg = int(sum(t["pct"] for t in incomplete) / len(incomplete))
        lines.append(f"{'—平均—':<10} {'':<22} {bar_text(avg, width)}  {avg:>3}%")
        lines.append("```")
    lines.append("")
    return lines


def build_markdown(data: dict) -> str:
    width = data.get("bar_width", 48)
    updated = data.get("updated_at", "")
    lines = [
        "# 开发任务进度条（横向 · 仅未完成）",
        "",
        f"> **更新**：{updated} · 数据源 [`pm-dev-task-progress.json`](./pm-dev-task-progress.json)",
        f"> **刷新**：`backend\\.venv\\Scripts\\python.exe scripts/render-dev-progress-bars.py`",
        "",
        "## 横向进度（预览）",
        "",
        CSS,
        '<div class="yd-progress-wrap">',
    ]
    for key, sprint in data.get("sprints", {}).items():
        incomplete = [t for t in sprint.get("tasks", []) if t.get("pct", 0) < 100]
        if not incomplete:
            continue
        lines.append(f"<p><strong>{html.escape(sprint.get('label', key))}</strong></p>")
        for t in incomplete:
            lines.append(html_row(t))
        avg = int(sum(t["pct"] for t in incomplete) / len(incomplete))
        lines.append(html_summary(f"平均 · {len(incomplete)} 项未完成", avg))
        lines.append("<br/>")
    lines.append("</div>")
    lines.append("")
    lines.append("## 纯文本横向（终端 / 复制）")
    lines.append("")
    for key, sprint in data.get("sprints", {}).items():
        lines.extend(sprint_block(sprint, width, html_mode=False))
    lines.append("---")
    lines.append("*pct=100 的任务不显示；S2 人类签字链见分配表*")
    lines.append("")
    return "\n".join(lines)


def tracker_snippet(data: dict) -> str:
    width = 48
    lines = [
        "## 开发进度条（横向 · 未完成）",
        "",
        CSS,
        '<div class="yd-progress-wrap">',
    ]
    r1 = data["sprints"]["R1"]
    incomplete = [t for t in r1["tasks"] if t["pct"] < 100]
    for t in incomplete:
        lines.append(html_row(t))
    if incomplete:
        avg = int(sum(t["pct"] for t in incomplete) / len(incomplete))
        lines.append(html_summary("Sprint-R1 平均", avg))
    lines.append("</div>")
    lines.append("")
    lines.append("<details><summary>纯文本横向</summary>")
    lines.append("")
    lines.append("```text")
    for t in incomplete:
        lines.append(text_line(t, width))
    if incomplete:
        avg = int(sum(t["pct"] for t in incomplete) / len(incomplete))
        lines.append(f"{'—平均—':<10} {'':<22} {bar_text(avg, width)}  {avg:>3}%")
    lines.append("```")
    lines.append("</details>")
    lines.append("")
    lines.append("完整：[`pm-dev-progress-bars.md`](./pm-dev-progress-bars.md)")
    return "\n".join(lines)


def inject_tracker(snippet: str) -> None:
    if not TRACKER.is_file():
        return
    text = TRACKER.read_text(encoding="utf-8")
    block = f"{MARKER_START}\n{snippet.strip()}\n{MARKER_END}"
    if MARKER_START in text:
        start = text.index(MARKER_START)
        end = text.index(MARKER_END) + len(MARKER_END)
        text = text[:start] + block + text[end:]
    else:
        anchor = "## Sprint-R1"
        idx = text.index(anchor) if anchor in text else 0
        text = text[:idx] + block + "\n\n" + text[idx:]
    TRACKER.write_text(text, encoding="utf-8")


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.write_text(build_markdown(data), encoding="utf-8")
    inject_tracker(tracker_snippet(data))
    print(f"Wrote {OUT}")
    print(f"Injected horizontal progress bars into {TRACKER}")


if __name__ == "__main__":
    main()
