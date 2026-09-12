"""开源精品轨执行器 — 统一 sidecar 契约或 KrillinAI CLI；未配置则明确失败。"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

import httpx

from app.core.config import settings
from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir
from app.services.cross_border.opensource_localization_registry import (
    pick_active_opensource_provider,
)
from app.services.cross_border.video_dub_service import _resolve_media_source_path

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None] | None

SIDECAR_SUBMIT_PATH = "/api/youding/translate-dub"
SIDECAR_JOB_PATH = "/api/youding/jobs/{job_id}"
SIDECAR_HEALTH_PATH = "/api/youding/health"

_SIDEcar_PROVIDER_BASE_ENV: dict[str, str] = {
    "linly_dubbing": "LINLY_DUBBING_BASE_URL",
    "youdub_webui": "YOUDUB_WEBUI_BASE_URL",
    "v2vt": "V2VT_SERVICE_URL",
    "videolingo": "VIDEOLINGO_BASE_URL",
    "narrator_ai": "NARRATOR_AI_BASE_URL",
    "pyvideotrans": "PYVIDEOTRANS_BASE_URL",
    "musetalk": "MUSETALK_SERVICE_URL",
}


def _env_str(name: str) -> str:
    """实现 envstr 的功能。
    
    :param name: 参数 name（类型: str）
    :return: 返回 str 结果
    """
    return (getattr(settings, name, None) or "").strip().rstrip("/")


def _public_base_url() -> str:
    """实现 publicbaseURL 的功能。
    
    :return: 返回 str 结果
    """
    raw = _env_str("CROSS_BORDER_PUBLIC_BASE_URL") or "http://127.0.0.1:8001"
    return raw.rstrip("/")


def _provider_base_url(provider_id: str) -> str:
    """实现 提供商baseURL 的功能。
    
    :param provider_id: 参数 provider_id（类型: str）
    :return: 返回 str 结果
    """
    if provider_id == "krillinai":
        return _env_str("KRILLINAI_SERVICE_URL")
    env_name = _SIDEcar_PROVIDER_BASE_ENV.get(provider_id, "")
    return _env_str(env_name) if env_name else ""


def _build_video_public_url(result_url: str | None) -> str | None:
    """实现 构建视频publicURL 的功能。
    
    :param result_url: 参数 result_url（类型: str | None）
    :return: 返回 str | None 结果
    """
    if not result_url:
        return None
    part = result_url.split("?", 1)[0]
    if part.startswith(("http://", "https://")):
        return part
    if part.startswith("/"):
        return f"{_public_base_url()}{part}"
    return f"{_public_base_url()}/{part.lstrip('/')}"


def _normalize_asset_url(url: str | None) -> str | None:
    """实现 normalizeassetURL 的功能。
    
    :param url: 参数 url（类型: str | None）
    :return: 返回 str | None 结果
    """
    if not url or not str(url).strip():
        return None
    raw = str(url).strip()
    if raw.startswith("/uploads/"):
        return raw
    parsed = urlparse(raw)
    if parsed.path.startswith("/uploads/"):
        return parsed.path
    return raw


async def _import_remote_asset(url: str, prefix: str) -> str | None:
    """将 sidecar 返回的 http(s) 或本地路径资产落到 /uploads。"""
    if not url:
        return None
    local = _normalize_asset_url(url)
    if local and local.startswith("/uploads/"):
        target = UPLOADS_DIR / local.removeprefix("/uploads/")
        if target.is_file():
            return local

    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        suffix = Path(parsed.path).suffix or ".bin"
        ensure_uploads_dir()
        out = UPLOADS_DIR / f"{prefix}_{uuid.uuid4().hex[:10]}{suffix}"
        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                out.write_bytes(resp.content)
            return f"/uploads/{out.name}"
        except Exception as exc:
            logger.warning("import remote asset failed %s: %s", url, exc)
            return url if url.startswith("/") else None

    path = Path(url)
    if path.is_file():
        ensure_uploads_dir()
        dest = UPLOADS_DIR / f"{prefix}_{uuid.uuid4().hex[:10]}{path.suffix or '.bin'}"
        shutil.copy2(path, dest)
        return f"/uploads/{dest.name}"
    return None


async def _poll_sidecar_job(
    base: str,
    job_id: str,
    *,
    on_progress: ProgressFn = None,
    timeout_sec: int = 1800,
    poll_interval: float = 3.0,
) -> dict[str, Any]:
    """实现 pollsidecar任务 的功能。
    
    :param base: 参数 base（类型: str）
    :param job_id: 参数 job_id（类型: str）
    :param on_progress: 参数 on_progress（类型: ProgressFn）
    :param timeout_sec: 参数 timeout_sec（类型: int）
    :param poll_interval: 参数 poll_interval（类型: float）
    :return: 返回 dict[str, Any] 结果
    """
    url = urljoin(base + "/", SIDECAR_JOB_PATH.format(job_id=job_id))
    elapsed = 0.0
    last_hint = ""
    async with httpx.AsyncClient(timeout=120) as client:
        while elapsed <= timeout_sec:
            resp = await client.get(url)
            if resp.status_code == 404:
                return {
                    "ok": False,
                    "error_code": "SIDECAR_JOB_NOT_FOUND",
                    "hint": f"sidecar 未找到任务 {job_id}",
                }
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                return {"ok": False, "error_code": "SIDECAR_BAD_RESPONSE", "hint": "sidecar 响应非 JSON 对象"}
            status = str(data.get("status") or "").lower()
            progress = int(data.get("progress") or 0)
            hint = str(data.get("hint") or data.get("message") or "")
            if hint and hint != last_hint and on_progress:
                on_progress(max(10, min(90, progress)), hint)
                last_hint = hint
            if status in ("done", "success", "completed"):
                result = data.get("result") if isinstance(data.get("result"), dict) else data
                return {"ok": True, "result": result, "sidecar_status": status}
            if status in ("failed", "error", "cancelled"):
                return {
                    "ok": False,
                    "error_code": "SIDECAR_JOB_FAILED",
                    "hint": hint or data.get("error") or "sidecar 任务失败",
                }
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
    return {"ok": False, "error_code": "SIDECAR_TIMEOUT", "hint": "sidecar 任务超时"}


async def _run_sidecar_http(
    provider: dict[str, Any],
    *,
    video_public_url: str,
    source_path: Path | None,
    lip_sync: bool,
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """实现 执行sidecarHTTP 的功能。
    
    :param provider: 参数 provider（类型: dict[str, Any]）
    :param video_public_url: 参数 video_public_url（类型: str）
    :param source_path: 参数 source_path（类型: Path | None）
    :param lip_sync: 参数 lip_sync（类型: bool）
    :param on_progress: 参数 on_progress（类型: ProgressFn）
    :return: 返回 dict[str, Any] 结果
    """
    base = _provider_base_url(provider["id"])
    if not base:
        return {
            "ok": False,
            "error_code": "OPENSOURCE_NOT_CONFIGURED",
            "hint": provider.get("access_note") or "未配置 sidecar URL",
        }

    submit_url = urljoin(base + "/", SIDECAR_SUBMIT_PATH.lstrip("/"))
    payload = {
        "video_url": video_public_url,
        "source_lang": "zh",
        "target_lang": "en",
        "lip_sync": lip_sync,
        "provider_id": provider["id"],
    }
    if on_progress:
        on_progress(8, f"提交 {provider['label']}…")

    async with httpx.AsyncClient(timeout=300) as client:
        resp = None
        if source_path and source_path.is_file():
            with source_path.open("rb") as fh:
                files = {"file": (source_path.name, fh, "video/mp4")}
                resp = await client.post(submit_url, data=payload, files=files)
        if resp is None or resp.status_code == 415:
            resp = await client.post(submit_url, json=payload)

        if resp.status_code in (404, 405):
            return {
                "ok": False,
                "error_code": "SIDECAR_CONTRACT_MISSING",
                "hint": (
                    f"sidecar 未实现 {SIDECAR_SUBMIT_PATH}；"
                    "请部署 YouDing 统一适配层，见 .project/opensource-sidecar-contract.json"
                ),
            }
        if resp.status_code >= 500:
            return {
                "ok": False,
                "error_code": "SIDECAR_UNAVAILABLE",
                "hint": f"sidecar 返回 HTTP {resp.status_code}",
            }
        if resp.status_code not in (200, 201, 202):
            body = resp.text[:300]
            return {
                "ok": False,
                "error_code": "SIDECAR_REJECTED",
                "hint": f"sidecar 拒绝任务 HTTP {resp.status_code}: {body}",
            }
        data = resp.json() if resp.content else {}
        if not isinstance(data, dict):
            return {"ok": False, "error_code": "SIDECAR_BAD_RESPONSE", "hint": "提交响应无效"}

        if data.get("ok") is False or data.get("success") is False:
            return {
                "ok": False,
                "error_code": data.get("error_code") or "SIDECAR_REJECTED",
                "hint": data.get("hint") or data.get("error") or "sidecar 未接受任务",
            }

        job_id = data.get("job_id") or data.get("id")
        if job_id:
            polled = await _poll_sidecar_job(base, str(job_id), on_progress=on_progress)
            if not polled.get("ok"):
                return polled
            raw = polled.get("result") or {}
        else:
            raw = data.get("result") if isinstance(data.get("result"), dict) else data

    return await _normalize_sidecar_result(raw, provider)


async def _normalize_sidecar_result(
    raw: dict[str, Any],
    provider: dict[str, Any],
) -> dict[str, Any]:
    """实现 normalizesidecar结果 的功能。
    
    :param raw: 参数 raw（类型: dict[str, Any]）
    :param provider: 参数 provider（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    output_url = await _import_remote_asset(
        str(raw.get("output_url") or raw.get("video_url") or ""),
        "premium",
    )
    srt_url = await _import_remote_asset(
        str(raw.get("srt_url") or ""),
        "premium_srt",
    )
    audio_url = await _import_remote_asset(
        str(raw.get("audio_url") or ""),
        "premium_audio",
    )
    if not output_url and not srt_url:
        return {
            "ok": False,
            "error_code": "SIDECAR_NO_OUTPUT",
            "hint": "sidecar 未返回 output_url 或 srt_url，禁止假成功",
            "localization_provider": provider["id"],
            "mode": "opensource",
        }

    output_mode = str(raw.get("output_mode") or "")
    if output_url and provider.get("lip_sync"):
        output_mode = output_mode or "opensource_lip_dub"
    elif output_url:
        output_mode = output_mode or "opensource_dub"
    else:
        output_mode = output_mode or "srt_only"

    return {
        "ok": True,
        "transcript_zh": raw.get("transcript_zh"),
        "script_en": raw.get("script_en"),
        "srt_url": srt_url,
        "output_url": output_url,
        "audio_url": audio_url,
        "output_mode": output_mode,
        "localization_provider": provider["id"],
        "localization_mode": "opensource",
        "lip_sync": bool(provider.get("lip_sync")),
        "voice_clone": bool(provider.get("voice_clone")),
        "human_confirm_required": True,
        "hint": raw.get("hint")
        or (
            f"已通过 {provider['label']} 生成精品出海成片，发送前请人工听看核对。"
            if output_url
            else "已生成精品字幕，画面未合成。"
        ),
    }


def _run_krillinai_cli(
    *,
    source_path: Path,
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """实现 执行krillinaicli 的功能。
    
    :param source_path: 参数 source_path（类型: Path）
    :param on_progress: 参数 on_progress（类型: ProgressFn）
    :return: 返回 dict[str, Any] 结果
    """
    cli = _env_str("KRILLINAI_CLI_PATH")
    if not cli:
        for name in ("KrillinAI-cli", "KrillinAI"):
            found = shutil.which(name)
            if found:
                cli = found
                break
    if not cli:
        return {
            "ok": False,
            "error_code": "KRILLINAI_NOT_CONFIGURED",
            "hint": "配置 KRILLINAI_CLI_PATH 或 KRILLINAI_SERVICE_URL",
        }
    resolved = cli if Path(cli).is_file() else shutil.which(cli)
    if not resolved:
        return {
            "ok": False,
            "error_code": "KRILLINAI_NOT_CONFIGURED",
            "hint": "配置 KRILLINAI_CLI_PATH 或 KRILLINAI_SERVICE_URL",
        }
    cli = resolved
    out_dir = UPLOADS_DIR / f"krillin_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if on_progress:
        on_progress(15, "KrillinAI CLI 处理中…")

    cmd = [
        cli,
        "pipeline",
        "--input",
        str(source_path),
        "--source-lang",
        "zh",
        "--target-lang",
        "en",
        "--output-dir",
        str(out_dir),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error_code": "KRILLINAI_TIMEOUT", "hint": "KrillinAI CLI 超时"}
    except OSError as exc:
        return {"ok": False, "error_code": "KRILLINAI_EXEC_FAILED", "hint": str(exc)}

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[:500]
        return {
            "ok": False,
            "error_code": "KRILLINAI_FAILED",
            "hint": err or f"KrillinAI 退出码 {proc.returncode}",
        }

    mp4_candidates = sorted(out_dir.glob("**/*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    srt_candidates = sorted(out_dir.glob("**/*.srt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp4_candidates and not srt_candidates:
        return {
            "ok": False,
            "error_code": "KRILLINAI_NO_OUTPUT",
            "hint": "KrillinAI 未产出 mp4/srt",
        }

    output_url = None
    srt_url = None
    if mp4_candidates:
        dest = UPLOADS_DIR / f"krillin_{uuid.uuid4().hex[:10]}.mp4"
        shutil.copy2(mp4_candidates[0], dest)
        output_url = f"/uploads/{dest.name}"
    if srt_candidates:
        dest = UPLOADS_DIR / f"krillin_{uuid.uuid4().hex[:10]}.srt"
        shutil.copy2(srt_candidates[0], dest)
        srt_url = f"/uploads/{dest.name}"

    return {
        "ok": True,
        "output_url": output_url,
        "srt_url": srt_url,
        "output_mode": "opensource_dub" if output_url else "srt_only",
        "localization_provider": "krillinai",
        "localization_mode": "opensource_cli",
        "human_confirm_required": True,
        "hint": "KrillinAI 已生成出海成片，发送前请人工核对。",
    }


async def run_opensource_premium_job(
    *,
    result_url: str | None,
    provider_id: str | None = None,
    on_progress: ProgressFn = None,
) -> dict[str, Any]:
    """执行开源精品轨；无配置或 sidecar 失败时 ok=false。"""
    provider = pick_active_opensource_provider(provider_id)
    if not provider:
        return {
            "ok": False,
            "error_code": "OPENSOURCE_NOT_CONFIGURED",
            "hint": (
                "未部署开源精品 sidecar。请配置 LINLY_DUBBING_BASE_URL 或 YOUDUB_WEBUI_BASE_URL 等，"
                "见剪辑台「智能推荐栈」。"
            ),
        }

    source_path, temp_path = _resolve_media_source_path(result_url)
    try:
        if provider["id"] == "krillinai" and source_path:
            return await asyncio.to_thread(
                _run_krillinai_cli,
                source_path=source_path,
                on_progress=on_progress,
            )

        video_public = _build_video_public_url(result_url)
        if not video_public and not source_path:
            return {
                "ok": False,
                "error_code": "VIDEO_SOURCE_MISSING",
                "hint": "找不到可提交给 sidecar 的视频地址",
            }

        return await _run_sidecar_http(
            provider,
            video_public_url=video_public or "",
            source_path=source_path,
            lip_sync=bool(provider.get("lip_sync")),
            on_progress=on_progress,
        )
    finally:
        if temp_path and temp_path.is_file():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
