"""矩阵发布零配置引导 — 自动补平台、占位账号、内容母版草稿。"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.services.platform_account_service import upsert_bound_account
from app.services.platform_catalog import resolve_or_create_platform_by_name


def ensure_platforms_for_names(db: Session, names: list[str], *, region: str = "cn") -> list[str]:
    """确保 catalog 平台入库，返回 platform_id 列表。"""
    ids: list[str] = []
    for name in names:
        plat = resolve_or_create_platform_by_name(
            db,
            name,
            region=region,
            content_type="article",
        )
        if plat:
            ids.append(str(plat.id))
    db.commit()
    return ids


def ensure_placeholder_accounts(
    db: Session,
    *,
    tenant_id: str,
    platform_ids: list[str],
) -> list[dict[str, Any]]:
    """为租户创建占位 platform_account（logged_out），便于先排队 PublishTask。"""
    created: list[dict[str, Any]] = []
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    label = (tenant.name if tenant else "tenant")[:32]
    for pid in platform_ids:
        plat = db.query(Platform).filter(Platform.id == pid).first()
        if not plat:
            continue
        existing = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.tenant_id == tenant_id,
                PlatformAccount.platform_id == pid,
                PlatformAccount.is_active.is_(True),
            )
            .first()
        )
        if existing:
            continue
        account, was_new = upsert_bound_account(
            db,
            tenant_id=tenant_id,
            platform=plat,
            payload={
                "account_name": f"{label}-{plat.name}",
                "username": f"stub_{tenant_id[:8]}_{plat.name}",
                "login_status": "logged_out",
            },
        )
        if was_new:
            created.append(
                {
                    "platform_id": pid,
                    "platform_name": plat.name,
                    "account_id": str(account.id),
                    "stub": True,
                }
            )
    db.commit()
    return created


def ensure_matrix_content_draft(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    product_hint: str | None = None,
) -> str:
    """无母版草稿时自动创建一篇矩阵用 ContentMaster。"""
    existing = (
        db.query(ContentMaster)
        .filter(
            ContentMaster.tenant_id == tenant_id,
            ContentMaster.status.in_(("draft", "ready")),
        )
        .order_by(ContentMaster.created_at.desc())
        .first()
    )
    if existing:
        return str(existing.id)

    hint = (product_hint or message or "建材出口").strip()[:120]
    body = (
        message.strip()
        or f"{hint} — B2B export overview. Contact us for MOQ, specs and delivery."
    )
    master = ContentMaster(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        title=f"[矩阵] {hint[:80]}",
        body=body,
        content_type="article",
        status="draft",
    )
    db.add(master)
    db.commit()
    return str(master.id)


def bootstrap_matrix_publish_context(
    db: Session,
    *,
    tenant_id: str,
    context: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    """
    零配置补全：平台入库 → 占位账号 → 内容母版。
    context.auto_bootstrap=false 可关闭。
    """
    from app.services.ubrain.matrix_publish_service import default_platform_names, resolve_platform_ids
    if context.get("auto_bootstrap") is False:
        return context

    locale = str(context.get("locale") or "zh")
    region = "cn" if locale.startswith("zh") else "global"
    names = context.get("platforms") or default_platform_names(locale=locale)
    platform_ids = [str(x) for x in (context.get("platform_ids") or []) if x]
    if not platform_ids:
        platform_ids = ensure_platforms_for_names(db, [str(n) for n in names], region=region)
        if not platform_ids:
            _, bindings = resolve_platform_ids(db, names, tenant_id=tenant_id)
            platform_ids = [b["platform_id"] for b in bindings if b.get("platform_id")]

    stubs = ensure_placeholder_accounts(db, tenant_id=tenant_id, platform_ids=platform_ids)
    master_id = context.get("content_master_id") or context.get("fallback_master_id")
    if not master_id:
        master_id = ensure_matrix_content_draft(
            db,
            tenant_id=tenant_id,
            message=message,
            product_hint=str(context.get("product_hint") or context.get("content_source") or ""),
        )

    out = dict(context)
    out["platform_ids"] = platform_ids
    out["fallback_master_id"] = master_id
    out["_bootstrap"] = {
        "platform_ids": platform_ids,
        "content_master_id": master_id,
        "stub_accounts": stubs,
        "note": "已自动创建占位账号与内容母版；真发前请在发布台完成 Cookie/OAuth 登录",
    }
    return out
