#!/usr/bin/env python3
"""多媒体工厂 · 视频生成效果检验（写 docs/qa/media-factory-render-test-latest.json）。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend/config/dev/.env", override=True)

BASE = os.getenv("VERIFY_API_BASE", "http://127.0.0.1:8001/api/v1")
USER = os.getenv("VERIFY_ADMIN_USER", "admin")
PASS = os.getenv("VERIFY_ADMIN_PASS", "admin123")
OUT = ROOT / "docs/qa/media-factory-render-test-latest.json"


def main() -> int:
    report: dict = {"steps": [], "verdict": "unknown"}
    steps: list[dict] = report["steps"]

    def log(name: str, ok: bool, detail: str = "") -> None:
        steps.append({"name": name, "ok": ok, "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    with httpx.Client(timeout=180.0) as client:
        r = client.post(
            f"{BASE}/auth/login",
            json={"username_or_email": USER, "password": PASS},
        )
        body = r.json()
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        token = data.get("access_token") or data.get("token")
        if not token:
            log("login", False, r.text[:200])
            report["verdict"] = "blocked_no_api"
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1
        log("login", True)
        h = {"Authorization": f"Bearer {token}"}

        r = client.get(f"{BASE}/media-factory/", headers=h)
        ov = r.json().get("data", r.json()) if r.status_code == 200 else {}
        mock = ov.get("mock_render")
        log("overview", r.status_code == 200, f"mock_render={mock}")

        script = (
            "镜头1 | 大城岩棉工厂外景 | 旁白：产品展示检验\n"
            "镜头2 | 仓库装货 | 旁白：外贸出货"
        )
        r = client.post(
            f"{BASE}/media-factory/generate",
            headers=h,
            json={
                "script": script,
                "title": "视频效果检验",
                "resolution": "720p",
                "aspect": "16:9",
                "auto_render": False,
            },
        )
        task = r.json().get("data", r.json()) if r.status_code == 200 else {}
        tid = task.get("id")
        if not tid:
            log("create_task", False, r.text[:200])
            report["verdict"] = "create_failed"
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return 1
        log("create_task", True, tid)

        r = client.post(f"{BASE}/media-factory/tasks/{tid}/run-sync", headers=h)
        done = r.json().get("data", r.json()) if r.status_code == 200 else {}
        st = done.get("raw_status") or done.get("status")
        url = done.get("result_url") or ""
        err = done.get("error_message") or ""
        log("render_sync", st == "done" and bool(url), f"status={st} url={url} err={err}")

        if url:
            vr = client.get(f"http://127.0.0.1:8001{url}")
            ctype = vr.headers.get("content-type", "")
            log(
                "download_mp4",
                vr.status_code == 200 and len(vr.content) > 512,
                f"bytes={len(vr.content)} type={ctype}",
            )
            disk = ROOT / "backend" / "uploads" / "media_factory" / f"{tid}.mp4"
            if disk.is_file():
                log("file_on_disk", True, f"path={disk.name} size={disk.stat().st_size}")
            else:
                log("file_on_disk", False, str(disk))

        report["mock_render"] = mock
        report["cosmos_url_set"] = bool((os.getenv("AI_NVIDIA_COSMOS_BASE_URL") or "").strip())
        report["task_id"] = tid
        report["result_url"] = url

        failed = [s for s in steps if not s["ok"]]
        if mock is True:
            report["verdict"] = "mock_only_pipeline_ok" if not failed else "mock_pipeline_broken"
            report["note"] = (
                "当前为 MOCK 占位视频（色块/短片），非 Cosmos 真实文生视频效果。"
                "要测真实生成：配置 AI_NVIDIA_COSMOS_BASE_URL 并设 MEDIA_FACTORY_MOCK_RENDER=false"
            )
        elif not failed:
            report["verdict"] = "real_render_ok"
        else:
            report["verdict"] = "render_failed"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0 if report["verdict"] in ("mock_only_pipeline_ok", "real_render_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
