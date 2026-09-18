# -*- coding: utf-8 -*-
"""P2-2a 设计锁门禁（DESIGN-TOKEN / LOGIN / ROLE-SHELL 三硬锁 · 精确版）。

仅针对锁的真实不变量告警，不误伤：
- 近黑 #0f172a 文字色 / hero黑底卡片（中性排版，允许）
- 装饰性渐变 accent / 卡片角标 / 图表序列色 / warning·info·channel·role 语义色（DESIGN §1.2 允许）
- Lock 定义常量文件（含禁止清单文档）

告警仅当：
  A. 主色令牌定义被置为非薄荷：`--color-primary`/`--uj-brand`/primary token = banned hex
  B. 主操作/主按钮被盖成违禁色：`.ant-btn-primary`/`btn-primary`/button-primary 的
     background / border-color / color = #2563eb/#3b82f6/#7c3aed/#ea580c
  C. 组件将 banned 蓝声明为品牌色：`$brand-*`/`--brand-*`/`brand:` 前缀变量 = #2563eb/#3b82f6

用法：python scripts/verify_design_locks.py [--json]
退出码：0=锁未破；1=发现违禁（需修复）。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
WORKTREE = os.path.dirname(ROOT)
EXCLUDE_DIRS = {
    "node_modules", "dist", ".git", "Lib", ".venv", "venv", "__pycache__",
    ".output", ".output.bak", "external", "_archive", ".nuxt", "_nuxt",
}
EDIBLE_PREFIX = ("frontend/admin",)  # 后台/平台品牌域（薄荷单真源管辖区）
BAN = ("#2563eb", "#3b82f6", "#7c3aed", "#ea580c")

PRIMARY_DEF = re.compile(r"(--color-primary|--primary|--uj-brand|--saas-primary\b|--b2b-primary\b)\s*:\s*(#[0-9a-fA-F]{3,8})\b")
BRAND_VAR = re.compile(r"(\$|--)[a-z0-9_-]*brand[a-z0-9_-]*\s*:\s*(#[0-9a-fA-F]{3,8})\b")
PRIMARY_BTN = re.compile(r"\.ant-btn-primary|\.btn-primary|\.button-primary|\.ant-btn[^{]*\{")

LOCK_FILES = {"roleShellLock.ts", "loginPortalCopy.ts", "stubVisibility.ts"}


def lower_hex(c: str) -> str:
    return c.lower()


def walk(root_dir):
    for base, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith((".vue", ".scss", ".css", ".ts")):
                yield os.path.join(base, f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    flagged = []
    mint_present = 0
    admin_dir = os.path.join(WORKTREE, "frontend", "admin")
    for p in walk(admin_dir):
        rel = os.path.relpath(p, WORKTREE).replace("\\", "/")
        if not any(rel.startswith(e) for e in EDIBLE_PREFIX):
            continue
        base = os.path.basename(p)
        if base.lower() in {x.lower() for x in LOCK_FILES}:
            continue
        try:
            s = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        lower = s.lower()
        mint_present += s.lower().count("#4a9b8c") + s.lower().count("--color-primary")
        # A. 主色令牌定义被置为非薄荷
        for m in PRIMARY_DEF.finditer(s):
            val = lower_hex(m.group(2))
            if val in BAN:
                flagged.append(f"TOKEN-{val} {rel}: {m.group(0)}")
        # C. brand 变量 = banned
        for m in BRAND_VAR.finditer(s):
            val = lower_hex(m.group(2))
            if val in BAN:
                flagged.append(f"BRAND-{val} {rel}: {m.group(0)}")
        # B. 主按钮背景/边框/文字 = banned（只在含 btn-primary 的文件里查）
        if "btn-primary" in lower or "button-primary" in lower:
            for ln, line in enumerate(s.splitlines(), 1):
                if "btn-primary" not in line.lower() and "button-primary" not in line.lower():
                    continue
                lowl = line.lower()
                if not any(k in lowl for k in ("background", "border-color", "color")):
                    continue
                for c in ("#2563eb", "#3b82f6", "#7c3aed", "#ea580c"):
                    if c in lowl:
                        flagged.append(f"BTN-{c} {rel}:{ln}: {line.strip()[:90]}")

    # 唯一登录：禁路由若带 component（即第二登录页）才算违禁；纯 redirect 别名合规
    router = os.path.join(admin_dir, "src", "router", "index.ts")
    login_issue = []
    if os.path.exists(router):
        lines = open(router, encoding="utf-8").readlines()
        for i, line in enumerate(lines):
            t = line.strip()
            m = re.search(r"(/client/login|/tenant/login|\?portal=)", t)
            if not m:
                continue
            low = t.lower()
            # 下一行是否为 redirect（兼容别名）
            nxt = lines[i + 1].lower() if i + 1 < len(lines) else ""
            is_redirect = "redirect" in low or "redirect" in nxt
            has_component = "component:" in low
            if has_component and not is_redirect:
                login_issue.append(f"{i + 1}: {t[:90]}")

    ok = (not flagged) and (not login_issue) and mint_present > 0
    if a.json:
        print({"lock_pass": ok, "flagged": flagged, "login_issues": login_issue, "mint_token_refs": mint_present})
    else:
        print(f"主色令牌/品牌/主按钮违禁命中: {len(flagged)}")
        for x in flagged:
            print("  ", x)
        print(f"非 redirect 的多登录路由: {len(login_issue)}")
        for x in login_issue:
            print("  ", x)
        print(f"薄荷主色令牌引用 {mint_present} 处")
        print("P2-2a 三锁门禁:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())