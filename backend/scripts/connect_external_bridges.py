# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外部桥探针 + env 同步 + 生产门禁复跑。

用法：
    python scripts/connect_external_bridges.py
    python scripts/connect_external_bridges.py --use-real-translate  # 真引擎健康时切 8099

诚实纪律：
    · GoodJob/翻译未健康 → 不改 env 假装已接
    · TradeAI 适配器 is_available 与 HTTP BASE_URL 分开报告
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

BACKEND = Path(__file__).resolve().parents[1]
ENV_FILES = [BACKEND / ".env", BACKEND / "config" / "dev" / ".env"]
GOODJOB_URL = "http://127.0.0.1:5188"
LT_STUB = "http://127.0.0.1:8098"
LT_REAL = "http://127.0.0.1:8099"
LT_TOKEN = "dev-sidecar-token"


def _probe(url: str, path: str = "/api/health", headers: dict | None = None, timeout: float = 5.0) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get(f"{url.rstrip('/')}{path}", headers=headers or {})
        body: Any
        try:
            body = r.json()
        except Exception:
            body = r.text[:200]
        return {"ok": r.status_code < 300, "status": r.status_code, "body": body, "url": url + path}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "url": url + path}


def probe_goodjob() -> dict[str, Any]:
    return _probe(GOODJOB_URL, "/api/health")


def probe_tradeai() -> dict[str, Any]:
    out: dict[str, Any] = {"base_url_env": (os.getenv("TRADEAI_BASE_URL") or "").strip() or None}
    try:
        sys.path.insert(0, str(BACKEND))
        from app.services.adapters import tradeai  # noqa: WPS433

        out["adapter_is_available"] = bool(tradeai.is_available())
        out["mode"] = "in_process_adapter" if out["adapter_is_available"] else "unavailable"
        out["plain"] = (
            "TradeAI 适配器进程内已加载（无需外部 HTTP 也可调度 vendor 能力面）"
            if out["adapter_is_available"]
            else "TradeAI 适配器未加载"
        )
    except Exception as exc:
        out["adapter_is_available"] = False
        out["error"] = str(exc)[:200]
    if out.get("base_url_env"):
        out["http"] = _probe(out["base_url_env"], "/health")
    return out


def probe_translate(url: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {LT_TOKEN}"} if LT_TOKEN else None
    for path in ("/languages", "/health", "/v1/health"):
        r = _probe(url, path, headers=headers, timeout=8.0)
        if r.get("ok"):
            r["healthy"] = True
            r["path"] = path
            return r
    r["healthy"] = False
    return r


def _set_env_key(key: str, value: str) -> None:
    for env_path in ENV_FILES:
        if not env_path.exists():
            continue
        text = env_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-real-translate", action="store_true", help="真翻译引擎健康时切到 8099 并关桩")
    args = ap.parse_args()

    report: dict[str, Any] = {"goodjob": probe_goodjob(), "tradeai": probe_tradeai()}
    report["libretranslate_stub"] = probe_translate(LT_STUB)
    report["libretranslate_real"] = probe_translate(LT_REAL)

    # GoodJob：健康才写 BASE_URL
    if report["goodjob"].get("ok"):
        _set_env_key("GOODJOB_BASE_URL", GOODJOB_URL)
        _set_env_key("GOODJOB_BRIDGE_TOKEN", "dev-bridge-token")
        report["goodjob"]["env_written"] = GOODJOB_URL
    else:
        report["goodjob"]["env_written"] = None
        report["goodjob"]["note"] = "GoodJob 未健康，不写入 GOODJOB_BASE_URL（避免假成功）"

    # 翻译：仅在 --use-real-translate 且真引擎健康时切换
    if args.use_real_translate and report["libretranslate_real"].get("ok"):
        _set_env_key("LIBRETRANSLATE_URL", LT_REAL)
        _set_env_key("LIBRETRANSLATE_TOKEN", LT_TOKEN)
        _set_env_key("LIBRETRANSLATE_ALLOW_DEV_STUB", "0")
        report["translate_switched"] = LT_REAL
    else:
        report["translate_switched"] = None
        if not report["libretranslate_real"].get("ok"):
            report["translate_note"] = "真翻译引擎未就绪（模型下载/网络），保持开发桩，不假装生产已接"

    # 门禁（读当前进程 env + 刚写的文件不会自动 reload，这里按报告口径打印）
    sys.path.insert(0, str(BACKEND))
    # 把写入的值注入当前进程，供门禁读取
    for env_path in ENV_FILES:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    if report.get("translate_switched"):
        os.environ["LIBRETRANSLATE_URL"] = LT_REAL
        os.environ["LIBRETRANSLATE_ALLOW_DEV_STUB"] = "0"

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    sys.path.insert(0, str(BACKEND))
    from verify_acquisition_production_gates import check_production_gates  # type: ignore

    try:
        report["production_gates"] = check_production_gates()
    except Exception as exc:
        report["production_gates"] = {"error": str(exc)[:200]}

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["goodjob"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
