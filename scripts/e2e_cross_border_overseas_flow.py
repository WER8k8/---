#!/usr/bin/env python3
"""MS-F E2E：出海 → 剪辑台项目 → 分发 handoff 探针。

流程：登录 → 上传 → 一键出海（带中文稿，跳过听写）→ 轮询 → 保存 studio project
     → 读取 project 校验 segments/srt → capabilities 探针。

需本地 API :8001 与 LLM 配置；配音模式另需 edge-tts+ffmpeg。
默认 output_mode=subtitle 以降低环境依赖（至少产出 srt + segments）。
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
SAMPLE_SCRIPT_EN = (
    "Hello everyone, this is our factory's exterior wall insulation decorative panel, "
    "with A1 fire rating, suitable for export projects."
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 YouDingOverseasFlowE2E/1.0",
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
        raise RuntimeError("login: no access_token")
    return token


def upload_minimal_mp4(token: str) -> str:
    """复用 transcribe e2e 的 fixture 逻辑。"""
    from e2e_cross_border_transcribe import pick_test_mp4, upload_video

    mp4 = pick_test_mp4()
    return upload_video(token, mp4)


def enqueue_dub(token: str, media_task_id: str) -> str:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    r = s.post(
        f"{API}/api/v1/cross-border/video-dub/jobs",
        json={
            "media_task_id": media_task_id,
            "transcript_zh": SAMPLE_ZH,
            "voice_consent": False,
            "output_mode": "subtitle",
            "track": "standard",
        },
        timeout=120,
    )
    data = _ok(r, "dub enqueue")
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
        r = s.get(f"{API}/api/v1/cross-border/video-dub/jobs/{job_id}", timeout=120)
        snap = _ok(r, "poll")
        status = snap.get("status")
        if status in ("done", "failed"):
            return snap
        time.sleep(2)
    raise RuntimeError("poll timeout")


def save_studio_project(token: str, media_task_id: str, body: dict) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    r = s.post(
        f"{API}/api/v1/cross-border/media-studio/projects/{media_task_id}",
        json=body,
        timeout=60,
    )
    return _ok(r, "save studio project")


def get_studio_project(token: str, media_task_id: str) -> dict:
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    r = s.get(
        f"{API}/api/v1/cross-border/media-studio/projects/{media_task_id}",
        timeout=60,
    )
    return _ok(r, "get studio project")


def probe_distribute_tenant_site(token: str, media_task_id: str) -> dict:
    """仅登记租户官网，不选外站（避免无 Worker 时假成功）。"""
    s = _session()
    s.headers["Authorization"] = f"Bearer {token}"
    r = s.post(
        f"{API}/api/v1/publish/video/distribute",
        json={
            "media_task_id": media_task_id,
            "platform_ids": [],
            "include_tenant_site": True,
        },
        timeout=120,
    )
    return _ok(r, "distribute tenant site")


def main() -> int:
    token = login()
    print("[OK] login")

    media_id = upload_minimal_mp4(token)
    job_id = enqueue_dub(token, media_id)
    final = poll_job(token, job_id)

    print("\n=== DUB RESULT ===")
    print(json.dumps(final, ensure_ascii=False, indent=2)[:2500])

    if final.get("status") != "done":
        print(f"\n[FAIL] dub job: {final.get('error') or final.get('hint')}")
        return 1

    result = final.get("result") if isinstance(final.get("result"), dict) else final
    srt_url = result.get("srt_url")
    segments = result.get("segments") or []
    script_en = result.get("script_en") or ""

    if not srt_url:
        print("[FAIL] no srt_url in dub result")
        return 1

    saved = save_studio_project(
        token,
        media_id,
        {
            "transcript_zh": result.get("transcript_zh") or SAMPLE_ZH,
            "script_en": script_en,
            "srt_url": srt_url,
            "segments": segments,
            "output_url": result.get("output_url"),
            "asr_backend": (result.get("asr") or {}).get("backend"),
        },
    )
    loaded = get_studio_project(token, media_id)
    proj = loaded.get("project") or {}
    if not proj.get("srt_url"):
        print("[FAIL] studio project missing srt_url after save")
        return 1
    if not isinstance(proj.get("segments"), list):
        print("[WARN] segments not persisted as list")

    cap = _ok(
        _session()
        .get(
            f"{API}/api/v1/cross-border/media-studio/capabilities",
            headers={**HEADERS, "Authorization": f"Bearer {token}"},
            timeout=30,
        ),
        "capabilities",
    )
    assert cap.get("product_id") == "CROSS-BORDER-MEDIA-STUDIO-01"

    dist = probe_distribute_tenant_site(token, media_id)
    tenant_site = dist.get("tenant_site") or {}
    if not tenant_site.get("published"):
        print(f"[FAIL] distribute tenant_site: {tenant_site.get('reason')}")
        return 1
    if not dist.get("publish_video_url"):
        print("[FAIL] distribute missing publish_video_url")
        return 1
    print(f"[OK] distribute tenant_site published, url={dist.get('publish_video_url')[:80]}")

    print(f"\n[PASS] overseas flow: media_task_id={media_id}")
    print(f"  srt_url={srt_url}")
    print(f"  segments={len(segments) if isinstance(segments, list) else 0}")
    print(f"  handoff_url=/client/distribute?media_task_id={media_id}")
    return 0


if __name__ == "__main__":
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
