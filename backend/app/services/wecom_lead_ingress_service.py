# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内轨 · 企微线索自动回流服务（Path A · Stage A4 · wecom_ingress）。

设计出处：
- 《多模型设计统一裁定书-2026-09-09》& 2026-10-01 拍板双重玩法（国内轨+海外轨双源入同一主链）；
- 核心约束：
  1. 线索同源化（最高优先）：iYqueCode 承接的国内线索必须带 source_channel="wecom_ingress"
     回流 UJ inquiries —— 两轨线索在 UJ 主链同一漏斗、同一计费、同一归因报表，严禁第二套独立 CRM；
  2. 反欺骗：忽略客户端传入的 source_channel 伪造声明，服务端硬性锁死 "wecom_ingress"；
  3. 联系方式强校验：必须提供 phone / wechat / email 至少一种有效触达方式，无有效触达渠道拒绝落库。
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inquiry import Inquiry

logger = logging.getLogger("uj-wecom-ingress")

FORCED_SOURCE_CHANNEL = "wecom_ingress"
ATTRIBUTION_CHANNEL = "wecom"


class WeComIngressError(Exception):
    """企微接入异常（携带 HTTP 状态码与拒绝原因）。"""

    def __init__(self, reason: str, status_code: int = 400):
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"wecom_ingress_rejected: {reason}")


def verify_bridge_token(token: str | None) -> bool:
    """校验附属系统/侧车桥接令牌（双向鉴权防伪造接入）。"""
    if not token:
        return False
    configured = (
        os.getenv("WECOM_BRIDGE_TOKEN")
        or getattr(settings, "ANNEX_BRIDGE_TOKEN", "")
        or "dev-bridge-token"
    ).strip()
    return token.strip() == configured


def ingest_wecom_lead(
    db: Session,
    payload: dict[str, Any],
    *,
    tenant_id: str | None = None,
) -> Inquiry:
    """将来自企微侧车的客户线索安全规整并直接写入 inquiries 表。

    :param db: SQLAlchemy Session
    :param payload: 客户线索原始报文
    :param tenant_id: 归属租户 ID（可从网关鉴权解析或请求透传）
    :return: 写入成功的 Inquiry 实例
    """
    if not isinstance(payload, dict):
        raise WeComIngressError("payload_must_be_json_object", 400)

    # 1. 提取并强校验联系方式（phone / wechat / email 至少一项）
    phone = (payload.get("phone") or "").strip() or None
    wechat = (payload.get("wechat") or payload.get("external_userid") or "").strip() or None
    email = (payload.get("email") or "").strip() or None

    if not phone and not wechat and not email:
        raise WeComIngressError("missing_contact_channel", 400)

    # 2. 姓名与基本信息清洗
    name = (
        (payload.get("name") or payload.get("customer_name") or payload.get("wechat_name") or "")
        .strip()
        or "企微新客"
    )
    product = (payload.get("product") or payload.get("interest_product") or "").strip() or None
    company = (payload.get("company") or payload.get("corp_name") or "").strip() or None

    # 3. 跟进意向与留言
    message_content = (
        payload.get("message")
        or payload.get("remark")
        or payload.get("inquiryContent")
        or "通过企业微信渠道添加，等待销售建档跟进"
    ).strip()

    # 4. 标签与归因沉淀
    tags = payload.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    channel_code = (payload.get("channel_code") or payload.get("user_code") or "").strip()
    staff_user_id = (payload.get("staff_user_id") or payload.get("user_id") or "").strip()
    assigned_to = (payload.get("assigned_to") or staff_user_id or "").strip() or None

    attribution_data = {
        "channel": ATTRIBUTION_CHANNEL,
        "channel_code": channel_code,
        "staff_user_id": staff_user_id,
        "tags": tags,
        "company": company,
        "raw_source": "iYqueCode",
    }

    # 5. 组装 Inquiry 实体（强制 channel="wecom_ingress"，不可被客户端声明改写）
    inquiry = Inquiry(
        id=str(uuid.uuid4()),
        name=name,
        phone=phone,
        wechat=wechat,
        email=email,
        product=product,
        message=message_content,
        status="pending",
        is_active=True,
        source_channel=FORCED_SOURCE_CHANNEL,
        tenant_id=tenant_id or payload.get("tenant_id"),
        assigned_to=assigned_to,
        attribution_channel=ATTRIBUTION_CHANNEL,
        attribution_data=json.dumps(attribution_data, ensure_ascii=False),
        priority_score=int(payload.get("priority_score") or 60),
        provenance_metadata={
            "ingress": "wecom_bridge",
            "corp_user_id": staff_user_id,
            "tags_count": len(tags),
        },
    )

    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    logger.info(
        "企微新线索入库成功: id=%s name=%s source_channel=%s phone=%s wechat=%s",
        inquiry.id,
        inquiry.name,
        inquiry.source_channel,
        inquiry.phone,
        inquiry.wechat,
    )
    return inquiry
