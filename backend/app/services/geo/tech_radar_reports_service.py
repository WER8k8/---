"""RADAR-06/08：技术雷达 Markdown 日报索引。"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    """实现 reporoot 的功能。
    
    :return: 返回 Path 结果
    """
    return Path(__file__).resolve().parents[4]


def _radar_dir() -> Path:
    """实现 radardir 的功能。
    
    :return: 返回 Path 结果
    """
    return _repo_root() / "docs" / "geo" / "tech-radar"


def list_tech_radar_reports(limit: int = 14) -> dict[str, Any]:
    """实现 列出techradarreports 的功能。
    
    :param limit: 参数 limit（类型: int）
    :return: 返回 dict[str, Any] 结果
    """
    out_dir = _radar_dir()
    if not out_dir.is_dir():
        return {"count": 0, "reports": [], "dir": str(out_dir.relative_to(_repo_root()))}
    files = sorted(out_dir.glob("*.md"), reverse=True)[:limit]
    reports: list[dict[str, Any]] = []
    for path in files:
        try:
            stat = path.stat()
            reports.append(
                {
                    "date": path.stem,
                    "path": str(path.relative_to(_repo_root())).replace("\\", "/"),
                    "bytes": stat.st_size,
                    "modified_at": stat.st_mtime,
                }
            )
        except OSError:
            continue
    return {
        "count": len(reports),
        "reports": reports,
        "dir": str(out_dir.relative_to(_repo_root())).replace("\\", "/"),
    }
