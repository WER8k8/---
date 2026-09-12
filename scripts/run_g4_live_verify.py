#!/usr/bin/env python3
"""G4 实机：配置探测 + 可选一次真实 LLM 调用（QA-08）。"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

try:
    from dotenv import load_dotenv

    for p in [
        BACKEND / "config" / "dev" / ".env",
        BACKEND.parent / ".env",
        BACKEND / ".env",
    ]:
        if p.is_file():
            load_dotenv(p, override=True)
            break
except ImportError:
    pass

os.environ.setdefault("JWT_SECRET_KEY", "g4-live-" + ("x" * 24))
os.environ.setdefault("SECRET_KEY", os.environ["JWT_SECRET_KEY"])
# 演示跳过：开发态用真实 Key，不强制 Mock
if os.getenv("MVP_LAUNCH", "").strip() == "":
    os.environ["MVP_LAUNCH"] = "0"


async def _live_ping() -> dict:
    from app.services.ai_engine import AIEngine

    engine = AIEngine()
    if not engine.is_available():
        return {"live_call": "skipped_mock_engine"}
    try:
        out = await engine.generate(
            "请只回复 OK 两个字母，不要其它内容。",
            model="general",
            max_tokens=16,
            task_complexity="simple",
            max_retries=1,
        )
        text = str(out.get("content") or out.get("optimized_content") or out)
        return {
            "live_call": "ok",
            "sample": text[:120],
            "provider": getattr(engine, "current_provider", None),
        }
    except Exception as exc:
        return {"live_call": "fail", "error": str(exc)[:300]}


def main() -> int:
    from app.db.session import SessionLocal
    from app.services.ai_key_probe import probe_ubrain_non_mock

    db = SessionLocal()
    try:
        st = probe_ubrain_non_mock(db)
    finally:
        db.close()

    if st.get("g4_pass") and os.getenv("G4_SKIP_LIVE", "").lower() not in (
        "1",
        "true",
        "yes",
    ):
        st["live"] = asyncio.run(_live_ping())
        if st["live"].get("live_call") == "fail":
            st["g4_pass"] = False

    report = {
        "g4_pass": bool(st.get("g4_pass")),
        "probe": st,
        "mvp_launch": os.getenv("MVP_LAUNCH", "0"),
    }
    out_path = ROOT / "docs" / "g4-ai-key-verify-latest.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    print(f"\nWrote {out_path}")
    return 0 if report["g4_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
