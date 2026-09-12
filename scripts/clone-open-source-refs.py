#!/usr/bin/env python3
"""Shallow-clone all open-source reference repos into _ref/ for Phase 0 audit."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "_ref"
MANIFEST = REF / "clone-manifest.json"

REPOS = [
    {
        "id": "vue-vben-admin",
        "url": "https://github.com/vbenjs/vue-vben-admin.git",
        "dir": "vue-vben-admin",
        "note": "唯一 Admin 底座 · web-antd",
    },
    {
        "id": "art-design-pro-edge",
        "url": "https://github.com/ChnMig/art-design-pro-edge.git",
        "dir": "art-design-pro-edge",
        "note": "多租户 + useTable + 动态菜单",
    },
    {
        "id": "art-design-pro",
        "url": "https://github.com/Daymychen/art-design-pro.git",
        "dir": "art-design-pro",
        "note": "Art 上游视觉",
    },
    {
        "id": "soybean-admin",
        "url": "https://github.com/soybeanjs/soybean-admin.git",
        "dir": "soybean-admin",
        "note": "工程规范 API 分层",
    },
    {
        "id": "vue-element-admin",
        "url": "https://github.com/PanJiaChen/vue-element-admin.git",
        "dir": "vue-element-admin",
        "note": "守卫 + meta 经典",
    },
    {
        "id": "vue-admin-better",
        "url": "https://github.com/zxwk1998/vue-admin-better.git",
        "dir": "vue-admin-better",
        "note": "CRUD 生成器",
    },
    {
        "id": "naive-ui-admin",
        "url": "https://github.com/jekip/naive-ui-admin.git",
        "dir": "naive-ui-admin",
        "note": "租户 SaaS 视觉",
    },
    {
        "id": "ruoyi-plus-soybean",
        "url": "https://github.com/m-xlsea/ruoyi-plus-soybean.git",
        "dir": "ruoyi-plus-soybean",
        "note": "后端能力清单",
    },
    {
        "id": "formily",
        "url": "https://github.com/alibaba/formily.git",
        "dir": "formily",
        "note": "Schema 表单核心",
    },
    {
        "id": "formily-antdv-x3",
        "url": "https://github.com/formilyjs/antdv-x3.git",
        "dir": "formily-antdv-x3",
        "note": "Formily + Ant Design Vue 3",
    },
    {
        "id": "daisyui",
        "url": "https://github.com/saadeghi/daisyui.git",
        "dir": "daisyui",
        "note": "Tailwind 营销组件",
    },
    {
        "id": "vue-pure-admin",
        "url": "https://gitee.com/yiming_chang/vue-pure-admin.git",
        "dir": "vue-pure-admin",
        "note": "Pure Mock + 主题",
    },
    {
        "id": "grooveshop-storefront-ui-node-nuxt",
        "url": "https://github.com/vasilistotskas/grooveshop-storefront-ui-node-nuxt.git",
        "dir": "grooveshop-storefront-ui-node-nuxt",
        "note": "SITE-DESIGN-01 · Nuxt 产品目录/筛选/SSR 参考",
    },
    {
        "id": "nuxtless",
        "url": "https://github.com/grandant/nuxtless.git",
        "dir": "nuxtless",
        "note": "SITE-DESIGN-01 · Nuxt4 SEO+i18n 店面 starter",
    },
    {
        "id": "sales-portal",
        "url": "https://github.com/geins-io/sales-portal.git",
        "dir": "sales-portal",
        "note": "SITE-DESIGN-01 · 多租户 hostname 店面",
    },
    {
        "id": "cf_b2b",
        "url": "https://github.com/geeeeeeeek/cf_b2b.git",
        "dir": "cf_b2b",
        "note": "SITE-DESIGN-01 · Cloudflare B2B 对照 reference_only",
    },
    {
        "id": "web_b2b",
        "url": "https://github.com/geeeeeeeek/web_b2b.git",
        "dir": "web_b2b",
        "note": "SITE-DESIGN-01 · Python B2B 信息架构对照",
    },
]


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def file_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    skip = {"node_modules", ".git", "dist", ".venv", "__pycache__"}
    n = 0
    for dp, dns, fns in __import__("os").walk(path):
        dns[:] = [d for d in dns if d not in skip]
        n += len(fns)
    return n


def git_head(path: Path) -> str | None:
    code, out = run(["git", "rev-parse", "HEAD"], cwd=path)
    return out if code == 0 else None


def clone_one(spec: dict) -> dict:
    dest = REF / spec["dir"]
    entry = {
        "id": spec["id"],
        "dir": spec["dir"],
        "url": spec["url"],
        "note": spec["note"],
        "path": str(dest),
        "status": "pending",
        "commit": None,
        "files": 0,
        "error": None,
    }
    REF.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (dest / ".git").exists():
        fc = file_count(dest)
        # 不完整 clone（如 sparse 仅根目录）→ 删除重拉
        if spec["id"] == "vue-vben-admin" and fc < 500:
            # 优先修复 sparse checkout，避免 Windows 锁文件删不掉 .git
            code, _ = run(["git", "sparse-checkout", "disable"], cwd=dest)
            if code == 0:
                run(["git", "checkout", "-f", "HEAD"], cwd=dest)
                fc2 = file_count(dest)
                if fc2 >= 500:
                    entry["status"] = "repaired_sparse"
                    entry["commit"] = git_head(dest)
                    entry["files"] = fc2
                    return entry
            import shutil
            try:
                shutil.rmtree(dest)
            except OSError as e:
                alt = REF / (spec["dir"] + "-full")
                if alt.exists():
                    entry["status"] = "exists"
                    entry["commit"] = git_head(alt)
                    entry["files"] = file_count(alt)
                    entry["path"] = str(alt)
                    entry["note"] = spec["note"] + " (use -full dir)"
                    return entry
                dest = alt
                entry["path"] = str(dest)
        else:
            entry["status"] = "exists"
            entry["commit"] = git_head(dest)
            entry["files"] = fc
            return entry
    if dest.exists():
        entry["status"] = "skip_non_git"
        entry["error"] = "path exists but not a git repo"
        return entry
    code, out = run(
        ["git", "clone", "--depth", "1", spec["url"], str(dest)],
        cwd=REF,
    )
    if code != 0:
        entry["status"] = "failed"
        entry["error"] = out[-2000:]
        return entry
    entry["status"] = "cloned"
    entry["commit"] = git_head(dest)
    entry["files"] = file_count(dest)
    return entry


def main() -> int:
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    results = []
    for spec in REPOS:
        if only and spec["id"] not in only and spec["dir"] not in only:
            continue
        print(f"[clone] {spec['id']} ...", flush=True)
        results.append(clone_one(spec))
    manifest = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "ref_root": str(REF),
        "repos": results,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    failed = [r for r in results if r["status"] == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
