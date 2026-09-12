#!/usr/bin/env python3
"""COMP-02 · 导出软著 60 页文本（每页 ≤50 行，自研目录内）"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / "docs/compliance/soft-copyright-file-export.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs/compliance/rz-60-pages"
LINES_PER_PAGE = 50


def paginate_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    lines = text.splitlines()
    pages: list[str] = []
    for i in range(0, len(lines), LINES_PER_PAGE):
        chunk = lines[i : i + LINES_PER_PAGE]
        pages.append(f"// FILE: {path.relative_to(ROOT)}\n" + "\n".join(chunk))
    return pages


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_files = SRC.get("backend_files", []) + SRC.get("frontend_files", [])
    pages: list[str] = []
    for rel in all_files:
        pages.extend(paginate_file(ROOT / rel))
    # 取前 60 页
    for idx, content in enumerate(pages[:60], start=1):
        (OUT / f"page-{idx:03d}.txt").write_text(content, encoding="utf-8")
    meta = {"total_source_pages": len(pages), "exported": min(60, len(pages))}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Exported {meta['exported']} pages to {OUT}")


if __name__ == "__main__":
    main()
