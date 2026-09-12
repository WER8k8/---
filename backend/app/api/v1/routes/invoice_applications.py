"""开票申请 API — 租户提交 + 财务审核。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.routes.client import _resolve_tenant
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.invoice_application_service import (
    INVOICE_LEGAL_DISCLAIMER,
    InvoiceApplicationError,
    InvoiceApplicationService,
)
from app.services.invoice_pdf_service import build_invoice_application_pdf_bytes

router = APIRouter(tags=["开票申请"])


class InvoiceApplicationCreate(BaseModel):
    payment_order_id: str
    buyer_type: str = Field("enterprise", pattern="^(enterprise|individual)$")
    invoice_type: str = Field("vat_general", pattern="^(vat_general|vat_special)$")
    title: str = Field(..., min_length=2, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=20)
    company_address: Optional[str] = Field(None, max_length=300)
    company_phone: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_account: Optional[str] = Field(None, max_length=64)
    recipient_email: str = Field(..., max_length=200)
    customer_note: Optional[str] = Field(None, max_length=500)
    disclaimer_ack: bool = False
    save_profile: bool = False


class PlatformConfigUpdate(BaseModel):
    seller_name: str = Field(..., min_length=2, max_length=200)
    seller_tax_id: str = Field(..., min_length=15, max_length=20)
    seller_address: Optional[str] = Field(None, max_length=300)
    seller_phone: Optional[str] = Field(None, max_length=50)
    seller_bank_name: Optional[str] = Field(None, max_length=200)
    seller_bank_account: Optional[str] = Field(None, max_length=64)
    service_category: Optional[str] = Field(None, max_length=100)
    disclaimer: Optional[str] = None


class ReviewBody(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reject_reason: Optional[str] = Field(None, max_length=500)
    admin_note: Optional[str] = Field(None, max_length=500)


class MarkIssuedBody(BaseModel):
    invoice_code: str = Field(..., min_length=4, max_length=32)
    invoice_number: str = Field(..., min_length=4, max_length=32)
    invoice_file_note: Optional[str] = Field(None, max_length=500)


def _finance_only(user: User):
    """
    处理 _finance_only 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if user.role not in ("admin", "super_admin"):
        return error_response(403, "仅财务/超管可操作")
    return None


# ---------------------------------------------------------------------------
# 租户端 /client
# ---------------------------------------------------------------------------

client_router = APIRouter(prefix="/client/invoice-applications", tags=["租户开票申请"])


@client_router.get("/meta")
def client_invoice_meta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """免责声明与平台开票能力说明。"""
    svc = InvoiceApplicationService(db)
    platform = svc.get_platform_config()
    return success_response(
        data={
            "disclaimer": INVOICE_LEGAL_DISCLAIMER,
            "platform_ready": platform is not None,
            "seller_name": platform.seller_name if platform else None,
            "invoice_types": [
                {"code": "vat_general", "label": "增值税普通发票"},
                {"code": "vat_special", "label": "增值税专用发票（一般纳税人）"},
            ],
        }
    )


@client_router.get("/eligible-orders")
def client_eligible_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 client_eligible_orders 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    svc = InvoiceApplicationService(db)
    return success_response(data=svc.list_eligible_orders(str(tenant.id)))


@client_router.get("")
def client_list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 client_list_applications 相关业务逻辑。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    svc = InvoiceApplicationService(db)
    items, total = svc.list_applications(tenant_id=str(tenant.id), page=page, page_size=page_size)
    return success_response(
        data={
            "items": [svc.to_dict(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@client_router.post("")
def client_create_application(
    body: InvoiceApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 client_create_application 相关业务逻辑。

    :param body: 入参 (InvoiceApplicationCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    svc = InvoiceApplicationService(db)
    try:
        row = svc.create_application(
            current_user,
            str(tenant.id),
            body.model_dump(),
        )
    except InvoiceApplicationError as exc:
        return error_response(400, str(exc))
    return success_response(data=svc.to_dict(row), message="开票申请已提交，请等待财务审核")


@client_router.get("/{application_id}/receipt.pdf")
def client_download_receipt(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载申请回执 PDF（非税票）。"""
    tenant, _, err = _resolve_tenant(db, current_user)
    if err:
        return err
    svc = InvoiceApplicationService(db)
    from app.models.invoice_application import InvoiceApplication
    row = (
        db.query(InvoiceApplication)
        .filter(
            InvoiceApplication.id == application_id,
            InvoiceApplication.tenant_id == str(tenant.id),
        )
        .first()
    )
    if not row:
        return error_response(404, "申请不存在")
    platform = svc.get_platform_config()
    pdf = build_invoice_application_pdf_bytes(
        svc.to_dict(row),
        seller=platform,
        disclaimer=INVOICE_LEGAL_DISCLAIMER,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="invoice-application-{application_id[:8]}.pdf"'
        },
    )


# ---------------------------------------------------------------------------
# 财务端 /finance
# ---------------------------------------------------------------------------

finance_router = APIRouter(prefix="/finance/invoice-applications", tags=["财务开票审核"])


@finance_router.get("/platform-config")
def get_platform_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_platform_config）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    row = svc.get_platform_config()
    if not row:
        return success_response(
            data={"configured": False, "disclaimer": INVOICE_LEGAL_DISCLAIMER}
        )
    return success_response(
        data={
            "configured": True,
            "seller_name": row.seller_name,
            "seller_tax_id": row.seller_tax_id,
            "seller_address": row.seller_address,
            "seller_phone": row.seller_phone,
            "seller_bank_name": row.seller_bank_name,
            "seller_bank_account": row.seller_bank_account,
            "service_category": row.service_category,
            "disclaimer": row.disclaimer or INVOICE_LEGAL_DISCLAIMER,
        }
    )


@finance_router.put("/platform-config")
def update_platform_config(
    body: PlatformConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新（update_platform_config）：处理相关业务逻辑并返回结果。

    :param body: 入参 (PlatformConfigUpdate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    try:
        row = svc.upsert_platform_config(body.model_dump())
    except InvoiceApplicationError as exc:
        return error_response(400, str(exc))
    return success_response(
        data={"id": str(row.id), "seller_name": row.seller_name},
        message="平台开票主体已更新",
    )


@finance_router.get("")
def finance_list_applications(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 finance_list_applications 相关业务逻辑。

    :param status: 入参 (Optional[str])。
    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    items, total = svc.list_applications(status=status, page=page, page_size=page_size)
    return success_response(
        data={
            "items": [svc.to_dict(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@finance_router.post("/{application_id}/review")
def finance_review_application(
    application_id: str,
    body: ReviewBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 finance_review_application 相关业务逻辑。

    :param application_id: 入参 (str)。
    :param body: 入参 (ReviewBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    try:
        row = svc.review(
            application_id,
            current_user,
            action=body.action,
            reject_reason=body.reject_reason,
            admin_note=body.admin_note,
        )
    except InvoiceApplicationError as exc:
        return error_response(400, str(exc))
    return success_response(data=svc.to_dict(row), message="审核完成")


@finance_router.post("/{application_id}/mark-issued")
def finance_mark_issued(
    application_id: str,
    body: MarkIssuedBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 finance_mark_issued 相关业务逻辑。

    :param application_id: 入参 (str)。
    :param body: 入参 (MarkIssuedBody)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    try:
        row = svc.mark_issued(
            application_id,
            current_user,
            invoice_code=body.invoice_code,
            invoice_number=body.invoice_number,
            invoice_file_note=body.invoice_file_note,
        )
    except InvoiceApplicationError as exc:
        return error_response(400, str(exc))
    return success_response(data=svc.to_dict(row), message="已标记为已开票")


@finance_router.post("/{application_id}/issue-via-provider")
def finance_issue_via_provider(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """通过全电票 Provider（诺诺等）开具；未配置时返回明确提示。"""
    if err := _finance_only(current_user):
        return err
    svc = InvoiceApplicationService(db)
    try:
        row, meta = svc.issue_via_provider(application_id, current_user)
    except InvoiceApplicationError as exc:
        return error_response(400, str(exc))
    return success_response(
        data={"application": svc.to_dict(row), "provider_result": meta},
        message=meta.get("message") or "电子开票已提交",
    )


@finance_router.get("/provider-status")
def finance_einvoice_provider_status(
    current_user: User = Depends(get_current_user),
):
    """
    处理 finance_einvoice_provider_status 相关业务逻辑。

    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _finance_only(current_user):
        return err
    from app.services.einvoice_provider import get_einvoice_provider
    p = get_einvoice_provider()
    return success_response(
        data={
            "provider": p.name,
            "configured": p.is_configured(),
        }
    )
