"""增值税发票开票申请（合规：申请≠已开票，须财务审核及税控开具）。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base

# pending_review → approved → issuing → issued | rejected | cancelled
INVOICE_APP_STATUSES = frozenset(
    {
        "pending_review",
        "approved",
        "rejected",
        "issuing",
        "issued",
        "cancelled",
    }
)


class PlatformInvoiceConfig(Base):
    """平台方（销售方）开票主体信息 — 公司注册完成后由超管配置。"""
    __tablename__ = "platform_invoice_configs"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_name = Column(String(200), nullable=False)
    seller_tax_id = Column(String(20), nullable=False)
    seller_address = Column(String(300))
    seller_phone = Column(String(50))
    seller_bank_name = Column(String(200))
    seller_bank_account = Column(String(64))
    service_category = Column(String(100), default="信息技术服务*软件服务费")
    disclaimer = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class TenantInvoiceProfile(Base):
    """租户常用开票抬头（购方）。"""
    __tablename__ = "tenant_invoice_profiles"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    buyer_type = Column(String(20), default="enterprise")  # enterprise | individual
    invoice_type = Column(String(20), default="vat_general")  # vat_general | vat_special
    title = Column(String(200), nullable=False)
    tax_id = Column(String(20))
    company_address = Column(String(300))
    company_phone = Column(String(50))
    bank_name = Column(String(200))
    bank_account = Column(String(64))
    recipient_email = Column(String(200), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class InvoiceApplication(Base):
    """开票申请单 — 关联已支付订单，财务审核后线下/税控 API 开具。"""
    __tablename__ = "invoice_applications"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=False, index=True)
    payment_order_id = Column(UUID_TYPE, ForeignKey("payment_orders.id"), nullable=False, index=True)
    applicant_user_id = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    buyer_type = Column(String(20), nullable=False, default="enterprise")
    invoice_type = Column(String(20), nullable=False, default="vat_general")
    title = Column(String(200), nullable=False)
    tax_id = Column(String(20))
    company_address = Column(String(300))
    company_phone = Column(String(50))
    bank_name = Column(String(200))
    bank_account = Column(String(64))
    recipient_email = Column(String(200), nullable=False)
    amount_cents = Column(Integer, nullable=False, default=0)
    order_no = Column(String(100))
    status = Column(String(30), default="pending_review", nullable=False, index=True)
    disclaimer_ack = Column(Boolean, default=False, nullable=False)
    reject_reason = Column(Text)
    admin_note = Column(Text)
    customer_note = Column(Text)
    reviewed_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    issued_at = Column(DateTime(timezone=True))
    invoice_code = Column(String(32))
    invoice_number = Column(String(32))
    invoice_file_note = Column(String(500))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
