"""Probe NVIDIA Cosmos hosted infer endpoints (dev only)."""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "config/dev/.env", override=True)

KEY = os.getenv("AI_NVIDIA_API_KEY", "")
HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
PAYLOAD = {
    "prompt": "A short clip of lightweight concrete blocks on a construction site.",
    "seed": 4,
    "video_params": {"height": 704, "width": 1280, "frames_count": 33, "frames_per_sec": 8},
}


def probe(method: str, url: str, body: dict | None = None) -> None:
    try:
        if method == "POST":
            r = httpx.post(url, headers=HEADERS, json=body, timeout=45)
        else:
            r = httpx.get(url, headers=HEADERS, timeout=45)
        text = r.text[:240].replace("\n", " ")
        logger.info('{method} {url} -> {r.status_code} {text}', method, url, r.status_code, text)
    except Exception as exc:
        logger.info('{method} {url} -> ERR {exc}', method, url, exc)


def main() -> None:
    model = "nvidia/cosmos-predict1-5b"
    candidates = [
        ("POST", f"https://integrate.api.nvidia.com/v1/{model}/infer", PAYLOAD),
        ("POST", "https://integrate.api.nvidia.com/v1/infer", {**PAYLOAD, "model": model}),
        ("POST", f"https://ai.api.nvidia.com/v1/gen/{model}/infer", PAYLOAD),
        ("POST", f"https://ai.api.nvidia.com/v1/gen/{model}", PAYLOAD),
        ("POST", "https://ai.api.nvidia.com/v1/infer", {**PAYLOAD, "model": model}),
        ("POST", f"https://ai.api.nvidia.com/v1/{model}/infer", PAYLOAD),
    ]
    for method, url, body in candidates:
        probe(method, url, body)

    page = httpx.get(
        "https://build.nvidia.com/nvidia/cosmos-predict1-5b",
        headers={"Authorization": f"Bearer {KEY}", "Accept": "text/html"},
        timeout=45,
        follow_redirects=True,
    )
    logger.info('"build page status", page.status_code, "len", len(page.text)')
    for pattern in (
        r"https://ai\.api\.nvidia\.com[^\"'\s<>\\]+",
        r"https://integrate\.api\.nvidia\.com[^\"'\s<>\\]+",
        r"https://api\.nvcf\.nvidia\.com[^\"'\s<>\\]+",
    ):
        hits = sorted(set(re.findall(pattern, page.text)))
        logger.info('pattern {pattern[:40]}... hits={len(hits)}', pattern[:40], len(hits))
        for u in hits[:12]:
            logger.info('" hint", u[:180]')


if __name__ == "__main__":
    main()
