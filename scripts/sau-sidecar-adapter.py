#!/usr/bin/env python3
"""SAU HTTP Sidecar — 在 Worker 机执行 social-auto-upload CLI。

启动:
  python scripts/sau-sidecar-adapter.py --port 9910

环境:
  SAU_CLI_PATH / PATH 中的 sau
  SAU_HOME — Cookie 目录
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()

PLATFORM_TO_SAU = {
    "抖音": "douyin",
    "快手": "kuaishou",
    "哔哩哔哩": "bilibili",
    "小红书": "xiaohongshu",
    "微信视频号": "tencent",
    "TikTok": "tiktok",
}


def _sau_cli() -> str:
    custom = (os.environ.get("SAU_CLI_PATH") or "").strip()
    if custom:
        return custom
    for name in ("sau", "sau.exe"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def _run_sau(args: list[str], *, timeout: int = 900) -> tuple[int, str, str]:
    cli = _sau_cli()
    if not cli:
        raise RuntimeError("sau CLI not found")
    env = os.environ.copy()
    home = (os.environ.get("SAU_HOME") or "").strip()
    if home:
        env["SAU_HOME"] = home
    proc = subprocess.run(
        [cli, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _download(url: str, dest: Path) -> None:
    with httpx.Client(timeout=300, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def _extract_url(text: str) -> str:
    for pat in (
        r"https?://(?:www\.)?bilibili\.com/video/BV[\w]+",
        r"https?://(?:www\.)?douyin\.com/video/\d+",
        r"https?://v\.douyin\.com/[\w/-]+",
        r"https?://(?:www\.)?kuaishou\.com/short-video/[\w-]+",
        r"https?://(?:www\.)?xiaohongshu\.com/explore/[\w]+",
    ):
        m = re.search(pat, text, re.I)
        if m:
            return m.group(0)
    m = re.search(r"\b(BV[\w]{10})\b", text)
    if m:
        return f"https://www.bilibili.com/video/{m.group(1)}"
    return ""


def _execute_job(job_id: str, payload: dict[str, Any]) -> None:
    with _LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        platform = payload.get("platform_name") or ""
        sau_plat = PLATFORM_TO_SAU.get(platform)
        if not sau_plat:
            raise RuntimeError(f"unsupported platform {platform}")
        account = payload.get("account") or ""
        mode = str(payload.get("mode") or "video")
        tmp = Path(os.environ.get("SAU_SIDECAR_TMP", "/tmp/sau-sidecar"))
        tmp.mkdir(parents=True, exist_ok=True)

        args: list[str]
        if mode == "note":
            images = []
            for p in payload.get("image_paths") or []:
                images.append(Path(p))
            if not images and payload.get("image_urls"):
                for i, url in enumerate(payload["image_urls"][:9]):
                    dest = tmp / f"{job_id}_{i}.jpg"
                    _download(url, dest)
                    images.append(dest)
            if not images:
                raise RuntimeError("note mode requires images")
            args = [sau_plat, "upload-note", "--account", account, "--title", payload.get("title") or "图文"]
            for img in images:
                args.extend(["--images", str(img)])
            args.extend(["--note", payload.get("desc") or ""])
        else:
            video = payload.get("video_path")
            if not video and payload.get("video_url"):
                dest = tmp / f"{job_id}.mp4"
                _download(payload["video_url"], dest)
                video = str(dest)
            if not video:
                raise RuntimeError("video mode requires video_path or video_url")
            args = [
                sau_plat,
                "upload-video",
                "--account",
                account,
                "--file",
                str(video),
                "--title",
                payload.get("title") or "视频",
                "--desc",
                payload.get("desc") or "",
            ]
            cover = payload.get("cover_path")
            if not cover and payload.get("cover_url"):
                cdest = tmp / f"{job_id}_cover.jpg"
                _download(payload["cover_url"], cdest)
                cover = str(cdest)
            if cover:
                args.extend(["--thumbnail", str(cover)])
            if sau_plat == "bilibili":
                args.extend(["--tid", str(payload.get("bilibili_tid") or 249)])

        tags = payload.get("tags") or []
        if tags:
            args.extend(["--tags", ",".join(str(t) for t in tags[:10])])
        schedule = payload.get("schedule")
        if schedule:
            args.extend(["--schedule", str(schedule)])

        code, out, err = _run_sau(args)
        merged = f"{out}\n{err}"
        post_url = _extract_url(merged)
        result: dict[str, Any] = {
            "exit_code": code,
            "raw_output": merged[:4000],
            "platform_post_url": post_url,
            "success": False,
        }
        if code != 0:
            result["error_message"] = (err or out or "sau failed")[:500]
        elif schedule and not post_url:
            result["pending"] = True
            result["publish_state"] = "scheduled"
            result["scheduled_at"] = schedule
        elif post_url:
            result["success"] = True
        else:
            result["error_message"] = "no verifiable post url"
        with _LOCK:
            _JOBS[job_id]["status"] = "done"
            _JOBS[job_id]["result"] = result
    except Exception as exc:
        with _LOCK:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = str(exc)[:500]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, code: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:
        if self.path == "/api/youding/health":
            self._json(
                200,
                {
                    "ok": True,
                    "mode": "production",
                    "produces_output": True,
                    "service": "sau-sidecar",
                    "sau_cli": bool(_sau_cli()),
                },
            )
            return
        if self.path.startswith("/api/youding/sau/jobs/"):
            job_id = self.path.rsplit("/", 1)[-1]
            with _LOCK:
                job = _JOBS.get(job_id)
            if not job:
                self._json(404, {"error": "job_not_found"})
                return
            self._json(200, job)
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/api/youding/sau/check":
            body = self._read_json()
            platform = body.get("platform_name") or ""
            account = body.get("account") or ""
            sau_plat = PLATFORM_TO_SAU.get(platform)
            if not sau_plat:
                self._json(400, {"ok": False, "reason": "bad_platform"})
                return
            try:
                code, out, err = _run_sau([sau_plat, "check", "--account", account], timeout=60)
                merged = f"{out}\n{err}"
                ok = code == 0 and ("有效" in merged or "valid" in merged.lower())
                self._json(200, {"ok": ok, "exit_code": code, "output": merged[:500]})
            except Exception as exc:
                self._json(200, {"ok": False, "reason": str(exc)})
            return

        if self.path == "/api/youding/sau/publish":
            body = self._read_json()
            job_id = uuid.uuid4().hex
            with _LOCK:
                _JOBS[job_id] = {"job_id": job_id, "status": "queued", "created_at": time.time()}
            threading.Thread(target=_execute_job, args=(job_id, body), daemon=True).start()
            self._json(202, {"job_id": job_id, "status": "queued"})
            return

        self._json(404, {"error": "not_found"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9910)
    args = parser.parse_args()
    if not _sau_cli():
        print("WARN: sau CLI not found; set SAU_CLI_PATH")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"SAU sidecar http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
