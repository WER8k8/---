"""UserActionAnalyzePlatform 并入网关 — 调 vendor Spark + MySQL 结果表。"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from mysql_repo import (
    compute_page_conversion_from_session_detail,
    create_task,
    fetch_page_conversion,
    fetch_session_aggr,
    fetch_top10_category,
    finish_task,
)
from task_runner import run_session_spark_job, vendor_root

app = FastAPI(
    title="UserActionAnalyzePlatform Gateway",
    version="1.0.0",
    description="封装上游 oeljeklaus-you/UserActionAnalyzePlatform（vendor + MySQL + Spark）",
)

TOKEN = (os.getenv("USER_ACTION_ANALYTICS_TOKEN") or "").strip()
ALLOW_STUB = (os.getenv("USER_ACTION_ANALYTICS_ALLOW_STUB") or "").strip().lower() in (
    "1",
    "true",
    "yes",
)

MODULE_MAIN = {
    "session_analysis": "cn.edu.hust.session.UserVisitAnalyze",
    "page_conversion": "page_conversion_stat",
    "hot_products": "top10_category",
    "ad_traffic_realtime": "ad_traffic_streaming",
}


class RunModuleBody(BaseModel):
    module_id: str
    upstream_module: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    purpose: str | None = None


def _auth(authorization: str | None) -> None:
    if not TOKEN:
        return
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
def health() -> dict[str, Any]:
    vr = vendor_root()
    return {
        "status": "ok",
        "service": "user-action-analytics-gateway",
        "vendor_present": vr.is_dir() and (vr / "pom.xml").is_file(),
        "vendor_path": str(vr),
        "upstream": "oeljeklaus-you/UserActionAnalyzePlatform",
    }


@app.get("/v1/vendor-info")
def vendor_info() -> dict[str, Any]:
    vr = vendor_root()
    return {
        "github": "https://github.com/oeljeklaus-you/UserActionAnalyzePlatform",
        "vendor_path": str(vr),
        "pom_exists": (vr / "pom.xml").is_file(),
        "modules_in_repo": ["session_analysis"],
        "modules_sidecar": ["page_conversion", "hot_products"],
        "note": "session 走上游 Spark；page_conversion 由 session_detail 聚合",
    }


@app.post("/v1/run-module")
def run_module(body: RunModuleBody, authorization: str | None = Header(None)) -> dict[str, Any]:
    _auth(authorization)
    module_id = (body.module_id or "").strip().lower()
    params = body.params or {}

    if ALLOW_STUB and os.getenv("ENVIRONMENT", "").lower() == "development":
        return {
            "items": [{"module": module_id, "note": "dev_stub"}],
            "job_id": "stub-dev-only",
            "probe_mode": "stub",
            "evidence_url": None,
        }

    if not vendor_root().is_dir():
        return {
            "items": [],
            "error_code": "VENDOR_NOT_INSTALLED",
            "note": "请运行 scripts/install-user-action-analytics-vendor.ps1 或 git submodule update",
            "probe_mode": "user_action_analytics",
        }

    start_date = params.get("start_date") or params.get("startDate") or "2016-01-01"
    end_date = params.get("end_date") or params.get("endDate") or "2016-01-31"
    task_param = {
        "startDate": start_date,
        "endDate": end_date,
        "startAge": params.get("startAge", 0),
        "endAge": params.get("endAge", 100),
        "professionals": params.get("professionals", []),
        "cities": params.get("cities", []),
        "sex": params.get("sex", []),
        "searchKeywords": params.get("searchKeywords", []),
        "clickCategoryIds": params.get("clickCategoryIds", []),
    }

    if module_id == "session_analysis":
        task_id = create_task(
            task_type="session_analysis",
            task_name=body.purpose or "session_analysis",
            task_param=task_param,
        )
        ok, detail = run_session_spark_job(task_id)
        if not ok:
            finish_task(task_id, "failed")
            return {
                "items": [],
                "job_id": str(task_id),
                "error_code": "SPARK_JOB_FAILED",
                "note": detail,
                "probe_mode": "user_action_analytics",
            }
        finish_task(task_id, "success")
        items = fetch_session_aggr(task_id)
        return {
            "items": items,
            "job_id": str(task_id),
            "evidence_url": f"mysql://user_action_analytics/session_aggr_stat/{task_id}",
            "probe_mode": "user_action_analytics",
            "human_review_required": True,
        }

    if module_id == "page_conversion":
        # 先跑 session 产出 session_detail，再聚合单跳转化
        task_id = create_task(
            task_type="page_conversion",
            task_name=body.purpose or "page_conversion",
            task_param=task_param,
        )
        ok, detail = run_session_spark_job(task_id)
        if not ok:
            finish_task(task_id, "failed")
            return {
                "items": [],
                "job_id": str(task_id),
                "error_code": "SPARK_JOB_FAILED",
                "note": detail,
                "probe_mode": "user_action_analytics",
            }
        items = compute_page_conversion_from_session_detail(task_id)
        finish_task(task_id, "success")
        if not items:
            items = fetch_page_conversion(task_id)
        return {
            "items": items,
            "job_id": str(task_id),
            "evidence_url": f"mysql://user_action_analytics/page_conversion_stat/{task_id}",
            "probe_mode": "user_action_analytics",
        }

    if module_id == "hot_products":
        task_id = create_task(
            task_type="hot_products",
            task_name=body.purpose or "hot_products",
            task_param=task_param,
        )
        ok, detail = run_session_spark_job(task_id)
        if not ok:
            finish_task(task_id, "failed")
            return {"items": [], "job_id": str(task_id), "error_code": "SPARK_JOB_FAILED", "note": detail}
        items = fetch_top10_category(task_id)
        finish_task(task_id, "success")
        return {
            "items": items,
            "job_id": str(task_id),
            "evidence_url": f"mysql://user_action_analytics/top10_category/{task_id}",
            "probe_mode": "user_action_analytics",
            "human_review_required": True,
        }

    if module_id == "ad_traffic_realtime":
        return {
            "items": [],
            "error_code": "MODULE_NOT_IN_UPSTREAM_REPO",
            "note": "广告实时流模块在上游 README 中，master 分支未包含 Spark Streaming 源码；须运维扩展 vendor",
            "probe_mode": "user_action_analytics",
        }

    return {"items": [], "error_code": "ANALYTICS_MODULE_UNKNOWN", "module_id": module_id}
