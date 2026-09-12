"""NVIDIA Cosmos NIM /v1/infer 客户端（文生视频等）。"""

from __future__ import annotations

import base64
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESOLUTION_PRESETS: dict[str, dict[str, int]] = {
    "1080p": {"height": 704, "width": 1280},
    "720p": {"height": 704, "width": 1280},
    "480p": {"height": 480, "width": 848},
}

ASPECT_PRESETS: dict[str, dict[str, int]] = {
    "16:9": {"height": 704, "width": 1280},
    "9:16": {"height": 1280, "width": 704},
    "1:1": {"height": 704, "width": 704},
}


class CosmosInferError(RuntimeError):
    """Cosmos 推理失败。"""


def infer_base_url() -> str | None:
    """infer_base_url。
    :return: 返回处理结果。
    """
    raw = (settings.AI_NVIDIA_COSMOS_BASE_URL or "").strip().rstrip("/")
    return raw or None


def infer_endpoint_url() -> str | None:
    """infer_endpoint_url。
    :return: 返回处理结果。
    """
    base = infer_base_url()
    if not base:
        return None
    if base.endswith("/v1/infer"):
        return base
    if base.endswith("/v1"):
        return f"{base}/infer"
    return f"{base}/v1/infer"


def script_to_video_prompt(script: str, max_chars: int = 1200) -> str:
    """从分镜脚本提取 Cosmos 文本提示。"""
    text = (script or "").strip()
    if not text:
        return "A short professional product showcase video."

    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("镜头", "Scene", "scene", "【", "#")):
            lines.append(stripped)
        elif "旁白" in stripped or "画面" in stripped:
            lines.append(stripped)
        else:
            lines.append(stripped)
    prompt = " ".join(lines) if lines else text
    if len(prompt) > max_chars:
        prompt = prompt[: max_chars - 3] + "..."
    return prompt


def build_video_params(
    *,
    resolution: str = "1080p",
    aspect: str = "16:9",
    frames_count: int | None = None,
    frames_per_sec: int = 8,
) -> dict[str, int]:
    """build_video_params。

    参数说明：
    :param resolution: 参数 resolution
    :param aspect: 参数 aspect
    :param frames_count: 参数 frames_count
    :param frames_per_sec: 参数 frames_per_sec
    :return: 返回处理结果。
    """
    size = ASPECT_PRESETS.get(aspect) or RESOLUTION_PRESETS.get(resolution) or RESOLUTION_PRESETS["1080p"]
    count = frames_count or int(getattr(settings, "MEDIA_FACTORY_DEFAULT_FRAMES", 33) or 33)
    return {
        "height": size["height"],
        "width": size["width"],
        "frames_count": count,
        "frames_per_sec": frames_per_sec,
    }


def build_infer_payload(
    *,
    prompt: str,
    model: str,
    resolution: str = "1080p",
    aspect: str = "16:9",
    seed: int = 4,
    image_url: str | None = None,
) -> dict[str, Any]:
    """build_infer_payload。

    参数说明：
    :param prompt: 参数 prompt
    :param model: 参数 model
    :param resolution: 参数 resolution
    :param aspect: 参数 aspect
    :param seed: 参数 seed
    :param image_url: 参数 image_url
    :return: 返回处理结果。
    """
    payload: dict[str, Any] = {
        "prompt": prompt,
        "seed": seed,
        "video_params": build_video_params(resolution=resolution, aspect=aspect),
    }
    if model:
        payload["model"] = model
    if image_url:
        payload["image"] = image_url
    return payload


def _auth_headers() -> dict[str, str]:
    """_auth_headers。
    :return: 返回处理结果。
    """
    key = (settings.AI_NVIDIA_API_KEY or "").strip()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def decode_infer_video(response_json: dict[str, Any]) -> bytes:
    """从 Cosmos infer 响应解析视频二进制。"""
    if not response_json:
        raise CosmosInferError("Cosmos 响应为空")

    for key in ("b64_video", "video", "output", "data"):
        value = response_json.get(key)
        if isinstance(value, str) and value.strip():
            try:
                return base64.b64decode(value)
            except Exception as exc:
                raise CosmosInferError(f"无法解码 {key}: {exc}") from exc

    nested = response_json.get("result") or response_json.get("outputs")
    if isinstance(nested, dict):
        return decode_infer_video(nested)
    if isinstance(nested, list) and nested:
        first = nested[0]
        if isinstance(first, dict):
            return decode_infer_video(first)

    raise CosmosInferError(
        "Cosmos 响应中未找到 b64_video 字段。"
        "请确认 AI_NVIDIA_COSMOS_BASE_URL 指向已启动的 Cosmos NIM（/v1/infer）。"
    )


def _mock_video_dimensions(resolution: str = "720p", aspect: str = "16:9") -> tuple[int, int]:
    """_mock_video_dimensions。

    参数说明：
    :param resolution: 参数 resolution
    :param aspect: 参数 aspect
    :return: 返回处理结果。
    """
    preset = ASPECT_PRESETS.get(aspect) or ASPECT_PRESETS["16:9"]
    return int(preset["width"]), int(preset["height"])


def _write_mock_video_ffmpeg(output_path: Path, *, width: int = 640, height: int = 360) -> bool:
    """用 ffmpeg 生成 2 秒可播放占位视频（开发/mock）。"""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"color=c=#1a1a2e:s={width}x{height}:d=2",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        "-shortest",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("ffmpeg mock video failed: %s", exc)
        return False
    return output_path.is_file() and output_path.stat().st_size > 512


def write_mock_video(
    output_path: Path,
    *,
    resolution: str = "720p",
    aspect: str = "16:9",
) -> None:
    """开发/mock 模式：写入可播放的短预览片（优先 ffmpeg）。"""
    width, height = _mock_video_dimensions(resolution, aspect)
    if _write_mock_video_ffmpeg(output_path, width=width, height=height):
        return

    # 无 ffmpeg 时的极小占位（不可播放，仅标记流程成功）
    output_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder = (
        b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
        b"\x00\x00\x00\x08free"
    )
    output_path.write_bytes(placeholder)
    logger.warning(
        "未找到 ffmpeg，mock 视频不可播放（%s bytes）。请安装 ffmpeg 或配置真实 Cosmos NIM。",
        len(placeholder),
    )


def infer_text_to_video(
    *,
    model: str,
    prompt: str,
    resolution: str = "1080p",
    aspect: str = "16:9",
    image_url: str | None = None,
    timeout: float | None = None,
) -> bytes:
    """调用 Cosmos /v1/infer 生成视频字节。"""
    if settings.MEDIA_FACTORY_MOCK_RENDER:
        logger.info("MEDIA_FACTORY_MOCK_RENDER=true，跳过真实 Cosmos 调用")
        return b""

    endpoint = infer_endpoint_url()
    if not endpoint:
        raise CosmosInferError(
            "未配置 Cosmos 推理端点。"
            "请在 backend/config/dev/.env 设置 AI_NVIDIA_COSMOS_BASE_URL"
            "（例如 http://127.0.0.1:8000，对应自托管 Cosmos NIM 的 /v1/infer）。"
            "NVIDIA 托管 catalog 目前不提供 integrate.api.nvidia.com 上的 Cosmos /v1/infer。"
        )

    payload = build_infer_payload(
        prompt=prompt,
        model=model,
        resolution=resolution,
        aspect=aspect,
        image_url=image_url,
    )
    req_timeout = timeout or float(settings.MEDIA_FACTORY_INFER_TIMEOUT or 600)
    logger.info("Cosmos infer -> %s model=%s", endpoint, model)
    try:
        with httpx.Client(timeout=req_timeout) as client:
            response = client.post(endpoint, headers=_auth_headers(), json=payload)
    except httpx.TimeoutException as exc:
        raise CosmosInferError(f"Cosmos 推理超时（{req_timeout}s）") from exc
    except httpx.HTTPError as exc:
        raise CosmosInferError(f"Cosmos 请求失败: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text[:500]
        raise CosmosInferError(f"Cosmos HTTP {response.status_code}: {detail}")

    try:
        data = response.json()
    except ValueError as exc:
        raise CosmosInferError("Cosmos 响应不是 JSON") from exc

    return decode_infer_video(data)
