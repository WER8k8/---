"""ECommerceCrawlers Sidecar 网关示例 — 运维独立部署，勿并入 backend 进程。"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="ECommerceCrawlers Sidecar", version="0.2.0")

TOKEN = (os.getenv("ECOMMERCE_CRAWLERS_TOKEN") or "").strip()
REPO_ROOT = (os.getenv("ECOMMERCE_CRAWLERS_REPO") or "/opt/ECommerceCrawlers").strip()


class RunSpiderBody(BaseModel):
    spider_id: str
    repo_path: str
    params: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    purpose: str | None = None
    compliance: str | None = None


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ecommerce-crawlers-sidecar"}


@app.post("/v1/run-spider")
def run_spider(body: RunSpiderBody, authorization: str | None = Header(None)) -> dict[str, Any]:
    _auth(authorization)
    if body.compliance == "platform_blocked":
        raise HTTPException(status_code=403, detail="platform_blocked")

    # 运维按 spider_id 扩展真实子项目调用；此处返回可核对结构，禁止无 evidence 假成功
    workdir = os.path.join(REPO_ROOT, body.repo_path)
    if not os.path.isdir(workdir):
        return {
            "items": [],
            "evidence_url": None,
            "probe_mode": "ecommerce_spider",
            "error": "REPO_PATH_NOT_FOUND",
            "repo_path": body.repo_path,
            "note": f"请在 Sidecar 主机 clone 上游仓库至 {REPO_ROOT}",
        }

    # 示例：调用子目录入口脚本（各子项目入口不同，运维需按 README 适配）
    entry = os.path.join(workdir, "main.py")
    if os.path.isfile(entry):
        try:
            proc = subprocess.run(
                [sys.executable, entry, "--json"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                import json

                data = json.loads(proc.stdout)
                if isinstance(data, dict):
                    data.setdefault("probe_mode", "ecommerce_spider")
                    return data
        except Exception as exc:
            return {
                "items": [],
                "evidence_url": None,
                "probe_mode": "ecommerce_spider",
                "error": str(exc)[:200],
            }

    keyword = (body.params.get("keyword") or body.params.get("target") or "").strip()
    source = f"https://www.baidu.com/s?wd={keyword}" if keyword else None
    return {
        "items": [],
        "evidence_url": source,
        "probe_mode": "ecommerce_spider",
        "skipped": True,
        "note": "子项目入口未适配；已返回 evidence_url 供主站校验，items 为空不算成功",
    }
