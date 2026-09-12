#!/usr/bin/env python3
"""PM-05 前置 · 合并 COMP-03 骨架 + 截图 → 送检手册 HTML"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "docs" / "compliance" / "comp-03-manual"
OUT = ROOT / "docs" / "compliance" / "cert-manual-draft.html"


def md_to_html_simple(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_ul = False
    for line in lines:
        if line.startswith("# "):
            out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("!["):
            # ![alt](path)
            import re

            m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if m:
                alt, src = m.group(1), m.group(2)
                # resolve relative to manual dir
                rel = Path("../../cert-screenshots") / Path(src).name
                if (ROOT / "docs" / "cert-screenshots" / Path(src).name).exists():
                    out.append(
                        f'<figure><img src="{rel.as_posix()}" alt="{alt}" style="max-width:100%"/>'
                        f"<figcaption>{alt}</figcaption></figure>"
                    )
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def main() -> None:
    parts = [
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>",
        "<title>优丁建材 AI-SaaS 用户操作手册（送检草案）</title>",
        "<style>body{font-family:sans-serif;max-width:900px;margin:2rem auto;line-height:1.6}",
        "h1{border-bottom:1px solid #ccc}figure{margin:1.5rem 0}</style></head><body>",
        "<h1>优丁建材 AI-SaaS 智能营销平台 V2.0 · 用户操作手册（草案）</h1>",
        "<p><em>COMP-03 骨架合并 · 人类章节待扩写 · PM-05 PDF 前置</em></p>",
    ]
    for md in sorted(MANUAL.glob("*.md")):
        if md.name == "README.md":
            continue
        parts.append(md_to_html_simple(md.read_text(encoding="utf-8")))
        parts.append("<hr/>")
    parts.append("</body></html>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
