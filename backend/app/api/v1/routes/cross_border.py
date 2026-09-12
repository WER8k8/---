"""跨境语言桥 API — W1 中文片出海 / W2 询盘桥 / W3 报价+SEO。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_json_response, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.cross_border.export_quote_service import build_export_quote_onepager
from app.services.cross_border.inquiry_bridge_service import (
    draft_reply_en,
    inquiry_bridge_status,
    summarize_inquiry_zh,
)
from app.services.cross_border.seo_belt_service import preview_belt_keywords, seed_keywords_for_tenant
from app.services.cross_border.industry_belt_product_import_service import (
    import_product_candidates,
    list_product_candidates,
)
from app.services.cross_border.cross_border_sse import stream_cross_border_job_events
from app.services.cross_border.cross_border_job_service import (
    create_cross_border_job,
    dispatch_cross_border_job,
    get_cross_border_job,
    serialize_cross_border_job,
)
from app.services.cross_border.tts_service import list_english_voices, tts_status
from app.services.cross_border.media_studio_capability_registry import build_media_studio_capabilities
from app.services.cross_border.media_studio_project_service import (
    get_studio_project,
    save_studio_project,
)
from app.services.cross_border.video_dub_service import ingest_client_video


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/cross-border", tags=["跨境语言桥"])

MEDIA_UPLOAD_EXTENSIONS = {"mp4", "webm", "mov", "avi", "mkv"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024


def _resolve_tenant(db: Session, user: User):
    """
    处理 _resolve_tenant 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    from app.api.v1.routes.client import _resolve_tenant as client_resolve
    return client_resolve(db, user)


def _staff(user: User) -> bool:
    """
    处理 _staff 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回 bool 类型的结果。
    """
    return user.role in ("super_admin", "admin", "tenant_admin", "operator", "user")


class ReplyDraftBody(BaseModel):
    boss_reply_zh: str = Field(..., min_length=2, max_length=4000)
    tone: str = Field(default="professional")


class ImapPollBody(BaseModel):
    tenant_consent: bool = False
    compliance_acknowledged: bool = False
    max_messages: int = Field(10, ge=1, le=50)
    mailbox: str | None = Field(None, max_length=120)


class ExportQuoteBody(BaseModel):
    inquiry_id: str | None = None
    product_id: str | None = None
    moq: str | None = None
    unit_price: float | None = None
    currency: str = "USD"
    delivery_terms: str = "FOB Tianjin"
    payment_terms: str = "30% T/T deposit, 70% before shipment"
    validity_days: int = 15
    notes_zh: str = ""


class VideoDubBody(BaseModel):
    media_task_id: str
    transcript_zh: str | None = None
    voice_consent: bool = False
    output_mode: str = "subtitle"
    auto_asr: bool = False
    tts_voice: str | None = None
    dub_voice_gender: str = "auto"
    track: str = "standard"  # standard | opensource_premium | vozo
    localization_provider: str | None = None


class PremiumDubBody(BaseModel):
    media_task_id: str
    transcript_zh: str | None = None
    voice_consent: bool = False
    output_mode: str = "dub"
    track: str = "opensource_premium"  # opensource_premium | vozo
    localization_provider: str | None = None
    dub_voice_gender: str = "auto"


class StudioProjectBody(BaseModel):
    transcript_zh: str | None = None
    script_en: str | None = None
    srt_url: str | None = None
    segments: list[dict[str, Any]] | None = None
    asr_backend: str | None = None
    localization_provider: str | None = None
    output_url: str | None = None


class TranscribeBody(BaseModel):
    media_task_id: str


class ImportCandidatesBody(BaseModel):
    candidate_ids: list[str] = Field(..., min_length=1, max_length=50)
    survey_id: str | None = None
    activate: bool = False


class SeedKeywordsBody(BaseModel):
    belt_id: str = "all"
    include_ranking: bool = True


class PipelineStageBody(BaseModel):
    stage: str = Field(..., min_length=2, max_length=20)
    note: str | None = Field(None, max_length=300)


@router.get("/inquiries/bridge-status")
def inquiry_bridge_status_route(current_user: User = Depends(get_current_user)):
    """XF-C1/C2 询盘语言桥 LLM 就绪态。"""
    if not _staff(current_user):
        return success_response(data={}, message="权限不足")
    return success_response(data=inquiry_bridge_status())


@router.post("/inquiries/imap-poll")
def inquiry_imap_poll(
    body: ImapPollBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P5 只读 IMAP 询盘收取 — 禁止 SMTP 自动回复。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    if not body.tenant_consent:
        return error_response(403, "IMAP_TENANT_CONSENT_REQUIRED")
    if not body.compliance_acknowledged:
        return error_response(403, "IMAP_COMPLIANCE_ACK_REQUIRED")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.cross_border.imap_inquiry_ingest_service import poll_and_ingest_imap_inquiries
    result = poll_and_ingest_imap_inquiries(
        db,
        tenant=tenant,
        max_messages=body.max_messages,
        mailbox=body.mailbox,
    )
    if not result.get("ok"):
        return error_response(503, result.get("note") or result.get("error_code") or "IMAP poll failed")
    return success_response(data=result)


@router.get("/inquiries/pipeline/summary")
def inquiry_pipeline_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GW-L-PL-01 询盘管道阶段汇总。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.foreign_trade.inquiry_pipeline_service import pipeline_summary
    return success_response(data=pipeline_summary(db, tenant_id=str(tenant.id)))


@router.patch("/inquiries/{inquiry_id}/pipeline-stage")
def inquiry_pipeline_stage_update(
    inquiry_id: str,
    body: PipelineStageBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GW-L-PL-01 更新询盘管道阶段。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    inquiry = (
        db.query(Inquiry)
        .filter(Inquiry.id == inquiry_id, Inquiry.is_active, Inquiry.tenant_id == str(tenant.id))
        .first()
    )
    if not inquiry:
        return error_response(404, "询盘不存在")
    from app.services.foreign_trade.inquiry_pipeline_service import set_pipeline_stage
    try:
        data = set_pipeline_stage(
            db,
            inquiry,
            stage=body.stage,
            user_id=str(current_user.id),
            note=body.note,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=data)


@router.get("/geo-visibility")
def geo_visibility_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GW-G-GEO-DASH 客户可见性看板。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    from app.services.foreign_trade.geo_visibility_dashboard_service import (
        build_geo_visibility_dashboard,
    )
    return success_response(data=build_geo_visibility_dashboard(db, tenant_id=str(tenant.id)))


@router.get("/unified-geo-score")
async def cross_border_unified_geo_score(
    include_probes: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GW-G-GEO-UNIFIED — 租户统一 GEO 分（unified-geo-v1）。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    domain = str(tenant.domain or "").strip()
    if not domain:
        return error_response(400, "租户未绑定独立域名，无法计算 GEO 分")
    from app.services.unified_geo_score_service import build_unified_geo_score
    payload = await build_unified_geo_score(db, domain=domain, include_probes=include_probes)
    return success_response(data=payload)


@router.post("/inquiries/{inquiry_id}/bridge-summary")
async def inquiry_bridge_summary(
    inquiry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W2: 外文询盘 → 中文摘要。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    inquiry = (
        db.query(Inquiry)
        .filter(Inquiry.id == inquiry_id, Inquiry.is_active, Inquiry.tenant_id == str(tenant.id))
        .first()
    )
    if not inquiry:
        return error_response(404, "询盘不存在")
    try:
        data = await summarize_inquiry_zh(db, tenant, inquiry)
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="已生成中文摘要，请核对后再回电")


@router.post("/inquiries/{inquiry_id}/reply-draft")
async def inquiry_reply_draft(
    inquiry_id: str,
    body: ReplyDraftBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W2: 老板中文要点 → 英文回复草稿。"""
    if not _staff(current_user):
        return error_response(403, "权限不足")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    inquiry = (
        db.query(Inquiry)
        .filter(Inquiry.id == inquiry_id, Inquiry.is_active, Inquiry.tenant_id == str(tenant.id))
        .first()
    )
    if not inquiry:
        return error_response(404, "询盘不存在")
    try:
        data = await draft_reply_en(
            db, tenant, inquiry, boss_reply_zh=body.boss_reply_zh, tone=body.tone
        )
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="英文草稿已生成，发送前须人工确认")


@router.get("/export-quote")
def get_export_quote(
    product_id: str | None = None,
    moq: str | None = None,
    unit_price: float | None = None,
    currency: str = "USD",
    delivery_terms: str = "FOB Tianjin",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W3: FOB/MOQ 报价一页（GET 预览）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    data = build_export_quote_onepager(
        db,
        tenant,
        product_id=product_id,
        moq=moq,
        unit_price=unit_price,
        currency=currency,
        delivery_terms=delivery_terms,
    )
    return success_response(data=data)


@router.post("/export-quote")
def post_export_quote(
    body: ExportQuoteBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W3: FOB/MOQ 报价一页（POST 带参数）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    data = build_export_quote_onepager(
        db,
        tenant,
        product_id=body.product_id,
        moq=body.moq,
        unit_price=body.unit_price,
        currency=body.currency,
        delivery_terms=body.delivery_terms,
        payment_terms=body.payment_terms,
        validity_days=body.validity_days,
        notes_zh=body.notes_zh,
    )
    # 批次 B 首调用方：报价签发即向 GoodJob 委派 QUOTATION 单证任务（失败静默）。
    doc_task_id = _dispatch_goodjob_quotation_task(tenant, body, data)
    if doc_task_id:
        data["goodjob_doc_task_id"] = doc_task_id
    return success_response(data=data)


def _dispatch_goodjob_quotation_task(
    tenant: Any,
    body: ExportQuoteBody,
    data: dict[str, Any],
) -> str | None:
    if not body.inquiry_id or not data.get("ready"):
        return None
    try:
        from app.orchestration.executors.goodjob_executor import (
            build_goodjob_executor,
        )
        from app.services.goodjob.trade_document_bridge import (
            submit_document_task,
        )
        executor = build_goodjob_executor()
        if executor is None:
            return None
        pi = data.get("pi") or {}
        options = {
            "currency": body.currency,
            "delivery_terms": body.delivery_terms,
            "payment_terms": body.payment_terms,
            "validity_days": body.validity_days,
            "human_confirm_required": True,
        }
        return submit_document_task(
            executor,
            tenant_id=str(tenant.id),
            inquiry_id=body.inquiry_id,
            doc_type="QUOTATION",
            items=pi.get("lines") or [],
            options=options,
        )
    except Exception:
        return None


@router.post("/video-dub/upload")
def upload_video_for_dub(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1: 租户上传中文产品片。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    original = file.filename or "video.mp4"
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in MEDIA_UPLOAD_EXTENSIONS:
        return error_response(400, f"不支持 .{ext}，允许: {', '.join(sorted(MEDIA_UPLOAD_EXTENSIONS))}")
    try:
        content = file.file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            return error_response(400, "文件超过 500MB")
    finally:
        file.file.close()
    item = ingest_client_video(
        db,
        current_user,
        content=content,
        original_filename=original,
        content_type=file.content_type,
        tenant_id=str(tenant.id),
    )
    return success_response(data=item, message="上传成功，可继续生成英文字幕")


@router.post("/video-dub/jobs")
async def create_video_dub_job(
    body: VideoDubBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1: 中→英脚本 + SRT（异步入队）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    track = (body.track or "standard").strip().lower()
    kind: str = "premium" if track in ("opensource_premium", "opensource", "premium", "vozo") else "dub"
    if kind == "premium" and track == "vozo":
        from app.services.cross_border.vozo_localization_service import is_vozo_configured
        if not is_vozo_configured():
            return error_json_response(503, "VOZO_NOT_CONFIGURED: Vozo 商业精品轨未配置 VOZO_API_KEY")
    elif kind == "premium":
        from app.services.cross_border.opensource_localization_registry import (
            pick_active_opensource_provider,
        )
        if not pick_active_opensource_provider(body.localization_provider):
            return error_json_response(
                503,
                "OPENSOURCE_NOT_CONFIGURED: 开源精品轨未部署 sidecar，请先在剪辑台查看配置项",
            )

    job, job_err = create_cross_border_job(
        db,
        tenant=tenant,
        user=current_user,
        media_task_id=body.media_task_id,
        kind=kind,  # type: ignore[arg-type]
        payload={
            "transcript_zh": body.transcript_zh,
            "voice_consent": body.voice_consent,
            "output_mode": body.output_mode,
            "auto_asr": body.auto_asr,
            "tts_voice": body.tts_voice,
            "dub_voice_gender": body.dub_voice_gender,
            "track": track if kind == "premium" else "standard",
            "localization_provider": body.localization_provider,
        },
    )
    if job_err:
        return error_json_response(job_err["code"], job_err["message"])
    backend = dispatch_cross_border_job(str(job.id))
    data = serialize_cross_border_job(job)
    data["dispatch"] = backend
    return success_response(data=data, message="出海任务已入队")


@router.post("/video-dub/premium-jobs")
async def create_premium_video_dub_job(
    body: PremiumDubBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1 精品轨：开源 sidecar 或 Vozo（异步入队）。"""
    return await create_video_dub_job(
        VideoDubBody(
            media_task_id=body.media_task_id,
            transcript_zh=body.transcript_zh,
            voice_consent=body.voice_consent,
            output_mode=body.output_mode,
            auto_asr=False,
            track=body.track,
            localization_provider=body.localization_provider,
            dub_voice_gender=body.dub_voice_gender,
        ),
        db=db,
        current_user=current_user,
    )


@router.get("/media-studio/projects/{media_task_id}")
def get_media_studio_project(
    media_task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """MS-BE-01: 读取剪辑台项目（SRT/segments）。"""
    data = get_studio_project(db, media_task_id, current_user)
    if not data:
        return error_json_response(404, "视频任务不存在")
    return success_response(data=data)


@router.post("/media-studio/projects/{media_task_id}")
def post_media_studio_project(
    media_task_id: str,
    body: StudioProjectBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """MS-BE-01: 保存剪辑台项目。"""
    data = save_studio_project(
        db,
        media_task_id,
        current_user,
        transcript_zh=body.transcript_zh,
        script_en=body.script_en,
        srt_url=body.srt_url,
        segments=body.segments,
        asr_backend=body.asr_backend,
        localization_provider=body.localization_provider,
        output_url=body.output_url,
    )
    if not data:
        return error_json_response(404, "视频任务不存在")
    return success_response(data=data, message="剪辑台项目已保存")


@router.post("/video-dub/transcribe")
async def transcribe_video(
    body: TranscribeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1: 中文听写（异步入队，轮询 GET /video-dub/jobs/{job_id}）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    job, job_err = create_cross_border_job(
        db,
        tenant=tenant,
        user=current_user,
        media_task_id=body.media_task_id,
        kind="transcribe",
    )
    if job_err:
        return error_json_response(job_err["code"], job_err["message"])
    backend = dispatch_cross_border_job(str(job.id))
    data = serialize_cross_border_job(job)
    data["dispatch"] = backend
    return success_response(data=data, message="听写任务已入队，请轮询进度")


@router.get("/video-dub/jobs/{job_id}")
def get_video_dub_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1: 查询听写/出海任务进度与结果。"""
    task = get_cross_border_job(db, job_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")
    return success_response(data=serialize_cross_border_job(task))


@router.get("/video-dub/jobs/{job_id}/events")
async def stream_video_dub_job_events(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W1: SSE 推送听写/出海任务进度（终态后自动结束）。"""
    task = get_cross_border_job(db, job_id, current_user)
    if not task:
        return error_json_response(404, "任务不存在")
    return StreamingResponse(
        stream_cross_border_job_events(db, job_id, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/media-studio/capabilities")
def get_media_studio_capabilities(
    current_user: User = Depends(get_current_user),
):
    """全媒体工作室：ASR / 剪辑适配器 / TTS 能力探测（无假配置）。"""
    _ = current_user
    return success_response(data=build_media_studio_capabilities())


@router.get("/video-dub/tts-status")
def get_tts_status_endpoint(
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_tts_status_endpoint）：处理相关业务逻辑并返回结果。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    _ = current_user
    return success_response(data=tts_status())


@router.get("/video-dub/voices")
async def get_tts_voices(
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_tts_voices）：处理相关业务逻辑并返回结果。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    voices = await list_english_voices()
    return success_response(data={"voices": voices})


@router.get("/product-candidates")
def get_product_candidates(
    survey_id: str | None = None,
    category_id: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """产业带 AI 调研候选 — 浏览，不自动入库。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    data = list_product_candidates(
        survey_id=survey_id,
        category_id=category_id,
        search=search,
        page=page,
        page_size=min(page_size, 100),
    )
    return success_response(data=data)


@router.post("/product-candidates/import")
def post_import_candidates(
    body: ImportCandidatesBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """勾选导入产品库（默认未上架）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    data = import_product_candidates(
        db,
        candidate_ids=body.candidate_ids,
        survey_id=body.survey_id,
        created_by=str(current_user.id),
        activate=body.activate,
    )
    return success_response(data=data, message=f"已导入 {data.get('imported_count', 0)} 条候选")


@router.get("/seo-keywords/preview")
def seo_keywords_preview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W3: 大城+河间词库预览。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    return success_response(data=preview_belt_keywords(db, tenant))


@router.post("/seo-keywords/seed")
def seo_keywords_seed(
    body: SeedKeywordsBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """W3: 入库产业带 SEO 词（租户管理员）。"""
    if current_user.role not in ("super_admin", "admin", "tenant_admin"):
        return error_response(403, "仅管理员可入库词库")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    data = seed_keywords_for_tenant(
        db, belt_id=body.belt_id, include_ranking=body.include_ranking
    )
    return success_response(data=data, message=data.get("message") or "词库入库完成")
