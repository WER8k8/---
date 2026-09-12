"""矩阵发布 — 计划预览、PublishTask 创建、视频真发统一入口。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount
from app.services.content_master_publish_service import publish_auto_variants
from app.services.geo.platform_rank_registry import publish_order_for_ranking
from app.services.publish_workers.tier_router import preflight_workers
from app.services.ubrain.matrix_publish_bootstrap import bootstrap_matrix_publish_context


def default_platform_names(*, locale: str = "zh", limit: int = 4) -> list[str]:
    """default_platform_names。

    参数说明：
    :param locale: 参数 locale
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    region = "cn" if (locale or "zh").startswith("zh") else "global"
    return publish_order_for_ranking(region=region, live_only=False, limit=limit)


def _match_platform(db: Session, name: str) -> Platform | None:
    """_match_platform。

    参数说明：
    :param db: 参数 db
    :param name: 参数 name
    :return: 返回处理结果。
    """
    raw = (name or "").strip()
    if not raw:
        return None
    plat = (
        db.query(Platform)
        .filter(Platform.is_active.is_(True), Platform.name == raw)
        .first()
    )
    if plat:
        return plat
    short = raw.split("(")[0].split("（")[0].strip()
    for candidate in (short, raw):
        if not candidate:
            continue
        plat = (
            db.query(Platform)
            .filter(Platform.is_active.is_(True), Platform.name.contains(candidate))
            .first()
        )
        if plat:
            return plat
    return None


def resolve_platform_ids(
    db: Session,
    names: list[str],
    *,
    tenant_id: str | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    """平台名 → platform_id；附带租户账号绑定态。"""
    ids: list[str] = []
    bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in names:
        plat = _match_platform(db, name)
        if plat is None:
            bindings.append({"platform_name": name, "matched": False, "reason": "platform_not_found"})
            continue
        if plat.id in seen:
            continue
        seen.add(plat.id)
        ids.append(str(plat.id))
        account: PlatformAccount | None = None
        if tenant_id:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.platform_id == plat.id,
                    PlatformAccount.tenant_id == tenant_id,
                    PlatformAccount.is_active.is_(True),
                )
                .first()
            )
        bindings.append(
            {
                "platform_id": str(plat.id),
                "platform_name": plat.name,
                "matched": True,
                "has_account": account is not None,
                "login_status": (account.login_status if account else None),
                "account_id": str(account.id) if account else None,
            }
        )
    return ids, bindings


def build_matrix_publish_plan(ctx: dict[str, Any]) -> dict[str, Any]:
    """build_matrix_publish_plan。

    参数说明：
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    locale = str(ctx.get("locale") or "zh")
    platforms = ctx.get("platforms") or default_platform_names(locale=locale)
    platforms = [str(p) for p in platforms][:8]
    return {
        "platforms": platforms,
        "content_source": ctx.get("content_source") or ctx.get("content_master_id") or "content_master",
        "cta": ctx.get("cta") or "导向独立域询盘表单/电话",
        "write_back": "publish_tasks",
        "human_confirmation_required": True,
    }


def _build_matrix_publish_plan(db, ctx, tenant_id, preflight):
    """_build_matrix_publish_plan。

    参数说明：
    :param db: 参数 db
    :param ctx: 参数 ctx
    :param tenant_id: 参数 tenant_id
    :param preflight: 参数 preflight
    :return: 返回处理结果。
    """
    plan = build_matrix_publish_plan(ctx)
    names = plan.get("platforms") or []
    _, bindings = resolve_platform_ids(db, names, tenant_id=tenant_id)
    from app.services.foreign_trade.matrix_oauth_publish_gate_service import (
        check_platform_oauth_gate,
    )
    for binding in bindings:
        pname = binding.get("platform_name")
        if pname and binding.get("matched"):
            gate = check_platform_oauth_gate(db, tenant_id=tenant_id, platform_name=pname)
            binding["oauth_gate"] = gate
            binding["selectable"] = gate.get("selectable")
    plan["preflight"] = preflight
    plan["platform_bindings"] = bindings
    plan["needs_confirmation"] = True
    plan["human_review_required"] = True
    plan["status"] = "awaiting_confirmation"
    plan["next_step"] = (
        "确认后在 context 设置 human_confirmed=true；"
        "默认 auto_bootstrap=true 将自动补平台占位账号与内容母版。"
    )
    return plan


def _run_matrix_video_publish(db, tenant_id, message, user_id, ctx, preflight):
    """_run_matrix_video_publish。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param message: 参数 message
    :param user_id: 参数 user_id
    :param ctx: 参数 ctx
    :param preflight: 参数 preflight
    :return: 返回处理结果。
    """
    from app.services.hermes.video_matrix_workflow import run_video_matrix_v1
    result = run_video_matrix_v1(
        db,
        tenant_id=tenant_id,
        message=message,
        user_id=user_id,
        context=ctx,
    )
    result.setdefault("mode", "video_matrix")
    result["preflight"] = preflight
    return result


def _build_matrix_publish_success(pub, ctx, preflight):
    """_build_matrix_publish_success。

    参数说明：
    :param pub: 参数 pub
    :param ctx: 参数 ctx
    :param preflight: 参数 preflight
    :return: 返回处理结果。
    """
    return {
        "status": "queued",
        "mode": "content_master_publish",
        "workflow": "matrix_publish_v2",
        "task_ids": pub["task_ids"],
        "count": pub["count"],
        "matches": pub["matches"],
        "preflight": preflight,
        "write_back": "publish_tasks",
        "bootstrap": ctx.get("_bootstrap"),
        "reply": f"已创建 {pub['count']} 个矩阵发布任务，发布 Worker 将处理 pending 队列。",
    }


def execute_matrix_publish(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    context: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """矩阵发布主入口：未确认 → 计划；确认 + 视频 → video_matrix；确认 + 图文 → PublishTask。"""
    ctx = dict(context or {})
    preflight = preflight_workers()
    if not ctx.get("human_confirmed"):
        return _build_matrix_publish_plan(db, ctx, tenant_id, preflight)

    ctx = bootstrap_matrix_publish_context(
        db,
        tenant_id=tenant_id,
        context=ctx,
        message=message,
    )
    media_task_id = (ctx.get("media_task_id") or "").strip()
    if media_task_id:
        return _run_matrix_video_publish(db, tenant_id, message, user_id, ctx, preflight)

    platform_ids = [str(x) for x in (ctx.get("platform_ids") or []) if x]
    resolved_names: list[str] = [str(n) for n in (ctx.get("platforms") or []) if n]
    if not platform_ids:
        resolved_names = ctx.get("platforms") or default_platform_names(
            locale=str(ctx.get("locale") or "zh")
        )
        platform_ids, bindings = resolve_platform_ids(db, resolved_names, tenant_id=tenant_id)
        if not platform_ids:
            return {
                "status": "failed",
                "error": "no_matching_platforms",
                "platform_bindings": bindings,
                "preflight": preflight,
                "next_step": "请先在发布台绑定平台账号并确保平台已入库",
            }

    from app.services.foreign_trade.matrix_oauth_publish_gate_service import (
        assert_matrix_oauth_before_publish,
    )
    gate_names = list(resolved_names)
    if not gate_names and platform_ids:
        plats = db.query(Platform).filter(Platform.id.in_(platform_ids)).all()
        gate_names = [p.name for p in plats]
    oauth_block = assert_matrix_oauth_before_publish(
        db, tenant_id=tenant_id, platform_names=gate_names
    )
    if oauth_block:
        oauth_block["preflight"] = preflight
        return oauth_block

    try:
        from app.models.content_master import ContentMaster
        master_for_check = None
        mid = ctx.get("content_master_id") or ctx.get("fallback_master_id")
        if mid:
            master_for_check = (
                db.query(ContentMaster).filter(ContentMaster.id == mid).first()
            )
        from app.services.foreign_trade.publish_preflight_checklist_service import (
            assert_publish_allowed,
        )
        preflight = assert_publish_allowed(master_for_check, ctx)
        if preflight.get("blocked"):
            preflight["preflight_workers"] = preflight_workers()
            return preflight

        pub = publish_auto_variants(
            db,
            tenant_id=tenant_id,
            platform_ids=platform_ids,
            draft_ids=ctx.get("draft_ids"),
            fallback_master_id=ctx.get("content_master_id") or ctx.get("fallback_master_id"),
            primary_url=ctx.get("primary_url"),
            secondary_url=ctx.get("secondary_url"),
            utm=ctx.get("utm"),
            utm_campaign=ctx.get("utm_campaign"),
        )
    except ValueError as exc:
        err = str(exc)
        return {
            "status": "failed",
            "error": err,
            "preflight": preflight,
            "next_step": (
                "请先创建 content_master 草稿并绑定 platform_accounts"
                if err in ("no_drafts", "no_tasks_created", "no_account")
                else None
            ),
        }

    return _build_matrix_publish_success(pub, ctx, preflight)
