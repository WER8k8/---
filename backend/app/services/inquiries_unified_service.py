"""询盘 v1 / v2 / unified 统一序列化与列表。"""

from __future__ import annotations

import os
import uuid
from typing import Any, Optional

from sqlalchemy import false, inspect, or_
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.user import User


def _column_names() -> set[str]:
    """_column_names。
    :return: 返回处理结果。
    """
    return {c.key for c in inspect(Inquiry).columns}


def serialize_inquiry(row: Inquiry, cols: Optional[set[str]] = None) -> dict[str, Any]:
    """serialize_inquiry。

    参数说明：
    :param row: 参数 row
    :param cols: 参数 cols
    :return: 返回处理结果。
    """
    cols = cols or _column_names()
    if "buyer_id" in cols and getattr(row, "buyer_id", None) is not None:
        return {
            "id": str(row.id),
            "kind": "b2b",
            "subject": getattr(row, "subject", None),
            "message": getattr(row, "message", None),
            "status": row.status,
            "buyer_id": str(row.buyer_id),
            "merchant_id": str(getattr(row, "merchant_id", "")),
            "product_id": str(row.product_id) if getattr(row, "product_id", None) else None,
            "source_channel": getattr(row, "source_channel", None),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    payload = {
        "id": str(row.id),
        "kind": "seo_lead",
        "name": getattr(row, "name", None),
        "phone": getattr(row, "phone", None),
        "email": getattr(row, "email", None),
        "product": getattr(row, "product", None),
        "source_channel": getattr(row, "source_channel", None),
        "message": getattr(row, "message", None),
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "session_id": getattr(row, "session_id", None),
        "landing_path": getattr(row, "landing_path", None),
        "last_click_label": getattr(row, "last_click_label", None),
        "assigned_to": getattr(row, "assigned_to", None),
    }
    if "source_utm" in cols:
        from app.services.foreign_trade.utm_attribution_service import deserialize_utm
        payload["source_utm"] = deserialize_utm(getattr(row, "source_utm", None))
        payload["publish_task_id"] = getattr(row, "publish_task_id", None)
    if "meddpicc_json" in cols:
        from app.services.foreign_trade.inquiry_meddpicc_service import load_meddpicc
        med = load_meddpicc(row)
        payload["meddpicc"] = med
        stage = str(med.get("pipeline_stage") or "").strip().lower()
        if stage:
            payload["pipeline_stage"] = stage
            from app.services.foreign_trade.inquiry_pipeline_service import PIPELINE_STAGES
            payload["pipeline_stage_label"] = next(
                (s["label_zh"] for s in PIPELINE_STAGES if s["id"] == stage),
                stage,
            )
    return payload


class InquiriesUnifiedService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self._cols = _column_names()

    def _base_query(self):
        """_base_query。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        q = self.db.query(Inquiry)
        if "is_active" in self._cols:
            q = q.filter(Inquiry.is_active.is_(True))
        return q

    def list_page(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        tenant_id: Optional[str] = None,
        source_channel: Optional[str] = None,
        assigned_to: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
    ) -> dict[str, Any]:
        """list_page。

        参数说明：
        :param self: 参数 self
        :param page: 参数 page
        :param page_size: 参数 page_size
        :param status: 参数 status
        :param search: 参数 search
        :param tenant_id: 参数 tenant_id
        :param source_channel: 参数 source_channel
        :param assigned_to: 参数 assigned_to
        :param pipeline_stage: 参数 pipeline_stage
        :return: 返回处理结果。
        """
        q = self._base_query()
        if tenant_id:
            tid_str = str(tenant_id)
            if "merchant_id" in self._cols:
                try:
                    uuid.UUID(tid_str)
                    q = q.filter(Inquiry.merchant_id == tid_str)
                except ValueError:
                    q = q.filter(false())
            elif "tenant_id" in self._cols:
                q = q.filter(Inquiry.tenant_id == tid_str)
        if status:
            q = q.filter(Inquiry.status == status)
        if source_channel and "source_channel" in self._cols:
            q = q.filter(Inquiry.source_channel == source_channel)
        if assigned_to and "assigned_to" in self._cols:
            q = q.filter(Inquiry.assigned_to == assigned_to)
        if pipeline_stage and "meddpicc_json" in self._cols:
            q = q.filter(Inquiry.meddpicc_json.contains(f'"pipeline_stage": "{pipeline_stage}"'))
        if search:
            like = f"%{search}%"
            clauses = []
            if "subject" in self._cols:
                clauses.append(Inquiry.subject.ilike(like))
            if "message" in self._cols:
                clauses.append(Inquiry.message.ilike(like))
            if "name" in self._cols:
                clauses.append(Inquiry.name.ilike(like))
            if "phone" in self._cols:
                clauses.append(Inquiry.phone.ilike(like))
            if "email" in self._cols:
                clauses.append(Inquiry.email.ilike(like))
            if "product" in self._cols:
                clauses.append(Inquiry.product.ilike(like))
            if clauses:
                q = q.filter(or_(*clauses))
        total = q.count()
        rows = (
            q.order_by(Inquiry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [serialize_inquiry(r, self._cols) for r in rows]
        try:
            from app.services.foreign_trade.inquiry_pipeline_service import enrich_inquiry_pipeline_fields
            for i, row in enumerate(rows):
                items[i] = enrich_inquiry_pipeline_fields(items[i], row)
        except Exception:
            pass
        try:
            from app.services.ubrain.inquiry_intel_service import enrich_inquiry_intel
            for i, item in enumerate(items):
                items[i] = enrich_inquiry_intel(item)
        except Exception:
            pass
        if "assigned_to" in self._cols:
            assignee_ids = {i["assigned_to"] for i in items if i.get("assigned_to")}
            if assignee_ids:
                users = (
                    self.db.query(User)
                    .filter(User.id.in_(list(assignee_ids)))
                    .all()
                )
                name_map = {str(u.id): u.username for u in users}
                for item in items:
                    aid = item.get("assigned_to")
                    if aid:
                        item["assigned_to_name"] = name_map.get(str(aid))
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "canonical_api": "/api/v1/inquiries/unified",
            "deprecated": ["/api/v1/inquiries/", "/api/v1/inquiries-v2/"],
        }

    def _default_merchant_user_id(self, merchant_id: Optional[str] = None) -> Any:
        """_default_merchant_user_id。

        参数说明：
        :param self: 参数 self
        :param merchant_id: 参数 merchant_id
        :return: 返回处理结果。
        """
        if merchant_id:
            try:
                # 验证并返回字符串格式，兼容SQLite测试环境
                uuid.UUID(str(merchant_id))  # 验证格式
                return str(merchant_id)
            except ValueError as exc:
                raise ValueError("merchant_id 必须是合法 UUID") from exc
        env_id = os.getenv("DEFAULT_MERCHANT_USER_ID", "").strip()
        if env_id:
            try:
                # 验证并返回字符串格式，兼容SQLite测试环境
                uuid.UUID(env_id)  # 验证格式
                return env_id
            except ValueError as exc:
                raise ValueError("DEFAULT_MERCHANT_USER_ID 必须是合法 UUID") from exc
        row = (
            self.db.query(User)
            .filter(User.role.in_(("admin", "super_admin", "merchant")))
            .order_by(User.created_at.asc())
            .first()
        )
        if not row:
            raise ValueError("未配置 DEFAULT_MERCHANT_USER_ID 且无可用商家用户")
        return row.id

    def _default_buyer_user_id(self, merchant_id: Any) -> Any:
        """_default_buyer_user_id。

        参数说明：
        :param self: 参数 self
        :param merchant_id: 参数 merchant_id
        :return: 返回处理结果。
        """
        env_id = os.getenv("DEFAULT_PUBLIC_BUYER_ID", "").strip()
        if env_id:
            # 验证并返回字符串格式，兼容SQLite测试环境
            uuid.UUID(env_id)  # 验证格式
            return env_id
        return merchant_id

    def _build_public_lead_kwargs(
        self,
        *,
        name: str,
        message: str,
        stored_message: str,
        email: Optional[str],
        phone: Optional[str],
        product: Optional[str],
        source_channel: Optional[str],
        merchant_id: Optional[str],
    ) -> dict[str, Any]:
        """按表结构构造询盘写入字段（SEO 表或 B2B 表）。"""
        cols = self._cols
        row_kwargs: dict[str, Any] = {"status": "pending"}
        if "name" in cols:
            row_kwargs.update(
                {
                    "name": name[:120],
                    "phone": phone[:50] if phone else None,
                    "message": stored_message,
                    "email": email,
                    "product": product,
                }
            )
            if "merchant_id" in cols:
                row_kwargs["merchant_id"] = self._default_merchant_user_id(merchant_id)
            if "is_active" in cols:
                row_kwargs["is_active"] = True
            if "source_channel" in cols and source_channel:
                row_kwargs["source_channel"] = source_channel
        elif "buyer_id" in cols and "merchant_id" in cols:
            mid = self._default_merchant_user_id(merchant_id)
            row_kwargs.update(
                {
                    "buyer_id": self._default_buyer_user_id(mid),
                    "merchant_id": mid,
                    "subject": (product or f"Web inquiry from {name}")[:255],
                    "message": stored_message,
                }
            )
            if product and "product_id" in cols:
                try:
                    # 验证并返回字符串格式，兼容SQLite测试环境
                    uuid.UUID(str(product))  # 验证格式
                    row_kwargs["product_id"] = str(product)
                except ValueError:
                    pass
            if "source_channel" in cols and source_channel:
                row_kwargs["source_channel"] = source_channel[:50]
        else:
            raise ValueError("inquiries 表结构无法写入公开询盘")
        return row_kwargs

    def _resolve_public_lead_tenant(
        self,
        *,
        tenant_id: Optional[str],
        merchant_id: Optional[str],
    ) -> Optional[str]:
        """解析公开询盘归属租户 ID。"""
        if tenant_id:
            return tenant_id
        from app.services.traffic_analytics_service import resolve_tenant_id
        return resolve_tenant_id(self.db, merchant_id=merchant_id)

    def _attach_inquiry_analytics(
        self,
        row: Inquiry,
        *,
        session_id: Optional[str],
        landing_path: Optional[str],
        last_click_label: Optional[str],
        merchant_id: Optional[str],
        tid: Optional[str],
        product: Optional[str],
    ) -> None:
        """记录访问归因与转化事件（失败静默）。"""
        try:
            from app.services.traffic_analytics_service import (
                TrafficAnalyticsService,
            )
            TrafficAnalyticsService(self.db).attach_inquiry_attribution(
                row,
                session_id=session_id,
                landing_path=landing_path,
                last_click_label=last_click_label,
                tenant_id=tid,
            )
            if session_id:
                TrafficAnalyticsService(self.db).record_event(
                    event_type="inquiry_submit",
                    session_id=session_id,
                    tenant_id=tid,
                    merchant_id=merchant_id,
                    page_path=landing_path,
                    element_label=last_click_label,
                    product_id=product if product else None,
                    inquiry_id=str(row.id),
                )
            self.db.commit()
            self.db.refresh(row)
        except Exception:
            pass

    def _notify_and_assign_public_lead(self, row: Inquiry) -> None:
        """推送新询盘通知并尝试自动分配（失败静默）。"""
        try:
            from app.services.inquiry_push_service import notify_new_public_inquiry
            notify_new_public_inquiry(self.db, row)
        except Exception:
            pass
        try:
            from app.services.inquiry_lead_assignment_service import auto_assign_platform_lead
            auto_assign_platform_lead(self.db, row)
            self.db.refresh(row)
        except Exception:
            pass

    def _push_goodjob_pool_projection(self, row: Inquiry) -> None:
        """询盘投影推送 GoodJob customer_pool（批次 B 首调用方，失败静默）。"""
        try:
            from app.orchestration.executors.goodjob_executor import (
                build_goodjob_executor,
            )
            from app.services.goodjob.customer_pool_projection import (
                sync_inquiry_to_pool,
            )
            executor = build_goodjob_executor()
            if executor is not None:
                sync_inquiry_to_pool(executor, row)
        except Exception:
            pass

    def _enrich_public_lead_row(self, row: Inquiry) -> dict[str, Any]:
        """序列化询盘并附加行业情报增强（失败静默）。"""
        cols = self._cols
        result = serialize_inquiry(row, cols)
        if result.get("assigned_to"):
            assignee = (
                self.db.query(User)
                .filter(User.id == result["assigned_to"])
                .first()
            )
            if assignee:
                result["assigned_to_name"] = assignee.username
        try:
            from app.services.ubrain.inquiry_intel_service import enrich_inquiry_intel
            result = enrich_inquiry_intel(result)
        except Exception:
            pass
        return result

    def create_public_lead(
        self,
        *,
        name: str,
        message: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        product: Optional[str] = None,
        source_channel: Optional[str] = None,
        merchant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        landing_path: Optional[str] = None,
        last_click_label: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_content: Optional[str] = None,
        publish_task_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """租户站 / StickyImBar 公开询盘（按表结构自动选 SEO 或 B2B 字段）。"""
        from app.services.ubrain.inquiry_discovery_service import (
            attach_discovery_to_message,
            build_discovery_questions,
        )
        discovery_questions = build_discovery_questions(product=product, message=message)
        stored_message = attach_discovery_to_message(message, discovery_questions)
        cols = self._cols

        row_kwargs = self._build_public_lead_kwargs(
            name=name,
            message=message,
            stored_message=stored_message,
            email=email,
            phone=phone,
            product=product,
            source_channel=source_channel,
            merchant_id=merchant_id,
        )
        tid = self._resolve_public_lead_tenant(
            tenant_id=tenant_id, merchant_id=merchant_id
        )
        if tid and "tenant_id" in cols:
            row_kwargs["tenant_id"] = tid

        row = Inquiry(**{k: v for k, v in row_kwargs.items() if k in cols})
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        self._attach_inquiry_analytics(
            row,
            session_id=session_id,
            landing_path=landing_path,
            last_click_label=last_click_label,
            merchant_id=merchant_id,
            tid=tid,
            product=product,
        )
        self._notify_and_assign_public_lead(row)

        # 附加 UTM 归因 + MEDDPICC 评分 + 行业情报
        try:
            from app.services.foreign_trade.inquiry_meddpicc_service import score_inquiry_meddpicc
            from app.services.foreign_trade.utm_attribution_service import attach_utm_to_inquiry
            attach_utm_to_inquiry(
                self.db,
                row,
                landing_path=landing_path,
                utm={
                    k: v
                    for k, v in {
                        "utm_source": utm_source,
                        "utm_medium": utm_medium,
                        "utm_campaign": utm_campaign,
                        "utm_content": utm_content,
                    }.items()
                    if v
                },
                publish_task_id=publish_task_id,
                session_id=session_id,
                tenant_id=tid,
            )
            med = score_inquiry_meddpicc(row)
            if "meddpicc_json" in cols:
                import json
                row.meddpicc_json = json.dumps(med.get("meddpicc") or {}, ensure_ascii=False)
            self.db.commit()
            self.db.refresh(row)
        except Exception:
            pass
        # 批次 B 首调用方：询盘落地即投影至 GoodJob customer_pool（master=uj）。
        self._push_goodjob_pool_projection(row)
        return self._enrich_public_lead_row(row)
