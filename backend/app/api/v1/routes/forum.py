"""论坛 Sidecar API — 状态、租户配置、Webhook（Apache Answer）。"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.forum_sidecar_service import (
    forum_sidecar_status,
    get_tenant_forum_config,
    update_tenant_forum_config,
)
from app.services.forum_webhook_service import (
    ingest_forum_webhook,
    resolve_tenant_for_webhook,
    verify_webhook_secret,
)
from app.services.cross_border.forum_language_bridge_service import (
    draft_forum_answer_en,
    summarize_forum_question_zh,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/forum", tags=["论坛Sidecar"])


def _resolve_tenant(db: Session, user: User):
    """
    处理 _resolve_tenant 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    from app.api.v1.routes.client import _resolve_tenant as client_resolve
    return client_resolve(db, user)


class ForumConfigBody(BaseModel):
    enabled: bool | None = None
    embed_url: str | None = Field(None, max_length=500)
    public_path: str | None = Field(None, max_length=200)
    rotate_webhook_secret: bool = False


class ForumTranslateBody(BaseModel):
    mode: Literal["question_to_zh", "answer_to_en"]
    text: str = Field(..., min_length=1, max_length=8000)
    context_title: str | None = Field(None, max_length=300)
    context_body: str | None = Field(None, max_length=4000)
    tone: str = "helpful"


@router.get("/status")
def forum_status(current_user: User = Depends(get_current_user)):
    """Sidecar 健康（Admin / 租户可读）。"""
    return success_response(data=forum_sidecar_status())


@router.get("/config")
def forum_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 forum_config 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    api_base = f"{settings.API_V1_PREFIX}"
    return success_response(data=get_tenant_forum_config(tenant, api_base=api_base))


@router.put("/config")
def forum_config_update(
    body: ForumConfigBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 forum_config_update 相关业务逻辑。

    :param body: 入参 (ForumConfigBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if current_user.role not in ("super_admin", "admin", "tenant_admin"):
        return error_response(403, "仅管理员可修改论坛配置")
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    update_tenant_forum_config(
        tenant,
        enabled=body.enabled,
        embed_url=body.embed_url,
        public_path=body.public_path,
        rotate_webhook_secret=body.rotate_webhook_secret,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return success_response(
        data=get_tenant_forum_config(tenant, api_base=settings.API_V1_PREFIX),
        message="论坛配置已保存",
    )


@router.get("/setup-guide")
def forum_setup_guide(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 forum_setup_guide 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    cfg = get_tenant_forum_config(tenant, api_base=settings.API_V1_PREFIX)
    return success_response(
        data={
            "steps": [
                "docker compose -f deploy/examples/forum-sidecar/compose.yml up -d",
                "浏览器打开 Sidecar :9080 完成 Answer 初始化",
                "Client → 买家问答：开启嵌入并保存",
                f"Answer 管理后台配置 Webhook → POST {cfg['webhook_url']}",
                "请求头：X-Forum-Webhook-Secret、X-Tenant-Id",
            ],
            "config": cfg,
            "reverse_proxy": "deploy/examples/forum-sidecar/Caddyfile.snippet",
        }
    )


@router.post("/translate-qa")
async def forum_translate_qa(
    body: ForumTranslateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """论坛语言桥：英问中读 / 中答英发（人工确认后复制到 Answer）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    text = body.text.strip()
    try:
        if body.mode == "question_to_zh":
            data = await summarize_forum_question_zh(
                db,
                tenant,
                question_text=text,
                question_title=body.context_title,
            )
        else:
            if not (body.context_title or "").strip():
                return error_response(400, "中答英发需填写 context_title（买家问题标题）")
            data = await draft_forum_answer_en(
                db,
                tenant,
                question_title=body.context_title or "",
                question_body=body.context_body or "",
                boss_answer_zh=text,
                tone=body.tone,
            )
    except RuntimeError as exc:
        return error_response(503, str(exc))
    return success_response(data=data, message="草稿已生成，发布前须人工确认")


@router.post("/webhook")
async def forum_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_forum_webhook_secret: str | None = Header(None, alias="X-Forum-Webhook-Secret"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-Id"),
):
    """Answer / 自定义论坛 → SEO 候选词入库。"""
    try:
        payload: dict[str, Any] = await request.json()
    except (json.JSONDecodeError, Exception):
        return error_response(400, "需要 JSON body")

    if not isinstance(payload, dict):
        return error_response(400, "无效 payload")

    tenant_id = x_tenant_id or payload.get("tenant_id")
    domain = payload.get("tenant_domain") or payload.get("domain")
    tenant = resolve_tenant_for_webhook(db, str(tenant_id) if tenant_id else None, str(domain) if domain else None)
    if not verify_webhook_secret(tenant, x_forum_webhook_secret):
        return error_response(403, "webhook 密钥无效")

    result = ingest_forum_webhook(db, tenant=tenant, payload=payload)
    if not result.get("ok"):
        return error_response(400, result.get("error") or "处理失败")
    return success_response(data=result, message=result.get("message"))
