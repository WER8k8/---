"""三大增长内置工具 API。"""

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import SessionLocal, get_db
from app.models.growth_tools import WORD_CLASSES
from app.models.user import User
from app.services.agent_loop.growth_workflow import (
    create_growth_run,
    execute_growth_run,
    get_growth_run,
)
from app.services.agent_loop.run_repository import list_runs, sync_run, upsert_run
from app.services.agent_loop.workflow_presets import list_presets
from app.services.growth_tools_service import (
    ai_traffic_overview,
    create_keyword_entry,
    delete_keyword_entry,
    growth_dashboard,
    hot_keywords_overview,
    inspect_content_quality,
    list_keyword_library,
)
from app.services.geo.headless_rank_probe_service import (
    headless_probe_sidecar_status,
    run_headless_probe_batch,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/growth-tools", tags=["增长工具"])


def _run_growth_agent_background(run_id: str, tenant_id: str | None) -> None:
    """
    处理 _run_growth_agent_background 相关业务逻辑。

    :param run_id: 入参 (str)。
    :param tenant_id: 入参 (str | None)。

    :return: 返回 None 类型的结果。
    """
    db = SessionLocal()
    try:
        execute_growth_run(db, run_id, tenant_id=tenant_id)
    finally:
        db.close()


class GrowthAgentRunBody(BaseModel):
    goal: str = Field(default="跑一轮增长诊断：热词→质检→引流监测", max_length=500)
    preset_id: Optional[str] = Field(default=None, max_length=64)
    mode: Optional[str] = Field(default=None, description="full|quality_only|keyword_only|traffic_only")
    focus_keyword: Optional[str] = Field(default=None, max_length=200)
    content_title: Optional[str] = Field(default=None, max_length=300)
    content_body: Optional[str] = Field(default=None, max_length=20000)
    extra_keywords: list[str] = Field(default_factory=list)
    save_focus_keyword: bool = False


class KeywordCreateBody(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=500)
    word_class: str = Field(..., description="industry|brand|competitor|demand")
    search_volume: int = 0
    competition: int = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None


class ContentInspectBody(BaseModel):
    title: str = ""
    body: str = Field(..., min_length=10)
    keywords: list[str] = Field(default_factory=list)


@router.get("/dashboard")
def get_growth_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_growth_dashboard）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    return success_response(data=growth_dashboard(db, tenant_id=tenant_id))


@router.get("/agent/presets")
def get_growth_agent_presets(
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_growth_agent_presets）：处理相关业务逻辑并返回结果。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    return success_response(data={"items": list_presets()})


@router.get("/agent/runs")
def list_growth_agent_runs(
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_growth_agent_runs）：处理相关业务逻辑并返回结果。

    :param limit: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    user_id = str(getattr(current_user, "id", "") or "") or None
    items = list_runs(db, tenant_id=tenant_id, user_id=user_id, limit=limit)
    return success_response(data={"items": items, "total": len(items)})


@router.get("/keywords/hot")
def get_hot_keywords(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_hot_keywords）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    return success_response(data=hot_keywords_overview(db, tenant_id=tenant_id))


@router.get("/keywords/library")
def get_keyword_library(
    word_class: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_keyword_library）：处理相关业务逻辑并返回结果。

    :param word_class: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if word_class and word_class not in WORD_CLASSES:
        return error_response(400, f"word_class 须为: {', '.join(WORD_CLASSES)}")
    tenant_id = getattr(current_user, "tenant_id", None)
    rows = list_keyword_library(db, tenant_id=tenant_id, word_class=word_class)
    return success_response(data={"items": rows, "total": len(rows)})


@router.post("/keywords/library")
def post_keyword_library(
    body: KeywordCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交（post_keyword_library）：处理相关业务逻辑并返回结果。

    :param body: 入参 (KeywordCreateBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    try:
        row = create_keyword_entry(
            db,
            keyword=body.keyword,
            word_class=body.word_class,
            tenant_id=tenant_id,
            search_volume=body.search_volume,
            competition=body.competition,
            notes=body.notes,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="已加入专属词库")


@router.delete("/keywords/library/{entry_id}")
def remove_keyword_library(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    移除（remove_keyword_library）：处理相关业务逻辑并返回结果。

    :param entry_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    try:
        delete_keyword_entry(db, entry_id)
    except ValueError as exc:
        return error_response(404, str(exc))
    return success_response(message="已删除")


@router.post("/content-quality/inspect")
def post_content_quality_inspect(
    body: ContentInspectBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交（post_content_quality_inspect）：处理相关业务逻辑并返回结果。

    :param body: 入参 (ContentInspectBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    report = inspect_content_quality(
        db,
        title=body.title,
        body=body.body,
        keywords=body.keywords,
    )
    return success_response(data=report)


@router.get("/ai-traffic/overview")
def get_ai_traffic_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_ai_traffic_overview）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    return success_response(data=ai_traffic_overview(db))


class HeadlessProbeBody(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    target_url: str = Field(..., min_length=8, max_length=500)
    engine_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=8)


@router.get("/ai-traffic/headless-status")
def get_headless_probe_status(
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_headless_probe_status）：处理相关业务逻辑并返回结果。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    return success_response(data=headless_probe_sidecar_status())


class BaiduProbeBody(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    site: str | None = Field(None, max_length=500)


@router.post("/ai-traffic/baidu-probe")
def run_baidu_inclusion_probe(
    body: BaiduProbeBody,
    current_user: User = Depends(get_current_user),
):
    """一键测百度收录（Sidecar 在线时返回 evidence，未配置则明确失败）。"""
    from app.services.crawlers.ecommerce_crawlers_smart import quick_run
    tenant_id = getattr(current_user, "tenant_id", None)
    result = quick_run(
        "baidu",
        keyword=body.keyword.strip(),
        site=body.site.strip() if body.site else None,
        tenant_id=str(tenant_id) if tenant_id else None,
        operator_role=current_user.role,
    )
    if not result.get("ok"):
        code = 503 if (result.get("error_code") or "").endswith("NOT_CONFIGURED") else 400
        return error_response(code, result.get("message_zh") or result.get("error_code"))
    return success_response(data=result)


class ConversionProbeBody(BaseModel):
    site: str | None = Field(None, max_length=500)
    start_date: str | None = Field(None, max_length=32)
    end_date: str | None = Field(None, max_length=32)


@router.post("/ai-traffic/conversion-probe")
def run_page_conversion_probe_api(
    body: ConversionProbeBody,
    current_user: User = Depends(get_current_user),
):
    """一键查页面单跳转化率（Spark Sidecar）。"""
    from app.services.analytics.user_action_analytics_smart import quick_run
    params: dict[str, Any] = {}
    if body.site:
        params["site"] = body.site.strip()
    if body.start_date:
        params["start_date"] = body.start_date.strip()
    if body.end_date:
        params["end_date"] = body.end_date.strip()
    tenant_id = getattr(current_user, "tenant_id", None)
    result = quick_run(
        "conversion",
        params=params,
        tenant_id=str(tenant_id) if tenant_id else None,
        operator_role=current_user.role,
    )
    if not result.get("ok"):
        code = 503 if (result.get("error_code") or "").endswith("NOT_CONFIGURED") else 400
        return error_response(code, result.get("message_zh") or result.get("error_code"))
    return success_response(data=result)


@router.post("/ai-traffic/headless-probe")
def run_headless_probe(
    body: HeadlessProbeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发 headless 探针 batch（须 Sidecar 或 dev stub）。"""
    report = run_headless_probe_batch(
        db,
        keyword=body.keyword.strip(),
        target_url=body.target_url.strip(),
        engine_ids=body.engine_ids or None,
        limit=body.limit,
    )
    if not report.get("configured") and not report.get("dev_stub"):
        return error_response(
            503,
            "HEADLESS_PROBE_NOT_CONFIGURED：请配置 HEADLESS_PROBE_SIDECAR_URL",
        )
    return success_response(data=report)


@router.post("/agent/runs")
def start_growth_agent_run(
    body: GrowthAgentRunBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    启动（start_growth_agent_run）：处理相关业务逻辑并返回结果。

    :param body: 入参 (GrowthAgentRunBody)。
    :param background_tasks: 入参 (BackgroundTasks)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    context: dict[str, Any] = {}
    if body.mode:
        context["mode"] = body.mode.strip()
    if body.focus_keyword:
        context["focus_keyword"] = body.focus_keyword.strip()
    if body.content_title:
        context["content_title"] = body.content_title.strip()
    if body.content_body:
        context["content_body"] = body.content_body
    if body.extra_keywords:
        context["extra_keywords"] = [k.strip() for k in body.extra_keywords if k.strip()]
    if body.save_focus_keyword:
        context["save_focus_keyword"] = True

    run = create_growth_run(
        goal=body.goal,
        tenant_id=tenant_id,
        user_id=str(getattr(current_user, "id", "") or ""),
        context=context,
        preset_id=body.preset_id,
    )
    upsert_run(db, run)
    background_tasks.add_task(_run_growth_agent_background, run["id"], tenant_id)
    return success_response(data=run, message="智能跑盘已启动")


@router.get("/agent/runs/{run_id}")
def get_growth_agent_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_growth_agent_run）：处理相关业务逻辑并返回结果。

    :param run_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    run = get_growth_run(db, run_id)
    if not run:
        return error_response(404, "跑盘任务不存在或已过期")
    tenant_id = getattr(current_user, "tenant_id", None)
    if tenant_id and run.get("tenant_id") and run.get("tenant_id") != tenant_id:
        return error_response(403, "无权查看该跑盘任务")
    return success_response(data=run)
