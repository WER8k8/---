# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国内询盘漏斗服务 (Domestic Inquiry Service)。

与外贸漏斗清晰隔离，支持国内三大主力买家类型：
1. 工程采购商 (engineering)：地产、装修总包、工装集采
2. 区域代理商 (distributor)：省级/市级建材代理
3. 批发商 (wholesaler)：建材批发市场、仓储式电商
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DomesticBuyerType(str, Enum):
    ENGINEERING = "engineering"
    DISTRIBUTOR = "distributor"
    WHOLESALER = "wholesaler"


class DomesticInquiryStage(str, Enum):
    INQUIRY = "inquiry"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    SAMPLE = "sample"
    DEAL = "deal"
    LOST = "lost"


class DomesticInquiryService:
    """国内询盘与内贸客户生命周期服务。"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def create_domestic_inquiry(
        self,
        tenant_id: str,
        *,
        buyer_name: str,
        buyer_type: str = "engineering",
        contact_name: str = "",
        contact_phone: str = "",
        contact_wechat: str = "",
        external_userid: str = "",
        product_category: str = "瓷砖",
        quantity_m2: float = 0.0,
        project_name: str = "",
        city: str = "",
        source_channel: str = "wechat",
        vat_type: str = "general",
        vat_rate: float = 0.13,
        note: str = "",
    ) -> Dict[str, Any]:
        """创建国内询盘档案。"""
        b_type = (buyer_type or "engineering").lower()
        if b_type not in {t.value for t in DomesticBuyerType}:
            b_type = DomesticBuyerType.ENGINEERING.value

        v_type = "special" if vat_type == "special" else "general"

        record_data = {
            "tenant_id": tenant_id or "default_tenant",
            "buyer_name": (buyer_name or "意向建材采购商").strip(),
            "buyer_type": b_type,
            "contact_name": contact_name.strip(),
            "contact_phone": contact_phone.strip(),
            "contact_wechat": contact_wechat.strip(),
            "external_userid": external_userid.strip(),
            "product_category": product_category.strip() or "瓷砖",
            "quantity_m2": float(quantity_m2 or 0.0),
            "project_name": project_name.strip(),
            "city": city.strip(),
            "source_channel": source_channel.strip() or "wechat",
            "stage": DomesticInquiryStage.INQUIRY.value,
            "currency": "CNY",
            "vat_type": v_type,
            "vat_rate": float(vat_rate or 0.13),
            "logistics_type": "domestic_freight",
            "note": note.strip(),
        }

        if self.db is not None:
            try:
                from app.models.domestic import DomesticInquiry
                inq = DomesticInquiry(**record_data)
                self.db.add(inq)
                self.db.commit()
                self.db.refresh(inq)
                return {
                    "success": True,
                    "inquiry_id": str(inq.id),
                    "buyer_name": inq.buyer_name,
                    "buyer_type": inq.buyer_type,
                    "stage": inq.stage,
                    "currency": inq.currency,
                    "vat_type": inq.vat_type,
                    "vat_rate": inq.vat_rate,
                }
            except Exception as exc:
                logger.warning("DomesticInquiry 入库失败 (降级返回结构化数据): %s", exc)
                try:
                    self.db.rollback()
                except Exception:
                    pass

        import uuid
        mock_id = f"dom_{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "inquiry_id": mock_id,
            **record_data,
            "persisted": False,
        }

    def advance_stage(
        self,
        inquiry_id: str,
        new_stage: str,
        *,
        quote_amount_rmb: Optional[float] = None,
        won_amount_rmb: Optional[float] = None,
        lost_reason: Optional[str] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """流转国内询盘生命周期阶段。"""
        valid_stages = {s.value for s in DomesticInquiryStage}
        target_stage = (new_stage or "").lower()
        if target_stage not in valid_stages:
            return {
                "success": False,
                "reason": f"无效的国内阶段 '{new_stage}'，支持阶段: {list(valid_stages)}",
            }

        res: Dict[str, Any] = {
            "success": True,
            "inquiry_id": inquiry_id,
            "new_stage": target_stage,
            "note": note,
        }

        if self.db is not None:
            try:
                from app.models.domestic import DomesticInquiry
                obj = self.db.query(DomesticInquiry).filter(DomesticInquiry.id == inquiry_id).first()
                if obj:
                    obj.stage = target_stage
                    if quote_amount_rmb is not None:
                        obj.quote_amount_rmb = quote_amount_rmb
                    if won_amount_rmb is not None:
                        obj.won_amount_rmb = won_amount_rmb
                    if lost_reason:
                        obj.lost_reason = lost_reason
                    if note:
                        obj.note = (obj.note or "") + f" | {note}"
                    self.db.commit()
                    self.db.refresh(obj)
                    res["quote_amount_rmb"] = obj.quote_amount_rmb
                    res["won_amount_rmb"] = obj.won_amount_rmb
            except Exception as exc:
                logger.warning("DomesticInquiry 状态流转失败: %s", exc)
                try:
                    self.db.rollback()
                except Exception:
                    pass

        # 挂接经验环 (Evolution Engine)
        if target_stage in ("deal", "lost"):
            try:
                from app.services.acquisition.experience_feed import record_ops_win, record_ops_loss
                if target_stage == "deal":
                    record_ops_win(
                        self.db,
                        tenant_id="domestic",
                        inquiry_id=inquiry_id,
                        amount=won_amount_rmb or quote_amount_rmb or 0.0,
                        currency="CNY",
                        note=note or "国内订单成交",
                    )
                else:
                    record_ops_loss(
                        self.db,
                        tenant_id="domestic",
                        inquiry_id=inquiry_id,
                        reasons=[lost_reason or "其他原因"],
                        note=note or "国内询盘流失",
                    )
            except Exception as exp_err:
                logger.debug("经验反哺钩子捕获并忽略: %s", exp_err)

        return res
