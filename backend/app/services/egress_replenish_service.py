# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IPRoyal 缓冲池补充与永续续费服务（长期养号核心）。

职责：
1. 缓冲池水位监控 + 批量采购补充
2. 到期前自动续费同一IP（永不过期）
3. 续费失败告警（飞书/企微webhook）
4. 过期IP清理
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.egress import EgressCostRecord, EgressEndpoint, EgressPoolReplenishJob

logger = logging.getLogger(__name__)

# 成本参考（美分）: 60天≈$2.55/IP，90天≈$2.40/IP
_COST_PER_IP_CENTS = {
    30: 270,
    60: 255,
    90: 240,
}


def _now_utc() -> datetime:
    """_now_utc。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc)


def _get_iproyal_client():
    """延迟导入避免循环依赖。"""
    from app.services.egress.iproyal_client import IPRoyalClient
    token = (settings.IPROYAL_API_TOKEN or "").strip()
    if not token:
        raise RuntimeError("IPROYAL_API_TOKEN 未配置")
    return IPRoyalClient(
        api_token=token,
        api_base=settings.IPROYAL_API_BASE or "https://apid.iproyal.com/v1/reseller",
    )


def _record_cost(
    db: Session,
    *,
    endpoint_id: str | None,
    operation: str,
    iproyal_order_id: int | None,
    quantity: int,
    plan_days: int,
    raw: Any = None,
    error_message: str | None = None,
) -> None:
    """写入成本/续费记录。"""
    unit = _COST_PER_IP_CENTS.get(plan_days, 255)
    rec = EgressCostRecord(
        endpoint_id=endpoint_id,
        provider="iproyal",
        operation=operation,
        iproyal_order_id=iproyal_order_id,
        quantity=quantity,
        unit_price_cents=unit,
        total_price_cents=unit * quantity,
        plan_days=plan_days,
        raw_response=raw if isinstance(raw, dict) else {"raw": str(raw)[:500]},
        error_message=error_message,
    )
    db.add(rec)
    db.commit()


def _send_alert(message: str) -> None:
    """发送告警到 webhook（飞书/企微）。"""
    webhook_url = (settings.IPROYAL_ALERT_WEBHOOK_URL or "").strip()
    if not webhook_url:
        logger.warning("[IPRoyal告警] %s (未配置 webhook)", message)
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            # 兼容飞书/企微/通用webhook
            payload = {
                "msg_type": "text",
                "content": {"text": f"[IPRoyal告警] {message}"},
                "text": f"[IPRoyal告警] {message}",
            }
            client.post(webhook_url, json=payload)
    except Exception as exc:
        logger.error("发送告警失败: %s", exc)


# ── 缓冲池补充 ──────────────────────────────────────────────


def check_and_replenish_pool(db: Session) -> dict[str, Any]:
    """检查缓冲池水位，不足时触发批量采购。

    返回: {"available": N, "low_watermark": M, "replenish_triggered": bool}
    """
    available_count = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.slot_status == "available",
            EgressEndpoint.provider == "iproyal",
        )
        .count()
    )
    watermark = settings.IPROYAL_POOL_LOW_WATERMARK
    result = {
        "available": available_count,
        "low_watermark": watermark,
        "replenish_triggered": False,
    }
    if available_count < watermark:
        result["replenish_triggered"] = True
        batch_size = settings.IPROYAL_BATCH_SIZE
        logger.info(
            "IPRoyal 池水位 %d < %d，触发补充 %d 个",
            available_count, watermark, batch_size,
        )
        _place_iproyal_order(db, batch_size=batch_size)

    return result


def _place_iproyal_order(db: Session, batch_size: int) -> dict[str, Any]:
    """调用 IPRoyal API 批量下单并创建 endpoint。"""
    job = EgressPoolReplenishJob(
        status="ordering",
        batch_size=batch_size,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        client = _get_iproyal_client()
        order = client.create_order(
            product_id=settings.IPROYAL_PRODUCT_ID,
            plan_id=settings.IPROYAL_PLAN_ID,
            location_id=settings.IPROYAL_LOCATION_ID,
            quantity=batch_size,
        )
        job.iproyal_order_id = order.order_id
        job.status = "stocking"
        db.commit()
        # 从订单中解析每个代理IP，创建 EgressEndpoint
        created = 0
        proxies = order.proxies
        http_port = order.ports.get("http|https", order.ports.get("http", 12323))
        socks_port = order.ports.get("socks5", 12324)
        # 解析 expire_date
        expire_dt = None
        if order.expire_date:
            try:
                expire_dt = datetime.strptime(
                    order.expire_date, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                logger.warning("无法解析 IPRoyal expire_date: %s", order.expire_date)

        if not proxies:
            # 某些情况下 proxy_data 为空，但订单已创建
            # 创建单个 endpoint 记录订单
            endpoint = EgressEndpoint(
                region="global",
                host=f"iproyal-order-{order.order_id}.pending",
                port=int(http_port) if http_port else 12323,
                provider="iproyal",
                slot_status="available",
                label=f"IPRoyal 住宅ISP · {order.location}",
                upstream_ref=f"iproyal-{order.order_id}",
                iproyal_order_id=order.order_id,
                expire_date=expire_dt,
            )
            db.add(endpoint)
            created = 1
        else:
            for p in proxies:
                ip = p.get("ip", "")
                username = p.get("username", p.get("login", ""))
                password = p.get("password", p.get("pass", ""))
                if not ip:
                    continue

                endpoint = EgressEndpoint(
                    region="global",
                    host=ip,
                    port=int(http_port) if http_port else 12323,
                    provider="iproyal",
                    slot_status="available",
                    label=f"IPRoyal 住宅ISP · {order.location}",
                    upstream_ref=f"iproyal-{order.order_id}",
                    proxy_username=username,
                    proxy_password=password,
                    iproyal_order_id=order.order_id,
                    expire_date=expire_dt,
                )
                db.add(endpoint)
                created += 1

        # 记录成本
        _record_cost(
            db,
            operation="purchase",
            iproyal_order_id=order.order_id,
            quantity=created or batch_size,
            plan_days=settings.IPROYAL_PLAN_ID,  # 近似
            raw=order.raw,
        )
        job.status = "completed"
        job.endpoints_created = created
        job.finished_at = _now_utc()
        db.commit()
        logger.info(
            "IPRoyal 补充完成: order=%d, created=%d endpoints",
            order.order_id, created,
        )
        return {"ok": True, "order_id": order.order_id, "created": created}

    except Exception as exc:
        logger.error("IPRoyal 补充失败: %s", exc)
        job.status = "failed"
        job.error_message = str(exc)[:500]
        job.finished_at = _now_utc()
        db.commit()
        _send_alert(f"缓冲池补充失败: {exc}")
        return {"ok": False, "error": str(exc)}


# ── 永续续费（养号核心）──────────────────────────────────────


def auto_renew_expiring_ips(db: Session) -> dict[str, Any]:
    """检查到期前N天的IP，自动续费同一IP。

    核心逻辑：调用 POST /orders/{id}/extend 续费，IP地址不变。
    """
    renew_days = settings.IPROYAL_AUTO_RENEW_DAYS
    threshold = _now_utc() + timedelta(days=renew_days)
    # 查找需要续费的 endpoint（iproyal + assigned + 即将到期）
    expiring = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "assigned",
            EgressEndpoint.expire_date.isnot(None),
            EgressEndpoint.expire_date <= threshold,
        )
        .all()
    )
    if not expiring:
        return {"checked": 0, "renewed": 0, "failed": 0}

    renewed = 0
    failed = 0
    for ep in expiring:
        try:
            result = _renew_single_endpoint(db, ep)
            if result.get("ok"):
                renewed += 1
            else:
                failed += 1
        except Exception as exc:
            logger.error("续费 endpoint %s 失败: %s", ep.id, exc)
            failed += 1
            _record_cost(
                db,
                endpoint_id=str(ep.id),
                operation="renew_failed",
                iproyal_order_id=ep.iproyal_order_id,
                quantity=1,
                plan_days=settings.IPROYAL_RENEW_PLAN_ID,
                error_message=str(exc)[:500],
            )

    if failed > 0:
        _send_alert(
            f"续费结果: 共{len(expiring)}个IP需续费，"
            f"成功{renewed}个，失败{failed}个。"
            f"请立即检查！养号IP过期=前功尽弃！"
        )

    return {
        "checked": len(expiring),
        "renewed": renewed,
        "failed": failed,
    }


def _renew_single_endpoint(db: Session, ep: EgressEndpoint) -> dict[str, Any]:
    """续费单个 endpoint 的IP。"""
    if not ep.iproyal_order_id:
        return {"ok": False, "reason": "no_iproyal_order_id"}

    client = _get_iproyal_client()
    plan_id = settings.IPROYAL_RENEW_PLAN_ID
    try:
        result = client.extend_order(ep.iproyal_order_id, plan_id=plan_id)
    except Exception as exc:
        logger.error("IPRoyal extend_order 失败 (order=%d): %s", ep.iproyal_order_id, exc)
        return {"ok": False, "reason": str(exc)}

    # 续费成功，更新 expire_date
    new_expire = None
    if isinstance(result, dict):
        new_expire_str = result.get("expire_date", "")
        if new_expire_str:
            try:
                new_expire = datetime.strptime(
                    new_expire_str, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

    if not new_expire:
        # 如果API没返回新到期日，手动加上计划天数
        base = ep.expire_date or _now_utc()
        new_expire = base + timedelta(days=plan_id)

    ep.expire_date = new_expire
    ep.renew_count = (ep.renew_count or 0) + 1
    ep.updated_at = _now_utc()
    db.commit()
    _record_cost(
        db,
        endpoint_id=str(ep.id),
        operation="renew",
        iproyal_order_id=ep.iproyal_order_id,
        quantity=1,
        plan_days=plan_id,
        raw=result if isinstance(result, dict) else {"raw": str(result)},
    )
    logger.info(
        "IPRoyal IP续费成功: endpoint=%s, order=%d, new_expire=%s, renew_count=%d",
        ep.id, ep.iproyal_order_id, new_expire, ep.renew_count,
    )
    return {"ok": True, "endpoint_id": str(ep.id), "new_expire": new_expire.isoformat()}


# ── 过期清理 ─────────────────────────────────────────────────


def cleanup_expired_ips(db: Session) -> dict[str, Any]:
    """将续费失败且已过期的IP标记为 disabled。

    注意：只有在 auto_renew 多次失败后才会走到这里。
    已分配给租户的IP过期会触发严重告警。
    """
    now = _now_utc()
    expired = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.expire_date.isnot(None),
            EgressEndpoint.expire_date < now,
            EgressEndpoint.slot_status.in_(("assigned", "available")),
        )
        .all()
    )
    disabled_count = 0
    assigned_expired = 0
    for ep in expired:
        was_assigned = ep.slot_status == "assigned"
        ep.slot_status = "disabled"
        ep.provision_error = "IP已过期（续费失败）"
        ep.updated_at = now
        disabled_count += 1
        if was_assigned:
            assigned_expired += 1

    if disabled_count > 0:
        db.commit()

    if assigned_expired > 0:
        _send_alert(
            f"严重: {assigned_expired}个已分配给租户的IP过期！"
            f"养号可能受影响，请立即人工介入！"
        )

    return {"disabled": disabled_count, "assigned_expired": assigned_expired}


# ── 补充后的待处理任务分配 ────────────────────────────────────


def fulfill_pending_jobs_from_pool(db: Session) -> dict[str, Any]:
    """新IP到货后，自动分配给排队等待的租户 job。"""
    from app.services.egress_jit_provision_service import (
        process_pending_provision_jobs,
        schedule_provision_jobs,
    )
    result = process_pending_provision_jobs(db, limit=20)
    return result
