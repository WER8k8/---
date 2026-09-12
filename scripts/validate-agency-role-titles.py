#!/usr/bin/env python3
"""校验 agency 角色 frontmatter name 与首级 H1 标题（sync 后门禁）。"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = ROOT / "backend" / "app" / "data" / "agency_roles"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_GENERIC_H1 = re.compile(r"^#\s*(?:🧠\s*)?你的身份与记忆\s*$", re.M)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str, str | None]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text, None
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    body = text[m.end() :]
    return meta, body, m.group(0)


def _first_h1(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return None


def _is_generic_h1(h1: str | None) -> bool:
    if not h1:
        return False
    return bool(re.fullmatch(r"(?:🧠\s*)?你的身份与记忆", h1))


def audit_roles(*, fix: bool = False) -> tuple[list[dict], int]:
    issues: list[dict] = []
    fixed = 0
    for md in sorted(ROLES_DIR.rglob("*.md")):
        rel = md.relative_to(ROLES_DIR).as_posix()
        if rel.startswith("strategy/"):
            continue
        raw = md.read_text(encoding="utf-8")
        meta, body, fm = _parse_frontmatter(raw)
        if fm is None:
            continue
        name = (meta.get("name") or "").strip()
        rel = md.relative_to(ROLES_DIR).as_posix()
        h1 = _first_h1(body)
        if not name:
            issues.append({"file": rel, "kind": "missing_name"})
            continue
        if _is_generic_h1(h1):
            if fix and fm is not None:
                new_body = _GENERIC_H1.sub(f"# {name}", body, count=1)
                md.write_text(fm + new_body, encoding="utf-8")
                fixed += 1
            else:
                issues.append(
                    {
                        "file": rel,
                        "kind": "generic_h1",
                        "name": name,
                        "h1": h1,
                    }
                )
    return issues, fixed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="将泛化 H1 替换为 frontmatter name")
    args = parser.parse_args()
    if not ROLES_DIR.is_dir():
        print(f"roles dir missing: {ROLES_DIR}", file=sys.stderr)
        return 1
    issues, fixed = audit_roles(fix=args.fix)
    if args.fix and fixed:
        print(f"fixed {fixed} role title(s)")
    if issues:
        for item in issues[:20]:
            print(f"FAIL {item}")
        if len(issues) > 20:
            print(f"... and {len(issues) - 20} more")
        return 1
    role_files = sum(
        1 for md in ROLES_DIR.rglob("*.md") if _FRONTMATTER_RE.match(md.read_text(encoding="utf-8"))
    )
    print(f"agency role titles OK ({role_files} role files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
