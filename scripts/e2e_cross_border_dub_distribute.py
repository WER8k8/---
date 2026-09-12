#!/usr/bin/env python3
"""MS-F E2E：英文配音出海 + 租户官网分发探针。

流程：登录 → 上传 → 出海（output_mode=dub + voice_consent）→ 轮询
     → 校验 output_url / edited_result_url → 保存 studio project
     → POST /publish/video/distribute（仅 include_tenant_site，无外站真发）

前置：edge-tts + ffmpeg（WinGet 安装即可）；缺依赖时 exit 2（blocked，非假通过）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

API = "http://127.0.0.1:8001"
USERNAME = "tenant"
PASSWORD = "tenant123"
TIMEOUT_SEC = 600
SAMPLE_ZH = "大家好，这是我们工厂的外墙保温装饰一体板，防火等级 A1，适合出口工程采购。"

HEADERS = {
    "User-Agent": "Mozilla/5.0 YouDingDubDistributeE2E/1.0",
    "Accept": "application/json",
}

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
UPLOADS = BACKEND / "uploads"


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


def _blocked(msg: str) -> int:
    print(f"[BLOCKED] {msg}", file=sys.stderr)
    return 2


def _ffmpeg_available() -> bool:
    import os
    import subprocess

    env_path = (os.environ.get("FFMPEG_PATH") or "").strip()
    if env_path and Path(env_path).exists():
        return True

    sys.path.insert(0, str(BACKEND))
    from app.core.executable_resolver import is_executable_available

    if is_executable_available("ffmpeg"):
        return True

    try:
        proc = subprocess.run(
            ["where", "ffmpeg"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0 and (proc.stdout or "").strip():
            line = proc.stdout.strip().splitlines()[0].strip()
            os.environ["FFMPEG_PATH"] = line
            return True
    except Exception:
        pass
    return False


def check_dub_prerequisites() -> str | None:
    """返回 None 表示可跑；否则为 blocked 原因。"""
    if not _ffmpeg_available():
        return "ffmpeg 未安装或子进程 PATH 不可见（WinGet: winget install Gyan.FFmpeg）"
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return "edge-tts 未安装（pip install -U 'edge-tts>=7.2.7'）"
    return None


def login() -> str:
    data = _ok(
        _session().post(
            f"{API}/api/v1/auth/login",
            json={"username_or_email": USERNAME, "password": PASSWORD},
            timeout=120,
        ),
        "login",
    )
    token = data.get("access_token")
    if not token:
        raise RuntimeError("login: no access_token")
    return token


def upload_minimal_mp4(token: str) -> str:
    from e2e_cross_border_transcribe import pick_test_mp4, upload_video

    return upload_video(token, pick_test_mp4())


def enqueue_dub(token: str, media_task_id: str) -> str:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    data = _ok(
        s.post(
            f"{API}/api/v1/cross-border/video-dub/jobs",
            json={
                "media_task_id": media_task_id,
                "transcript_zh": SAMPLE_ZH,
                "voice_consent": True,
                "output_mode": "dub",
                "track": "standard",
            },
            timeout=120,
        ),
        "dub enqueue",
    )
    job_id = data.get("job_id")
    if not job_id:
        raise RuntimeError(f"dub enqueue missing job_id: {data}")
    print(f"[OK] dub job_id={job_id}")
    return str(job_id)


def poll_job(token: str, job_id: str) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    started = time.time()
    while time.time() - started < TIMEOUT_SEC:
        snap = _ok(
            s.get(f"{API}/api/v1/cross-border/video-dub/jobs/{job_id}", timeout=120),
            "poll",
        )
        status = snap.get("status")
        if status in ("done", "failed"):
            return snap
        time.sleep(2)
    raise RuntimeError("poll timeout")


def save_studio_project(token: str, media_task_id: str, body: dict) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    return _ok(
        s.post(
            f"{API}/api/v1/cross-border/media-studio/projects/{media_task_id}",
            json=body,
            timeout=60,
        ),
        "save studio project",
    )


def get_studio_project(token: str, media_task_id: str) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    return _ok(
        s.get(
            f"{API}/api/v1/cross-border/media-studio/projects/{media_task_id}",
            timeout=60,
        ),
        "get studio project",
    )


def probe_distribute_tenant_site(token: str, media_task_id: str) -> dict:
    """仅登记租户官网，不选外站（避免无 Worker 时假成功）。"""
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    return _ok(
        s.post(
            f"{API}/api/v1/publish/video/distribute",
            json={
                "media_task_id": media_task_id,
                "platform_ids": [],
                "include_tenant_site": True,
            },
            timeout=120,
        ),
        "distribute tenant site",
    )


def _local_upload_path(url: str | None) -> Path | None:
    if not url or not url.startswith("/uploads/"):
        return None
    rel = url.removeprefix("/uploads/").replace("/", "\\")
    path = UPLOADS / rel
    return path if path.is_file() and path.stat().st_size > 1000 else None


def main() -> int:
    blocked = check_dub_prerequisites()
    if blocked:
        return _blocked(blocked)

    token = login()
    print("[OK] login")

    media_id = upload_minimal_mp4(token)
    job_id = enqueue_dub(token, media_id)
    final = poll_job(token, job_id)

    print("\n=== DUB RESULT ===")
    print(json.dumps(final, ensure_ascii=False, indent=2)[:3000])

    if final.get("status") != "done":
        print(f"\n[FAIL] dub job: {final.get('error') or final.get('hint')}")
        return 1

    result = final.get("result") if isinstance(final.get("result"), dict) else final
    output_url = result.get("output_url")
    output_mode = result.get("output_mode") or ""
    srt_url = result.get("srt_url")
    segments = result.get("segments") or []
    script_en = result.get("script_en") or ""

    if output_mode != "english_dub":
        print(f"[FAIL] expected output_mode=english_dub, got {output_mode!r}")
        print(f"  hint={result.get('hint')}")
        return 1
    if not output_url:
        print("[FAIL] dub mode done but no output_url")
        return 1

    local_mp4 = _local_upload_path(output_url)
    if not local_mp4:
        print(f"[FAIL] output_url not found on disk: {output_url}")
        return 1
    print(f"[OK] dubbed mp4 on disk: {local_mp4} ({local_mp4.stat().st_size} bytes)")

    save_studio_project(
        token,
        media_id,
        {
            "transcript_zh": result.get("transcript_zh") or SAMPLE_ZH,
            "script_en": script_en,
            "srt_url": srt_url,
            "segments": segments,
            "output_url": output_url,
            "asr_backend": (result.get("asr") or {}).get("backend"),
        },
    )
    loaded = get_studio_project(token, media_id)
    proj = loaded.get("project") or {}
    if proj.get("output_url") != output_url:
        print("[FAIL] studio project output_url mismatch after save")
        return 1

    dist = probe_distribute_tenant_site(token, media_id)
    tenant_site = dist.get("tenant_site") or {}
    publish_url = dist.get("publish_video_url") or ""

    print("\n=== DISTRIBUTE PROBE ===")
    print(json.dumps(
        {
            "publish_video_url": publish_url,
            "tenant_site": tenant_site,
            "message": dist.get("message"),
            "summary": dist.get("summary"),
        },
        ensure_ascii=False,
        indent=2,
    )[:2000])

    if not tenant_site.get("published"):
        print(f"[FAIL] tenant_site not published: {tenant_site.get('reason')}")
        return 1
    if not publish_url:
        print("[FAIL] distribute returned empty publish_video_url")
        return 1

    print(f"\n[PASS] dub+distribute: media_task_id={media_id}")
    print(f"  output_url={output_url}")
    print(f"  publish_video_url={publish_url}")
    print(f"  tenant_landing={dist.get('tenant_landing_url')}")
    return 0


if __name__ == "__main__":
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
