#!/usr/bin/env python3
"""The Agency + ECC 团队启动画面 — 扫描本机已安装的全部子代理。"""

from __future__ import annotations

import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

AGENCY_DIR = Path(os.environ.get("AGENCY_AGENTS_DIR", Path.home() / ".claude" / "agents"))


def _resolve_ecc_agents_dir() -> Path:
    """ECC 代理目录：优先外部 dev-stack，其次仓库 .cursor Junction。"""
    env = os.environ.get("DEV_STACK_CURSOR_DIR")
    if env:
        p = Path(env) / "agents"
        if p.is_dir():
            return p
    cfg = REPO_ROOT / ".project" / "dev-stack.config.json"
    if cfg.is_file():
        try:
            import json

            data = json.loads(cfg.read_text(encoding="utf-8"))
            cursor_root = Path(data.get("paths", {}).get("cursor", ""))
            agents = cursor_root / "agents"
            if agents.is_dir():
                return agents
        except Exception:
            pass
    return REPO_ROOT / ".cursor" / "agents"


ECC_DIR = _resolve_ecc_agents_dir()

DEPARTMENT_PREFIXES = {
    "engineering": "工程技术部",
    "design": "设计部",
    "marketing": "营销部",
    "sales": "销售部",
    "product": "产品部",
    "project-management": "项目管理部",
    "testing": "测试部",
    "support": "支持部",
    "spatial-computing": "空间计算部",
    "game-development": "游戏开发部",
    "academic": "学术研究部",
    "finance": "财务部",
    "paid-media": "付费媒体部",
    "specialized": "专业服务部",
}

GAME_SPATIAL_HINTS = (
    "game-",
    "unity-",
    "unreal-",
    "godot-",
    "roblox-",
    "xr-",
    "visionos-",
    "spatial-",
    "macos-spatial",
)


def classify_agency_agent(stem: str) -> str:
    for prefix in DEPARTMENT_PREFIXES:
        if prefix != "specialized" and stem.startswith(prefix):
            return prefix
    for hint in GAME_SPATIAL_HINTS:
        if stem.startswith(hint) or hint.strip("-") in stem:
            if any(
                stem.startswith(x)
                for x in ("game-", "unity-", "unreal-", "godot-", "roblox-")
            ):
                return "game-development"
            return "spatial-computing"
    return "specialized"


def scan_agency() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    if not AGENCY_DIR.is_dir():
        return groups
    for path in sorted(AGENCY_DIR.glob("*.md")):
        dept = classify_agency_agent(path.stem)
        groups[dept].append(path.stem)
    return groups


def scan_ecc() -> list[str]:
    if not ECC_DIR.is_dir():
        return []
    return sorted(p.stem for p in ECC_DIR.glob("*.md"))


def scan_codegraph() -> tuple[bool, str]:
    """返回 (已初始化, 状态摘要)。"""
    cg_dir = REPO_ROOT / ".codegraph"
    if not cg_dir.is_dir():
        return False, "未初始化 — 运行 scripts/install-dev-stack-external.ps1"
    db = cg_dir / "codegraph.db"
    if db.is_file():
        mb = db.stat().st_size / (1024 * 1024)
        return True, f"已索引 · DB {mb:.1f} MB · MCP codegraph · 本地 gitignore"
    return True, "目录存在，索引可能未完成 — 运行 codegraph sync"


def print_banner() -> None:
    print(
        """
╔══════════════════════════════════════════════════════════════════════╗
║     AI 全局栈 — CodeGraph + Hey AI README + Agency + ECC              ║
║     Agency 184 + ECC 38（222） + 本地代码图谱 MCP                       ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    )


def main() -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print_banner()
    print(f"扫描时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Agency 路径: {AGENCY_DIR}")
    print(f"ECC 路径:    {ECC_DIR}\n")

    agency = scan_agency()
    ecc = scan_ecc()
    agency_total = sum(len(v) for v in agency.values())
    ecc_total = len(ecc)

    print("=" * 72)
    print("  THE AGENCY（~/.claude/agents）")
    print("=" * 72)
    for dept in DEPARTMENT_PREFIXES:
        names = agency.get(dept, [])
        if names:
            print(f"  {DEPARTMENT_PREFIXES[dept]:<16} {len(names):>3} 位")
    print("-" * 72)
    print(f"  {'Agency 小计':<16} {agency_total:>3} 位")

    print("\n" + "=" * 72)
    print("  ECC v1.10.0（.cursor/agents）")
    print("=" * 72)
    for name in ecc[:12]:
        print(f"  • {name}")
    if ecc_total > 12:
        print(f"  • ... 另有 {ecc_total - 12} 位工程子代理")
    print("-" * 72)
    print(f"  {'ECC 小计':<16} {ecc_total:>3} 位")

    cg_ok, cg_msg = scan_codegraph()
    print("\n" + "=" * 72)
    print("  CodeGraph + Hey AI README")
    print("=" * 72)
    print(f"  CodeGraph:     {'OK' if cg_ok else '—'}  {cg_msg}")
    print("  Hey AI README: docs/Hey-AI-README.md · .cursor/rules/hey-ai-readme.mdc")

    print("\n" + "=" * 72)
    print(f"  合计在线: {agency_total + ecc_total} 位  |  工作流: 外部 dev-stack（见 DEV-TOOLS-ISOLATION.md）")
    print("=" * 72)

    phases = [
        "阶段 0  需求分析 & 战略规划",
        "阶段 1  架构设计",
        "阶段 2  核心开发（ECC 工程环）",
        "阶段 3  UI/UX 设计",
        "阶段 4  测试优化（ECC 质量门）",
        "阶段 5  上线准备",
        "阶段 6  运营维护",
    ]
    print("\n7 阶段编排已就绪：")
    for phase in phases:
        print(f"  {phase}")
        time.sleep(0.05)

    print("\n下一步: 描述你的任务；开发工具见 docs/DEV-TOOLS-ISOLATION.md。\n")
    return 0 if agency_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
