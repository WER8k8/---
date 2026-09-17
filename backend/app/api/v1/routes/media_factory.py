# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多媒体内容工厂路由。"""



import asyncio
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, Response, UploadFile

from pydantic import BaseModel

from sqlalchemy.orm import Session



from app.core.config import settings

from app.core.response import error_json_response, success_response
from app.core.no_fake_delivery import stamp_mock

from app.core.security import get_current_user

from app.db.session import get_db

from app.models.user import User

from app.services.ai_invocation_service import invoke_llm, normalize_scenario
from app.services.media_retention_service import record_handoff
from app.services.media_render_worker import run_render_task, run_render_task_background
from app.services.media_video_edit_service import (
    apply_video_clip,
    build_edit_payload,
    prepare_task_rerender,
    update_task_script,
)
from app.services.tenant_scenario_service import resolve_tenant_id_for_user

from app.services.media_factory_service import (

    build_ai_write_prompt,

    build_dev_video_script_fallback,

    build_article_to_video_script_prompt,

    clear_done_tasks,

    create_render_task,

    delete_render_task,

    get_render_task,

    get_render_task_for_user,

    ingest_uploaded_media_file,

    list_render_tasks,

    list_videos_for_dashboard,

    media_overview_stats,

    scenario_for_content_type,

    serialize_task,

    update_task_status,

)
from app.services.product_image_storage_service import validate_platform_tenant_id
from app.services.tts_synthesis_service import list_tts_history, synthesize_tts
from app.core.no_fake_delivery import NotConfiguredError


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/media-factory"
ROUTE_TAGS = ["多媒体工厂"]

router = APIRouter()





class AiWriteBody(BaseModel):

    prompt: str = ""
    contentType: str = "video-script"
    scenario: str | None = None





class GenerateVideoBody(BaseModel):

    script: str = ""
    title: str | None = None
    voice: str = "default"
    speed: int = 100
    bgm: str = "none"
    material: str = "search"
    resolution: str = "1080p"
    aspect: str = "16:9"
    subtitle: bool = True
    auto_render: bool | None = None





class ArticleToVideoBody(BaseModel):

    article: str = ""
    title: str | None = None
    resolution: str = "1080p"
    aspect: str = "16:9"
    auto_render: bool | None = None




class HandoffBody(BaseModel):

    action: str = "downloaded"
    external_url: str | None = None


class MediaPublishBody(BaseModel):

    platform_ids: list[str] = []
    persist_seo: bool = True


class MediaPublishTrafficBody(BaseModel):

    """引流闭环：先上租户官网（SEO/GEO），再可选发视频网站。"""
    platform_ids: list[str] = []


class GuestBindBody(BaseModel):

    guest_token: str | None = None




class ClipBody(BaseModel):

    start_sec: float = 0
    end_sec: float = 0




class ScriptUpdateBody(BaseModel):

    script: str = ""
    shots: list[dict] | None = None




class ReRenderBody(BaseModel):

    script: str | None = None
    shots: list[dict] | None = None
    auto_render: bool = True





def _admin_only(current_user: User):
    """执行 admin_only 相关逻辑处理。
    
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    from app.core.tenant_access import user_has_module_permission
    if not user_has_module_permission(current_user, "content", "update"):

        return error_json_response(403, "缺少权限: content:update")

    return None


MEDIA_UPLOAD_EXTENSIONS = {
    "mp4", "webm", "avi", "mov", "mkv", "flv", "wmv",
    "mp3", "wav", "m4a", "aac", "ogg",
}
MAX_MEDIA_UPLOAD_BYTES = 500 * 1024 * 1024





def _allow_dev_ai_fallback() -> bool:
    """执行 allow_dev_ai_fallback 相关逻辑处理。
    :return: 返回处理结果。
    """
    mvp = settings.MVP_LAUNCH
    return settings.ENVIRONMENT in ("development", "testing", "test") or mvp


def _guest_token_from_request(request: Request, body_token: str | None = None) -> str | None:
    """执行 guest_token_from_request 相关逻辑处理。
    
    :param request: HTTP 请求对象
    :param body_token: 参数 body_token
    :return: 返回处理结果。
    """
    from app.services.media_guest_service import GUEST_COOKIE, GUEST_HEADER, resolve_guest_token
    return resolve_guest_token(
        request.headers.get(GUEST_HEADER),
        request.cookies.get(GUEST_COOKIE),
        body_token,
    )


def _inject_guest(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    """执行 inject_guest 相关逻辑处理。
    
    :param payload: 请求体数据
    :param request: HTTP 请求对象
    :return: 返回处理结果。
    """
    out = dict(payload)
    token = _guest_token_from_request(request, out.get("guest_token"))
    if token:
        out["guest_token"] = token
    return out





def _schedule_render(

    background_tasks: BackgroundTasks,

    task_id: str,

    auto_render: bool | None,

) -> bool:
    """执行 schedule_render 相关逻辑处理。
    
    :param background_tasks: 后台任务
    :param task_id: 任务ID
    :param auto_render: 参数 auto_render
    :return: 返回处理结果。
    """
    should_run = settings.MEDIA_FACTORY_AUTO_RENDER if auto_render is None else auto_render
    if should_run:

        background_tasks.add_task(run_render_task_background, task_id)

    return should_run





@router.get("/")

def get_media_factory_overview(

    tenant_id: str | None = Query(None, description="超管可选：按租户筛选"),
    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 GET / 请求，获取相关资源。
    
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_json_response(400, tenant_err)

    return success_response(
        data=media_overview_stats(
            db,
            current_user,
            tenant_id=tenant_id.strip() if tenant_id else None,
        )
    )


@router.get("/videos")
def list_media_factory_videos(
    tenant_id: str | None = Query(None, description="超管可选：按租户筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """视频管理中心列表（租户仅见本租户任务）。"""
    denied = _admin_only(current_user)
    if denied:
        return denied
    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_json_response(400, tenant_err)
    return success_response(
        data=list_videos_for_dashboard(
            db,
            current_user,
            limit=200,
            tenant_id=tenant_id.strip() if tenant_id else None,
        )
    )


@router.post("/upload")
def upload_media_factory_file(
    file: UploadFile = File(...),
    tenant_id: str | None = Form(None, description="超管可选：代指定租户上传"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """直传视频/音频 — 按租户写入 tenants/{id}/videos|audio/ 并登记任务。"""
    denied = _admin_only(current_user)
    if denied:
        return denied

    tenant_err = validate_platform_tenant_id(db, current_user, tenant_id)
    if tenant_err:
        return error_json_response(400, tenant_err)

    original_filename = file.filename or "unnamed"
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in MEDIA_UPLOAD_EXTENSIONS:
        return error_json_response(
            400,
            f"不支持的媒体类型 .{ext or '?'}，允许: {', '.join(sorted(MEDIA_UPLOAD_EXTENSIONS))}",
        )

    try:
        content = file.file.read()
        if len(content) > MAX_MEDIA_UPLOAD_BYTES:
            return error_json_response(400, "文件大小超过 500MB 限制")
    except Exception as exc:
        return error_json_response(500, f"读取文件失败: {exc}")
    finally:
        file.file.close()

    try:
        item = ingest_uploaded_media_file(
            db,
            current_user,
            content=content,
            original_filename=original_filename,
            content_type=file.content_type,
            explicit_tenant_id=tenant_id.strip() if tenant_id else None,
        )
    except ValueError as exc:
        return error_json_response(400, str(exc))

    return success_response(data=item, message="上传成功")





async def _invoke_ai_write_llm(db: Session, current_user: User, prompt: str, full_prompt: str, scenario: str, ai_write_timeout: int):
    """调用 LLM 生成脚本，超时/异常时按 dev fallback 规则返回 (result, error_response)。"""
    try:
        result = await asyncio.wait_for(
            invoke_llm(
                db,
                prompt=full_prompt,
                scenario=scenario,
                tenant_id=resolve_tenant_id_for_user(db, current_user),
                enable_fallback=False,
                max_retries=1,
            ),
            timeout=ai_write_timeout,
        )
    except (RuntimeError, asyncio.TimeoutError) as exc:
        if _allow_dev_ai_fallback():
            fallback = build_dev_video_script_fallback(prompt)
            return None, success_response(
                data=stamp_mock(
                    {
                        "content": fallback,
                        "text": fallback,
                        "scenario": scenario,
                        "fallback_reason": "timeout" if isinstance(exc, asyncio.TimeoutError) else str(exc),
                    },
                    reason="ai_write_dev_fallback",
                )
            )
        msg = "AI 生成超时，请稍后重试" if isinstance(exc, asyncio.TimeoutError) else str(exc)
        return None, error_json_response(503, msg)
    return result, None


@router.post("/ai-write")
async def ai_write_script(
    body: AiWriteBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 写脚本/文案（按 contentType 映射场景）"""
    denied = _admin_only(current_user)
    if denied:
        return denied

    prompt = (body.prompt or "").strip()
    if not prompt:
        return error_json_response(400, "prompt 不能为空")

    scenario = normalize_scenario(
        body.scenario or scenario_for_content_type(body.contentType)
    )
    full_prompt = build_ai_write_prompt(prompt, body.contentType)
    ai_write_timeout = int(getattr(settings, "MEDIA_FACTORY_AI_WRITE_TIMEOUT", 8) or 8)
    result, err = await _invoke_ai_write_llm(db, current_user, prompt, full_prompt, scenario, ai_write_timeout)
    if err:
        return err

    content = (result.get("content") or "").strip()
    if not content and _allow_dev_ai_fallback():
        fallback = build_dev_video_script_fallback(prompt)
        return success_response(
            data=stamp_mock(
                {
                    "content": fallback,
                    "text": fallback,
                    "scenario": scenario,
                },
                reason="ai_write_empty_dev_fallback",
            )
        )
    return success_response(
        data={
            "content": content,
            "text": content,
            "scenario": scenario,
            "token_usage": result.get("token_usage", 0),
        }
    )





async def _generate_article_video_script(db: Session, article: str, current_user: User):
    """调用 LLM 生成文章转视频分镜脚本，返回 (script, error_response)。"""
    try:
        script_result = await invoke_llm(
            db,
            prompt=build_article_to_video_script_prompt(article),
            scenario="article_to_video_script",
            task_type="article_to_video_script",
            tenant_id=resolve_tenant_id_for_user(db, current_user),
        )
    except RuntimeError as exc:
        return None, error_json_response(503, str(exc))

    script = (script_result.get("content") or "").strip()
    if not script:
        return None, error_json_response(502, "脚本生成失败，模型未返回内容")
    return script, None


def _create_article_video_render_task(db: Session, body, request, article, script, current_user):
    """创建渲染任务，返回 (task, error_response)。"""
    try:
        task = create_render_task(
            db,
            _inject_guest(
                {
                    "script": script,
                    "title": body.title or article[:40],
                    "resolution": body.resolution,
                    "aspect": body.aspect,
                    "scenario": "article_to_video_render",
                    "tenant_id": resolve_tenant_id_for_user(db, current_user),
                },
                request,
            ),
        )
    except ValueError as exc:
        return None, error_json_response(400, str(exc))
    return task, None


@router.post("/article-to-video")

async def article_to_video_pipeline(

    body: ArticleToVideoBody,

    request: Request,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """文章 → 分镜脚本 → 渲染任务（可选自动执行 Cosmos）。"""
    denied = _admin_only(current_user)
    if denied:

        return denied



    article = (body.article or "").strip()
    if not article:

        return error_json_response(400, "article 不能为空")



    script, err = await _generate_article_video_script(db, article, current_user)
    if err:

        return err



    task, err = _create_article_video_render_task(db, body, request, article, script, current_user)
    if err:

        return err



    scheduled = _schedule_render(background_tasks, task.id, body.auto_render)
    data = serialize_task(task, db)
    data["script"] = script
    data["auto_render"] = scheduled
    data["message"] = (

        "脚本已生成并加入渲染队列。"
        + ("后台 worker 已开始执行。" if scheduled else "请调用 POST /tasks/{id}/run 手动执行。")

    )
    return success_response(data=data, message="文章转视频任务已创建")





@router.post("/generate")

def generate_video_task(

    body: GenerateVideoBody,

    request: Request,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """创建视频渲染任务并入队。"""
    denied = _admin_only(current_user)
    if denied:

        return denied



    try:

        task = create_render_task(

            db,
            _inject_guest(

                {

                    "script": body.script,
                    "title": body.title,
                    "voice": body.voice,
                    "resolution": body.resolution,
                    "aspect": body.aspect,
                    "scenario": "article_to_video_render",
                    "tenant_id": resolve_tenant_id_for_user(db, current_user),

                },
                request,

            ),

        )

    except ValueError as exc:

        return error_json_response(400, str(exc))



    scheduled = _schedule_render(background_tasks, task.id, body.auto_render)
    data = serialize_task(task, db)
    data["auto_render"] = scheduled
    data["message"] = (

        "任务已入队。"
        + ("Cosmos 渲染 worker 已启动。" if scheduled else "可手动触发 POST /tasks/{id}/run。")

    )
    return success_response(data=data, message="任务已加入渲染队列")





@router.get("/tasks/{task_id}")

def get_task_detail(

    task_id: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 GET /tasks/{task_id} 请求，获取相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    return success_response(data=serialize_task(task, db))


@router.get("/guest-session")
def guest_session(response: Response):
    """未登录访客领取 guest_token（Cookie + 响应体）。"""
    from app.services.media_guest_service import GUEST_COOKIE, new_guest_token
    token = new_guest_token()
    response.set_cookie(
        key=GUEST_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return success_response(
        data={"guest_token": token, "header": "X-Guest-Token"},
        message="访客会话已创建",
    )


@router.get("/tasks/{task_id}/seo-bundle")
def get_task_seo_bundle(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """视频专用 SEO/GEO 包（VideoObject 独立，不合并进文章 Schema）。"""
    denied = _admin_only(current_user)
    if denied:
        return denied
    task = get_render_task_for_user(db, task_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")
    from app.services.media_seo_service import build_media_seo_bundle
    return success_response(data=build_media_seo_bundle(task))


@router.post("/tasks/{task_id}/publish-traffic")
async def publish_video_traffic_api(
    task_id: str,
    body: MediaPublishTrafficBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """视频引流：租户官网落地页 + VideoObject/GEO + 可选 YouTube 等。"""
    denied = _admin_only(current_user)
    if denied:
        return denied
    from app.services.video_publish_router import distribute_video
    try:
        data = await distribute_video(
            db,
            media_task_id=task_id,
            platform_ids=body.platform_ids or None,
            include_tenant_site=True,
        )
    except ValueError as exc:
        return error_json_response(400, str(exc))
    return success_response(data=data, message=data.get("message") or "视频分发完成")


@router.post("/tasks/{task_id}/publish-to-site")
def publish_video_to_tenant_site_api(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """仅登记租户官网视频页（SEO sitemap + VideoObject），不发外站。"""
    denied = _admin_only(current_user)
    if denied:
        return denied
    from app.services.media_tenant_traffic_service import get_tenant, publish_video_to_tenant_site
    task = get_render_task_for_user(db, task_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")
    tenant = get_tenant(db, task.tenant_id)
    if not tenant:
        return error_json_response(400, "任务未绑定租户，无法生成官网落地页")
    try:
        result = publish_video_to_tenant_site(db, task, tenant)
    except ValueError as exc:
        return error_json_response(400, str(exc))
    return success_response(data=result, message="租户视频落地页已发布")


@router.post("/tasks/{task_id}/publish")
async def publish_task_to_platforms_api(
    task_id: str,
    body: MediaPublishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """渲染完成后发布到多平台（YouTube 等使用 publish_video_url）。"""
    denied = _admin_only(current_user)
    if denied:
        return denied
    if not body.platform_ids:
        return error_json_response(400, "platform_ids 不能为空")
    from app.services.media_publish_service import publish_task_to_platforms
    task = get_render_task_for_user(db, task_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")
    if task.status != "done":
        return error_json_response(400, "任务尚未渲染完成")
    try:
        results = await publish_task_to_platforms(
            task,
            body.platform_ids,
            db=db if body.persist_seo else None,
            persist_seo=body.persist_seo,
        )
    except ValueError as exc:
        return error_json_response(400, str(exc))
    from app.services.media_seo_service import build_media_seo_bundle
    return success_response(
        data={
            "task_id": task_id,
            "results": results,
            "seo_bundle": build_media_seo_bundle(task),
        },
        message="发布请求已处理",
    )


@router.post("/tasks/{task_id}/handoff")

def handoff_task_media(

    task_id: str,

    body: HandoffBody,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """登记「已下载 / 已发布」，加速删除成品（脚本保留）。"""
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    if task.file_purged or not task.result_path:

        return error_json_response(400, "成品已过期或不存在，无法登记 handoff")

    if task.status != "done":

        return error_json_response(400, "任务尚未完成，无法登记 handoff")

    try:

        updated = record_handoff(db, task, body.action.strip(), body.external_url)

    except ValueError as exc:

        return error_json_response(400, str(exc))

    return success_response(

        data=serialize_task(updated, db),
        message="已登记，成品将在 handoff 窗口后自动删除",

    )





@router.get("/tasks/{task_id}/edit")

def get_task_edit_state(

    task_id: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """剪辑调试：预览 URL、时长、分镜列表。"""
    denied = _admin_only(current_user)
    if denied:

        return denied

    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    payload = build_edit_payload(db, task)
    payload["task"] = serialize_task(task, db)
    return success_response(data=payload)





@router.put("/tasks/{task_id}/script")

def update_task_script_api(

    task_id: str,

    body: ScriptUpdateBody,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """保存脚本修改（调试），不自动重渲。"""
    denied = _admin_only(current_user)
    if denied:

        return denied

    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    try:

        updated = update_task_script(

            db,
            task,
            script=body.script,
            shots=body.shots,

        )

    except ValueError as exc:

        return error_json_response(400, str(exc))

    data = serialize_task(updated, db)
    data["edit"] = build_edit_payload(db, updated)
    return success_response(data=data, message="脚本已保存")





@router.post("/tasks/{task_id}/clip")

def clip_task_video(

    task_id: str,

    body: ClipBody,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """按起止时间裁剪成片，生成剪辑版预览。"""
    denied = _admin_only(current_user)
    if denied:

        return denied

    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    try:

        updated = apply_video_clip(

            db,
            task,
            start_sec=body.start_sec,
            end_sec=body.end_sec,

        )

    except ValueError as exc:

        return error_json_response(400, str(exc))

    data = serialize_task(updated, db)
    data["edit"] = build_edit_payload(db, updated)
    return success_response(data=data, message="剪辑版已生成")





@router.post("/tasks/{task_id}/re-render")

def rerender_task(

    task_id: str,

    body: ReRenderBody,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """保存脚本并重置任务，重新进入渲染队列。"""
    denied = _admin_only(current_user)
    if denied:

        return denied

    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    if body.script or body.shots:

        try:

            task = update_task_script(

                db,
                task,
                script=body.script or task.script,
                shots=body.shots,

            )

        except ValueError as exc:

            return error_json_response(400, str(exc))

    task = prepare_task_rerender(db, task)
    scheduled = _schedule_render(background_tasks, task.id, body.auto_render)
    data = serialize_task(task, db)
    data["auto_render"] = scheduled
    data["edit"] = build_edit_payload(db, task)
    return success_response(data=data, message="已加入重渲队列")





@router.post("/tasks/{task_id}/run")

def run_task(

    task_id: str,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 POST /tasks/{task_id}/run 请求，运行相关资源。
    
    :param task_id: 任务ID
    :param background_tasks: 后台任务
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    if task.status == "rendering":

        return success_response(data=serialize_task(task, db), message="任务正在渲染")

    if task.status == "done":

        return success_response(data=serialize_task(task, db), message="任务已完成")



    background_tasks.add_task(run_render_task_background, task_id)
    update_task_status(db, task, status="queued", progress=0, error_message=None)
    refreshed = get_render_task_for_user(db, task_id, current_user)
    return success_response(data=serialize_task(refreshed, db), message="渲染 worker 已启动")





@router.post("/tasks/{task_id}/run-sync")

def run_task_sync(

    task_id: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """同步执行（仅开发/调试；生产请用 /run）。"""
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")



    try:

        finished = run_render_task(db, task_id)

    except ValueError as exc:

        return error_json_response(400, str(exc))

    except RuntimeError as exc:

        return error_json_response(409, str(exc))



    return success_response(data=serialize_task(finished, db))





@router.get("/render-queue")

def get_render_queue(

    page: int = 1,

    page_size: int = 20,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 GET /render-queue 请求，获取相关资源。
    
    :param page: 页码
    :param page_size: 每页条数
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    items = list_render_tasks(db, limit=max(page_size, 50), user=current_user)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    return success_response(

        data={

            "items": page_items,
            "list": page_items,
            "total": len(items),
            "page": page,
            "page_size": page_size,

        }

    )





@router.post("/render-queue/{task_id}/pause")

def pause_task(

    task_id: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 POST /render-queue/{task_id}/pause 请求，pause相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    if task.status != "queued":

        return error_json_response(409, "仅排队中任务可暂停")



    update_task_status(db, task, status="paused")
    return success_response(data=serialize_task(task, db), message="任务已暂停")





@router.post("/render-queue/{task_id}/resume")

def resume_task(

    task_id: str,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 POST /render-queue/{task_id}/resume 请求，resume相关资源。
    
    :param task_id: 任务ID
    :param background_tasks: 后台任务
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:

        return error_json_response(404, "任务不存在")

    if task.status != "paused":

        return error_json_response(409, "任务未处于暂停状态")



    update_task_status(db, task, status="queued")
    _schedule_render(background_tasks, task_id, True)
    refreshed = get_render_task_for_user(db, task_id, current_user)
    return success_response(data=serialize_task(refreshed, db), message="任务已恢复")





@router.delete("/render-queue/{task_id}")

def cancel_task(

    task_id: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 DELETE /render-queue/{task_id} 请求，cancel相关资源。
    
    :param task_id: 任务ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    task = get_render_task_for_user(db, task_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")

    try:
        ok = delete_render_task(db, task_id)
    except ValueError as exc:
        return error_json_response(409, str(exc))

    if not ok:
        return error_json_response(404, "任务不存在")
    return success_response(message="任务已取消")





@router.post("/render-queue/clear-done")

def clear_done(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 POST /render-queue/clear-done 请求，clear相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied



    count = clear_done_tasks(db)
    return success_response(data={"cleared": count}, message=f"已清空 {count} 个已完成任务")





class TtsSynthesizeBody(BaseModel):
    text: str
    voice: str = "female"
    speed: float = 1.0
    volume: int = 80


@router.get("/tts")
def get_tts_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /tts 请求，获取相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:
        return denied
    history = list_tts_history(str(current_user.id))
    return success_response(
        data={
            "voices_available": 4,
            "generated_count": len(history),
            "list": history,
            "recent_audio": history[:10],
        }
    )


@router.post("/tts/synthesize")
def post_tts_synthesize(
    body: TtsSynthesizeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /tts/synthesize 请求，post相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:
        return denied
    try:
        record = synthesize_tts(
            user_id=str(current_user.id),
            text=body.text,
            voice=body.voice,
            speed=body.speed,
            volume=body.volume,
        )
    except ValueError as exc:
        return error_json_response(400, str(exc))
    except NotConfiguredError as exc:
        return error_json_response(503, f"{exc.code}: {exc}")
    except NotImplementedError as exc:
        return error_json_response(501, str(exc))
    return success_response(data=record, message="配音任务已创建")





@router.get("/charts")

def get_chart_engine_status(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):
    """处理 GET /charts 请求，获取相关资源。
    
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _admin_only(current_user)
    if denied:

        return denied

    return success_response(

        data={

            "chart_types": ["market_share", "sales_trend", "product_category"],
            "generated_count": 0,
            "recent_charts": [],

        }

    )


