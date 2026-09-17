# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Accio A2/A3/A4：租户真实询盘上下文 → 草稿、评分与经营快照。"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.finance_honesty import is_excluded_inquiry_payload
from app.services.inquiries_unified_service import InquiriesUnifiedService


def get_latest_inquiry(db: Session, tenant_id: str) -> dict[str, Any] | None:
    """get_latest_inquiry。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    data = InquiriesUnifiedService(db).list_page(
        page=1, page_size=1, tenant_id=tenant_id
    )
    items = data.get("items") or []
    return items[0] if items else None


def resolve_inquiry(
    db: Session,
    tenant_id: str,
    ctx: dict[str, Any],
) -> dict[str, Any] | None:
    """resolve_inquiry。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param ctx: 参数 ctx
    :return: 返回处理结果。
    """
    raw = ctx.get("inquiry")
    if isinstance(raw, dict) and raw.get("id"):
        return raw
    inquiry_id = ctx.get("inquiry_id")
    if inquiry_id:
        page = InquiriesUnifiedService(db).list_page(
            page=1, page_size=50, tenant_id=tenant_id
        )
        for item in page.get("items") or []:
            if str(item.get("id")) == str(inquiry_id):
                return item
    if ctx.get("use_latest_inquiry", True):
        return get_latest_inquiry(db, tenant_id)
    return None


def build_inquiry_reply_draft(
    inquiry: dict[str, Any],
    *,
    tone: str,
    lang: str,
    product_category: str,
) -> tuple[str, dict[str, Any]]:
    """build_inquiry_reply_draft。

    参数说明：
    :param inquiry: 参数 inquiry
    :param tone: 参数 tone
    :param lang: 参数 lang
    :param product_category: 参数 product_category
    :return: 返回处理结果。
    """
    name = inquiry.get("name") or "客户"
    product = inquiry.get("product") or product_category or "建材"
    msg_snip = (inquiry.get("message") or "")[:120]
    phone = inquiry.get("phone") or ""
    if lang == "en":
        reply = (
            f"【{tone} · draft · inquiry #{str(inquiry.get('id', ''))[:8]}】\n"
            f"Dear {name},\n"
            f"Thank you for your inquiry on {product}. "
            f"We noted: \"{msg_snip}\". "
            "Please confirm quantity, destination port and specs (thickness / fire rating). "
            "We will reply with EXW/FOB range and lead time today."
        )
    else:
        reply = (
            f"【{tone} · 询盘回复草稿 · {name}】\n"
            f"感谢咨询{product}。您提到：「{msg_snip}」。"
            "请补充数量、目的港与规格（厚度/防火等级），"
            "我们将在今日内回复报价区间与交期。"
        )
        if phone and len(phone) >= 7:
            masked = f"{phone[:3]}****{phone[-4:]}"
            reply += f"\n（已记录手机 {masked}，建议优先电话跟进）"
    meta = {
        "inquiry_id": inquiry.get("id"),
        "source_channel": inquiry.get("source_channel"),
        "from_real_inquiry": True,
    }
    return reply, meta


def _ssl_ops_counts(db: Session, tenant_id: str) -> tuple[int | None, int | None]:
    """从租户 settings.domain_ssl 统计失败与即将过期（30 天内）。"""
    try:
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return None, None
        raw = tenant.settings or "{}"
        data = json.loads(raw) if isinstance(raw, str) else (raw or {})
        records = data.get("domain_ssl") or {}
        if not isinstance(records, dict):
            return 0, 0
        failed = 0
        expiring = 0
        now = datetime.now(timezone.utc)
        for rec in records.values():
            if not isinstance(rec, dict):
                continue
            if rec.get("status") == "failed":
                failed += 1
            exp = rec.get("expires_at")
            if not exp:
                continue
            try:
                exp_dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                days = (exp_dt - now).days
                if 0 <= days <= 30:
                    expiring += 1
            except (TypeError, ValueError):
                continue
        return failed, expiring
    except Exception:
        return None, None


def _publish_failure_count(db: Session) -> int | None:
    """_publish_failure_count。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    try:
        from app.models.content import PublishTask
        return (
            db.query(PublishTask).filter(PublishTask.status == "failed").count()
        )
    except Exception:
        return None


def _ops_pending_inquiries(
    db: Session,
    tenant_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """拉取待处理真实询盘，返回 (pending, with_phone)。"""
    inq = InquiriesUnifiedService(db).list_page(
        page=1, page_size=100, tenant_id=tenant_id, status="pending"
    )
    pending = [
        i for i in (inq.get("items") or []) if not is_excluded_inquiry_payload(i)
    ]
    with_phone = [
        i for i in pending if re.search(r"1[3-9]\d{9}", str(i.get("phone") or ""))
    ]
    return pending, with_phone


def _ops_prospect_stats(db: Session, tenant_id: str, snapshot: dict[str, Any]) -> None:
    """统计候选客户的 draft_ready / discovered 数量。"""
    try:
        from app.models.ubrain_accio import BuyerProspectLead
        snapshot["prospects_draft_ready"] = (
            db.query(BuyerProspectLead)
            .filter(
                BuyerProspectLead.tenant_id == tenant_id,
                BuyerProspectLead.status == "draft_ready",
            )
            .count()
        )
    except Exception:
        pass
    try:
        from app.models.ubrain_accio import BuyerProspectLead
        snapshot["prospects_discovered"] = (
            db.query(BuyerProspectLead)
            .filter(
                BuyerProspectLead.tenant_id == tenant_id,
                BuyerProspectLead.status == "discovered",
            )
            .count()
        )
    except Exception:
        snapshot["prospects_discovered"] = 0


def _ops_funnel_publish(
    db: Session,
    tenant_id: str,
    snapshot: dict[str, Any],
    pending: list[dict[str, Any]],
    with_phone: list[dict[str, Any]],
) -> None:
    """填充发布漏斗统计。"""
    snapshot["funnel"] = {
        "inquiries_pending": len(pending),
        "inquiries_with_phone": len(with_phone),
        "prospects_discovered": snapshot.get("prospects_discovered", 0),
        "prospects_draft_ready": snapshot.get("prospects_draft_ready", 0),
        "publish_pending": 0,
        "publish_success": 0,
    }
    try:
        from app.models.content import PlatformAccount, PublishTask
        pub_q = (
            db.query(PublishTask)
            .join(PlatformAccount, PublishTask.account_id == PlatformAccount.id)
            .filter(PlatformAccount.tenant_id == tenant_id)
        )
        snapshot["funnel"]["publish_pending"] = pub_q.filter(
            PublishTask.status.in_(("pending", "processing"))
        ).count()
        snapshot["funnel"]["publish_success"] = pub_q.filter(
            PublishTask.status == "success"
        ).count()
    except Exception:
        pass


def _ops_hints(
    snapshot: dict[str, Any],
    ssl_failed: int | None,
    ssl_expiring: int | None,
    pending_count: int,
) -> None:
    """根据各项统计生成经营提示，追加到 snapshot["hints"]。"""
    if pending_count > 5:
        snapshot["hints"].append("未处理询盘较多，建议副驾批量意向分级后优先带手机号。")
    if snapshot["prospects_draft_ready"] > 0:
        snapshot["hints"].append("有候选客户待开发信，可在「卖货执行」区生成草稿。")
    funnel = snapshot.get("funnel") or {}
    if funnel.get("prospects_discovered", 0) > 0:
        snapshot["hints"].append(
            f"有 {funnel['prospects_discovered']} 条「待核实候选」客户，核实后可导出 CSV 标记已联系。"
        )
    if ssl_failed and ssl_failed > 0:
        snapshot["hints"].append(f"有 {ssl_failed} 个域名 SSL 失败，请在域名管理重试签发。")
    if ssl_expiring and ssl_expiring > 0:
        snapshot["hints"].append(f"有 {ssl_expiring} 个证书 30 天内到期，请提前续期。")
    pub_fail = snapshot.get("publish_failures")
    if isinstance(pub_fail, int) and pub_fail > 0:
        snapshot["hints"].append(f"矩阵发布失败任务 {pub_fail} 条，可在运维中心重试。")


def _ops_platform_accounts(db: Session, tenant_id: str, snapshot: dict[str, Any]) -> None:
    """统计平台账号总数与绑定情况。"""
    try:
        from app.models.content import PlatformAccount
        accounts = (
            db.query(PlatformAccount)
            .filter(
                PlatformAccount.tenant_id == tenant_id,
                PlatformAccount.is_active.is_(True),
            )
            .all()
        )
        bound = sum(1 for a in accounts if (a.login_status or "") == "logged_in")
        snapshot["platform_accounts_total"] = len(accounts)
        snapshot["platform_accounts_bound"] = bound
        snapshot["platform_accounts_unbound"] = max(len(accounts) - bound, 0)
        if accounts and bound < len(accounts):
            snapshot["hints"].append(
                f"有 {len(accounts) - bound} 个平台账号未绑定，矩阵发布前请先完成 OAuth/Cookie。"
            )
    except Exception:
        pass


def _ops_ai_quota(db: Session, tenant_id: str, snapshot: dict[str, Any]) -> None:
    """统计租户 AI 配额用量。"""
    try:
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            total = 0
            if tenant.plan:
                total = int(tenant.plan.max_ai_quota or 0)
            used = int(tenant.ai_quota_used or 0)
            snapshot["ai_quota_used"] = used
            snapshot["ai_quota_total"] = total
            if total > 0 and used / total >= 0.85:
                snapshot["hints"].append(
                    f"AI 用量已达 {round(used / total * 100)}%，续费或升级套餐后可继续深度研究。"
                )
    except Exception:
        pass


def tenant_ops_snapshot(db: Session, tenant_id: str) -> dict[str, Any]:
    """Accio A4 轻量经营快照（只读）。"""
    pending, with_phone = _ops_pending_inquiries(db, tenant_id)
    ssl_failed, ssl_expiring = _ssl_ops_counts(db, tenant_id)
    snapshot: dict[str, Any] = {
        "pending_inquiries": len(pending),
        "pending_with_phone": len(with_phone),
        "publish_failures": _publish_failure_count(db),
        "ssl_expiring_soon": ssl_expiring,
        "ssl_failed": ssl_failed,
        "prospects_draft_ready": 0,
    }
    snapshot["hints"] = []
    _ops_prospect_stats(db, tenant_id, snapshot)
    _ops_funnel_publish(db, tenant_id, snapshot, pending, with_phone)
    _ops_hints(snapshot, ssl_failed, ssl_expiring, len(pending))
    _ops_platform_accounts(db, tenant_id, snapshot)
    _ops_ai_quota(db, tenant_id, snapshot)
    return snapshot
