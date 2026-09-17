# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开票申请合规校验与业务逻辑。"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.invoice_application import (
    INVOICE_APP_STATUSES,
    InvoiceApplication,
    PlatformInvoiceConfig,
    TenantInvoiceProfile,
)
from app.models.payment import PaymentOrder
from app.models.tenant import Tenant, UserTenant
from app.models.user import User

# 对外统一免责声明（界面与 PDF 须展示）
INVOICE_LEGAL_DISCLAIMER = (
    "【重要说明】本页面提交的是「开票申请」，不构成已开具的增值税发票。"
    "正式发票由平台财务审核后，通过税控/全电发票系统开具。"
    "票面销售方为平台运营主体，与代理分润无关。"
    "申请信息与已支付订单金额须一致，虚假申请将被驳回并可能影响服务。"
)

# 统一社会信用代码 / 纳税人识别号（18 位，国标简化校验）
_USCC_PATTERN = re.compile(
    r"^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_ACTIVE_BLOCKING_STATUSES = frozenset(
    {"pending_review", "approved", "issuing", "issued"}
)


class InvoiceApplicationError(ValueError):
    pass


def normalize_tax_id(raw: str | None) -> str:
    """normalize_tax_id。

    参数说明：
    :param raw: 参数 raw
    :return: 返回处理结果。
    """
    return (raw or "").strip().upper().replace(" ", "")


def validate_uscc(tax_id: str) -> bool:
    """validate_uscc。

    参数说明：
    :param tax_id: 参数 tax_id
    :return: 返回处理结果。
    """
    tid = normalize_tax_id(tax_id)
    if not tid:
        return False
    if len(tid) == 15 and tid.isdigit():
        return True
    if len(tid) == 18:
        return bool(_USCC_PATTERN.match(tid))
    if len(tid) == 20 and tid[:18].isalnum():
        return bool(_USCC_PATTERN.match(tid[:18]))
    return False


def validate_application_payload(data: dict[str, Any]) -> None:
    """validate_application_payload。

    参数说明：
    :param data: 参数 data
    :return: 返回处理结果。
    """
    buyer_type = data.get("buyer_type") or "enterprise"
    invoice_type = data.get("invoice_type") or "vat_general"
    title = (data.get("title") or "").strip()
    email = (data.get("recipient_email") or "").strip()
    if not title or len(title) < 2:
        raise InvoiceApplicationError("发票抬头至少 2 个字符")
    if len(title) > 200:
        raise InvoiceApplicationError("发票抬头过长")
    if not email or not _EMAIL_PATTERN.match(email):
        raise InvoiceApplicationError("请填写有效的收票邮箱")

    if buyer_type not in ("enterprise", "individual"):
        raise InvoiceApplicationError("购方类型无效")
    if invoice_type not in ("vat_general", "vat_special"):
        raise InvoiceApplicationError("发票类型无效")

    tax_id = normalize_tax_id(data.get("tax_id"))
    if invoice_type == "vat_special":
        if buyer_type != "enterprise":
            raise InvoiceApplicationError("增值税专用发票仅限企业一般纳税人")
        if not validate_uscc(tax_id):
            raise InvoiceApplicationError("专票须填写有效的18位统一社会信用代码/税号")
        for field, label in (
            ("company_address", "注册地址"),
            ("company_phone", "注册电话"),
            ("bank_name", "开户银行"),
            ("bank_account", "银行账号"),
        ):
            if not (data.get(field) or "").strip():
                raise InvoiceApplicationError(f"专票须填写{label}")

    if buyer_type == "enterprise" and invoice_type == "vat_general":
        if tax_id and not validate_uscc(tax_id):
            raise InvoiceApplicationError("企业普票税号格式不正确")

    if not data.get("disclaimer_ack"):
        raise InvoiceApplicationError("请阅读并确认开票免责声明")


class InvoiceApplicationService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def get_platform_config(self) -> Optional[PlatformInvoiceConfig]:
        """get_platform_config。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return (
            self.db.query(PlatformInvoiceConfig)
            .filter(PlatformInvoiceConfig.is_active.is_(True))
            .order_by(PlatformInvoiceConfig.updated_at.desc())
            .first()
        )

    def upsert_platform_config(self, data: dict[str, Any]) -> PlatformInvoiceConfig:
        """upsert_platform_config。

        参数说明：
        :param self: 参数 self
        :param data: 参数 data
        :return: 返回处理结果。
        """
        seller_tax_id = normalize_tax_id(data.get("seller_tax_id"))
        if not validate_uscc(seller_tax_id):
            raise InvoiceApplicationError("销售方税号格式无效")
        if not (data.get("seller_name") or "").strip():
            raise InvoiceApplicationError("销售方名称为必填")

        row = self.get_platform_config()
        if not row:
            row = PlatformInvoiceConfig(id=str(uuid.uuid4()))
            self.db.add(row)
        row.seller_name = data["seller_name"].strip()
        row.seller_tax_id = seller_tax_id
        row.seller_address = (data.get("seller_address") or "")[:300] or None
        row.seller_phone = (data.get("seller_phone") or "")[:50] or None
        row.seller_bank_name = (data.get("seller_bank_name") or "")[:200] or None
        row.seller_bank_account = (data.get("seller_bank_account") or "")[:64] or None
        row.service_category = (data.get("service_category") or row.service_category or "")[:100]
        row.disclaimer = data.get("disclaimer") or INVOICE_LEGAL_DISCLAIMER
        row.is_active = True
        self.db.commit()
        self.db.refresh(row)
        return row

    def assert_tenant_access(self, user: User, tenant_id: str) -> Tenant:
        """assert_tenant_access。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        if user.role in ("admin", "super_admin"):
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise InvoiceApplicationError("租户不存在")
            return tenant
        link = (
            self.db.query(UserTenant)
            .filter(
                UserTenant.user_id == user.id,
                UserTenant.tenant_id == tenant_id,
                UserTenant.is_active,
            )
            .first()
        )
        if not link:
            raise InvoiceApplicationError("无权访问该租户")
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise InvoiceApplicationError("租户不存在")
        return tenant

    def list_eligible_orders(self, tenant_id: str) -> list[dict[str, Any]]:
        """list_eligible_orders。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        orders = (
            self.db.query(PaymentOrder)
            .filter(PaymentOrder.tenant_id == tenant_id, PaymentOrder.status == "paid")
            .order_by(PaymentOrder.paid_at.desc())
            .all()
        )
        blocked = {
            str(r.payment_order_id)
            for r in self.db.query(InvoiceApplication.payment_order_id)
            .filter(
                InvoiceApplication.tenant_id == tenant_id,
                InvoiceApplication.status.in_(_ACTIVE_BLOCKING_STATUSES),
            )
            .all()
        }
        result = []
        for o in orders:
            oid = str(o.id)
            result.append(
                {
                    "id": oid,
                    "order_no": o.order_no,
                    "amount_cents": o.amount,
                    "subject": o.subject,
                    "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                    "invoice_applied": oid in blocked,
                }
            )
        return result

    def create_application(
        self,
        user: User,
        tenant_id: str,
        payload: dict[str, Any],
    ) -> InvoiceApplication:
        """create_application。

        参数说明：
        :param self: 参数 self
        :param user: 参数 user
        :param tenant_id: 参数 tenant_id
        :param payload: 参数 payload
        :return: 返回处理结果。
        """
        validate_application_payload(payload)
        self.assert_tenant_access(user, tenant_id)
        order_id = payload.get("payment_order_id")
        order = (
            self.db.query(PaymentOrder)
            .filter(
                PaymentOrder.id == order_id,
                PaymentOrder.tenant_id == tenant_id,
                PaymentOrder.status == "paid",
            )
            .first()
        )
        if not order:
            raise InvoiceApplicationError("仅已支付订单可申请开票")

        exists = (
            self.db.query(InvoiceApplication)
            .filter(
                InvoiceApplication.payment_order_id == order_id,
                InvoiceApplication.status.in_(_ACTIVE_BLOCKING_STATUSES),
            )
            .first()
        )
        if exists:
            raise InvoiceApplicationError("该订单已有进行中的开票申请")

        platform = self.get_platform_config()
        if not platform:
            raise InvoiceApplicationError(
                "平台开票主体尚未配置，暂无法受理申请，请联系客服"
            )

        row = InvoiceApplication(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            payment_order_id=str(order.id),
            applicant_user_id=str(user.id),
            buyer_type=payload.get("buyer_type") or "enterprise",
            invoice_type=payload.get("invoice_type") or "vat_general",
            title=payload["title"].strip(),
            tax_id=normalize_tax_id(payload.get("tax_id")) or None,
            company_address=(payload.get("company_address") or "").strip() or None,
            company_phone=(payload.get("company_phone") or "").strip() or None,
            bank_name=(payload.get("bank_name") or "").strip() or None,
            bank_account=(payload.get("bank_account") or "").strip() or None,
            recipient_email=payload["recipient_email"].strip(),
            amount_cents=int(order.amount),
            order_no=order.order_no,
            status="pending_review",
            disclaimer_ack=True,
            customer_note=(payload.get("customer_note") or "")[:500] or None,
        )
        self.db.add(row)
        if payload.get("save_profile"):
            self._save_profile(tenant_id, payload)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _save_profile(self, tenant_id: str, payload: dict[str, Any]) -> None:
        """_save_profile。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param payload: 参数 payload
        :return: 返回处理结果。
        """
        prof = TenantInvoiceProfile(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            buyer_type=payload.get("buyer_type") or "enterprise",
            invoice_type=payload.get("invoice_type") or "vat_general",
            title=payload["title"].strip(),
            tax_id=normalize_tax_id(payload.get("tax_id")) or None,
            company_address=(payload.get("company_address") or "").strip() or None,
            company_phone=(payload.get("company_phone") or "").strip() or None,
            bank_name=(payload.get("bank_name") or "").strip() or None,
            bank_account=(payload.get("bank_account") or "").strip() or None,
            recipient_email=payload["recipient_email"].strip(),
            is_default=True,
        )
        self.db.query(TenantInvoiceProfile).filter(
            TenantInvoiceProfile.tenant_id == tenant_id
        ).update({"is_default": False})
        self.db.add(prof)

    def list_applications(
        self,
        *,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InvoiceApplication], int]:
        """list_applications。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param status: 参数 status
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        q = self.db.query(InvoiceApplication)
        if tenant_id:
            q = q.filter(InvoiceApplication.tenant_id == tenant_id)
        if status:
            q = q.filter(InvoiceApplication.status == status)
        total = q.count()
        items = (
            q.order_by(InvoiceApplication.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def review(
        self,
        app_id: str,
        reviewer: User,
        *,
        action: str,
        reject_reason: Optional[str] = None,
        admin_note: Optional[str] = None,
    ) -> InvoiceApplication:
        """review。

        参数说明：
        :param self: 参数 self
        :param app_id: 参数 app_id
        :param reviewer: 参数 reviewer
        :param action: 参数 action
        :param reject_reason: 参数 reject_reason
        :param admin_note: 参数 admin_note
        :return: 返回处理结果。
        """
        row = self.db.query(InvoiceApplication).filter(InvoiceApplication.id == app_id).first()
        if not row:
            raise InvoiceApplicationError("申请不存在")
        if row.status != "pending_review":
            raise InvoiceApplicationError("仅待审核申请可操作")

        if action == "approve":
            row.status = "approved"
        elif action == "reject":
            if not (reject_reason or "").strip():
                raise InvoiceApplicationError("驳回须填写原因")
            row.status = "rejected"
            row.reject_reason = reject_reason.strip()[:500]
        else:
            raise InvoiceApplicationError("无效审核动作")

        row.reviewed_by = str(reviewer.id)
        row.reviewed_at = datetime.now(timezone.utc)
        if admin_note:
            row.admin_note = admin_note.strip()[:500]
        self.db.commit()
        self.db.refresh(row)
        return row

    def mark_issued(
        self,
        app_id: str,
        reviewer: User,
        *,
        invoice_code: str,
        invoice_number: str,
        invoice_file_note: Optional[str] = None,
    ) -> InvoiceApplication:
        """mark_issued。

        参数说明：
        :param self: 参数 self
        :param app_id: 参数 app_id
        :param reviewer: 参数 reviewer
        :param invoice_code: 参数 invoice_code
        :param invoice_number: 参数 invoice_number
        :param invoice_file_note: 参数 invoice_file_note
        :return: 返回处理结果。
        """
        row = self.db.query(InvoiceApplication).filter(InvoiceApplication.id == app_id).first()
        if not row:
            raise InvoiceApplicationError("申请不存在")
        if row.status not in ("approved", "issuing"):
            raise InvoiceApplicationError("仅已审核通过的申请可标记为已开票")

        code = (invoice_code or "").strip()
        number = (invoice_number or "").strip()
        if not code or not number:
            raise InvoiceApplicationError("须填写发票代码与发票号码")

        row.status = "issued"
        row.invoice_code = code[:32]
        row.invoice_number = number[:32]
        row.invoice_file_note = (invoice_file_note or "")[:500] or None
        row.issued_at = datetime.now(timezone.utc)
        if not row.reviewed_by:
            row.reviewed_by = str(reviewer.id)
            row.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(row)
        return row

    def issue_via_provider(self, app_id: str, reviewer: User) -> tuple[InvoiceApplication, dict]:
        """调用全电票 Provider 开票；成功则自动 mark-issued。"""
        from app.services.einvoice_provider import build_issue_request, get_einvoice_provider
        row = self.db.query(InvoiceApplication).filter(InvoiceApplication.id == app_id).first()
        if not row:
            raise InvoiceApplicationError("申请不存在")
        if row.status not in ("approved", "issuing"):
            raise InvoiceApplicationError("仅已审核通过的申请可电子开票")

        platform = self.get_platform_config()
        if not platform:
            raise InvoiceApplicationError("平台开票主体未配置")

        provider = get_einvoice_provider()
        if provider.name == "manual" or not provider.is_configured():
            raise InvoiceApplicationError(
                "未配置全电票 Provider（设置 EINVOICE_PROVIDER=nuonuo 及 NUONUO_*），"
                "请先在税控系统手工开票，再使用「标记已开票」"
            )

        req = build_issue_request(self.to_dict(row), platform)
        result = provider.issue(req)
        meta = {
            "provider": result.provider,
            "message": result.message,
            "success": result.success,
        }
        if not result.success:
            raise InvoiceApplicationError(result.message or "电子开票失败")

        if not result.invoice_code or not result.invoice_number:
            row.status = "issuing"
            row.admin_note = (result.message or "Provider 受理中")[:500]
            self.db.commit()
            self.db.refresh(row)
            return row, meta

        issued = self.mark_issued(
            app_id,
            reviewer,
            invoice_code=result.invoice_code,
            invoice_number=result.invoice_number,
            invoice_file_note=result.pdf_url or result.message,
        )
        meta["auto_marked"] = True
        return issued, meta

    def to_dict(self, row: InvoiceApplication) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :param row: 参数 row
        :return: 返回处理结果。
        """
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "payment_order_id": str(row.payment_order_id),
            "order_no": row.order_no,
            "amount_cents": row.amount_cents,
            "buyer_type": row.buyer_type,
            "invoice_type": row.invoice_type,
            "title": row.title,
            "tax_id": row.tax_id,
            "company_address": row.company_address,
            "company_phone": row.company_phone,
            "bank_name": row.bank_name,
            "bank_account": row.bank_account,
            "recipient_email": row.recipient_email,
            "status": row.status,
            "reject_reason": row.reject_reason,
            "customer_note": row.customer_note,
            "invoice_code": row.invoice_code,
            "invoice_number": row.invoice_number,
            "invoice_file_note": row.invoice_file_note,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
            "issued_at": row.issued_at.isoformat() if row.issued_at else None,
        }
