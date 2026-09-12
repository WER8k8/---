#!/usr/bin/env python3
"""E2E：中文片出海 — 上传 → 听写入队 → SSE/轮询 → 结果。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

API = "http://127.0.0.1:8001"
USERNAME = "tenant"
PASSWORD = "tenant123"
TIMEOUT_SEC = 600
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) YouDingE2E/1.0",
    "Accept": "application/json",
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _ok(resp: requests.Response, step: str) -> dict:
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text[:500]}
    if not resp.ok:
        raise RuntimeError(f"{step} HTTP {resp.status_code}: {body}")
    if isinstance(body, dict) and body.get("code") not in (None, 0):
        raise RuntimeError(f"{step} code={body.get('code')}: {body.get('message')}")
    return body.get("data", body) if isinstance(body, dict) else body


def resolve_executable(name: str) -> str:
    """Resolve CLI on Windows (subprocess often lacks WinGet shim PATH)."""
    found = shutil.which(name)
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    if local.is_file():
        return str(local)
    raise FileNotFoundError(f"{name} not found in PATH or {local}")


def pick_test_mp4() -> Path:
    fixture = Path(__file__).resolve().parent.parent / "backend" / "fixtures" / "dev" / "e2e_test.mp4"
    for candidate in (
        Path(r"C:\Users\97907\Desktop\微信.mp4"),
        Path(__file__).resolve().parent.parent / "微信.mp4",
        fixture,
    ):
        if candidate.is_file() and candidate.stat().st_size > 1000:
            print(f"[OK] use existing video: {candidate} ({candidate.stat().st_size} bytes)")
            return candidate
    return ensure_test_mp4(fixture)


def login() -> str:
    s = _session()
    r = s.post(
        f"{API}/api/v1/auth/login",
        json={"username_or_email": USERNAME, "password": PASSWORD},
        timeout=120,
    )
    data = _ok(r, "login")
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"login missing token: {data}")
    print(f"[OK] login as {USERNAME}")
    return token


def ensure_test_mp4(path: Path) -> Path:
    if path.is_file() and path.stat().st_size > 1000:
        print(f"[OK] use existing video: {path} ({path.stat().st_size} bytes)")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    wav = path.with_suffix(".speech.wav")
    # Windows SAPI 生成中文语音，供 Whisper 识别
    ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SetOutputToWaveFile('{wav.as_posix().replace("'", "''")}')
$s.Speak('你好，这是中文片出海听写测试。')
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        check=True,
        capture_output=True,
        timeout=60,
    )
    if not wav.is_file():
        raise RuntimeError("speech wav generation failed")
    ffmpeg = resolve_executable("ffmpeg")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(wav),
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=320x240:d=4",
        "-shortest",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    try:
        wav.unlink(missing_ok=True)
    except OSError:
        pass
    print(f"[OK] generated speech test mp4: {path} ({path.stat().st_size} bytes)")
    return path


def upload_video(token: str, mp4: Path) -> str:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    with mp4.open("rb") as fh:
        r = s.post(
            f"{API}/api/v1/cross-border/video-dub/upload",
            files={"file": (mp4.name, fh, "video/mp4")},
            timeout=300,
        )
    data = _ok(r, "upload")
    media_id = data.get("media_task_id") or data.get("id")
    if not media_id:
        raise RuntimeError(f"upload missing media_task_id: {data}")
    print(f"[OK] upload media_task_id={media_id}")
    return str(media_id)


def enqueue_transcribe(token: str, media_task_id: str) -> str:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    r = s.post(
        f"{API}/api/v1/cross-border/video-dub/transcribe",
        json={"media_task_id": media_task_id},
        timeout=120,
    )
    data = _ok(r, "transcribe enqueue")
    job_id = data.get("job_id")
    if not job_id:
        raise RuntimeError(f"enqueue missing job_id (raw): {json.dumps(data, ensure_ascii=False)[:500]}")
    print(f"[OK] job queued job_id={job_id} dispatch={data.get('dispatch')}")
    return str(job_id)


def poll_job(token: str, job_id: str) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    started = time.time()
    last_progress = -1
    while time.time() - started < TIMEOUT_SEC:
        r = s.get(
            f"{API}/api/v1/cross-border/video-dub/jobs/{job_id}",
            timeout=120,
        )
        snap = _ok(r, "poll job")
        prog = int(snap.get("progress") or 0)
        status = snap.get("status")
        hint = snap.get("hint") or ""
        if prog != last_progress or status in ("done", "failed"):
            print(f"  .. status={status} progress={prog}% hint={hint[:80]}")
            last_progress = prog
        if status in ("done", "failed"):
            return snap
        time.sleep(2)
    raise RuntimeError("poll timeout")


def try_sse(token: str, job_id: str) -> bool:
    """对已终态任务探测 SSE 路由是否可连（应立刻返回终态）。"""
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Accept"] = "text/event-stream"
    try:
        with s.get(
            f"{API}/api/v1/cross-border/video-dub/jobs/{job_id}/events",
            stream=True,
            timeout=15,
        ) as r:
            if r.status_code != 200:
                print(f"[WARN] SSE HTTP {r.status_code}")
                return False
            chunk = ""
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                chunk += line + "\n"
                if "data:" in line:
                    break
            print(f"[OK] SSE first event received ({len(chunk)} chars)")
            return True
    except Exception as exc:
        print(f"[WARN] SSE probe failed: {exc}")
        return False


def main() -> int:
    mp4 = pick_test_mp4()

    # health（跳过严格检查，直接打登录）
    try:
        h = _session().get(f"{API}/health", timeout=60)
        print(f"[OK] API health HTTP {h.status_code} {h.text[:120]}")
    except Exception as exc:
        print(f"[WARN] health probe: {exc} — continue to login")

    token = login()
    media_id = upload_video(token, mp4)
    job_id = enqueue_transcribe(token, media_id)
    final = poll_job(token, job_id)
    try_sse(token, job_id)

    print("\n=== RESULT ===")
    print(json.dumps(final, ensure_ascii=False, indent=2)[:2000])

    if final.get("status") == "done":
        text = (final.get("text") or (final.get("result") or {}).get("text") or "").strip()
        print(f"\n[PASS] transcribe done, text_len={len(text)}, backend={final.get('backend')}")
        return 0
    print(f"\n[FAIL] job failed: {final.get('error') or final.get('hint')}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
