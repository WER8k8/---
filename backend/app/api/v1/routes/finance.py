# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""财务中台 MVP — 营收/成本流水"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.commission_settlement import AgentCommissionSettlement
from app.models.finance_ledger import (
    ENTRY_TYPE_COST,
    ENTRY_TYPE_REVENUE,
    FinanceLedgerEntry,
    normalize_entry_type,
)
from app.models.user import User
from app.services.finance_service import FinanceService

from app.services.commission_rule_service import CommissionRuleService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/finance", tags=["财务中台"])


class LedgerCreate(BaseModel):
    entry_type: str = Field(..., pattern="^(revenue|cost)$")
    category: str
    amount_cents: int = Field(..., gt=0)
    tenant_id: Optional[str] = None
    reference_id: Optional[str] = None
    note: Optional[str] = None


def _admin_only(user: User):
    """
    处理 _admin_only 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可访问财务中台")
    return None


@router.get("/commission-rules")
def list_commission_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """多级分润规则表（超管可读；代理可读用于展示结算说明）。"""
    if current_user.role not in (
        "admin",
        "super_admin",
        "tenant_admin",
        "agent",
        "l2",
        "l3",
    ):
        return error_response(403, "权限不足")
    return success_response(data=CommissionRuleService(db).list_rules())


class CommissionRuleUpdate(BaseModel):
    rate_bp: Optional[int] = Field(None, ge=0, le=10000)
    label: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


@router.put("/commission-rules/{rule_id}")
def update_commission_rule(
    rule_id: str,
    body: CommissionRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新多级分润规则（仅超管）。"""
    if err := _admin_only(current_user):
        return err
    svc = CommissionRuleService(db)
    try:
        row = svc.update_rule(
            rule_id,
            rate_bp=body.rate_bp,
            label=body.label,
            is_active=body.is_active,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="分润规则已更新")


@router.get("/expiring-tenants")
def finance_expiring_tenants(
    within_days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """即将到期租户（续费提醒用）。"""
    if err := _admin_only(current_user):
        return err
    from app.services.tenant_lifecycle_service import TenantLifecycleService
    return success_response(data=TenantLifecycleService(db).preview_expiring(within_days=within_days))


@router.get("/ledger")
def list_ledger(
    entry_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_ledger）：处理相关业务逻辑并返回结果。

    :param entry_type: 入参 (Optional[str])。
    :param from_date: 入参 (Optional[str])。
    :param to_date: 入参 (Optional[str])。
    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _admin_only(current_user):
        return err
    q = db.query(FinanceLedgerEntry)
    if entry_type:
        canonical = normalize_entry_type(entry_type)
        allowed = ENTRY_TYPE_REVENUE if canonical == "revenue" else ENTRY_TYPE_COST
        q = q.filter(FinanceLedgerEntry.entry_type.in_(allowed))
    if from_date:
        q = q.filter(FinanceLedgerEntry.recorded_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(FinanceLedgerEntry.recorded_at <= datetime.fromisoformat(to_date))
    total = q.count()
    items = (
        q.order_by(FinanceLedgerEntry.recorded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [
                {
                    "id": i.id,
                    "entry_type": i.entry_type,
                    "category": i.category,
                    "amount_cents": i.amount_cents,
                    "tenant_id": i.tenant_id,
                    "reference_id": i.reference_id,
                    "note": i.note,
                    "recorded_at": i.recorded_at.isoformat() if i.recorded_at else None,
                }
                for i in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/ledger")
def create_ledger_entry(
    req: LedgerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_ledger_entry）：处理相关业务逻辑并返回结果。

    :param req: 入参 (LedgerCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _admin_only(current_user):
        return err
    row = FinanceLedgerEntry(**req.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data={"id": row.id}, message="已记账")


@router.get("/summary")
def finance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 finance_summary 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _admin_only(current_user):
        return err
    svc = FinanceService(db)
    summary = svc.profit_summary()
    summary["top_tenants_by_revenue"] = svc.revenue_by_tenant(limit=10)
    return success_response(data=summary)


class FinanceImportValidateBody(BaseModel):
    csv_text: str = Field(..., min_length=10)


@router.post("/import/validate")
def validate_finance_import(
    body: FinanceImportValidateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """财务对账 CSV 导入预检（不写库）。"""
    if err := _admin_only(current_user):
        return err
    report = FinanceService(db).validate_import_csv(body.csv_text)
    return success_response(data=report)


class FinanceImportCommitBody(BaseModel):
    csv_text: str = Field(..., min_length=10)
    dry_run: bool = False


@router.post("/import/commit")
def commit_finance_import(
    body: FinanceImportCommitBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """财务对账 CSV 写入台账（七步财务闭环；reference_id 幂等）。"""
    if err := _admin_only(current_user):
        return err
    report = FinanceService(db).commit_import_csv(body.csv_text, dry_run=body.dry_run)
    return success_response(data=report)


@router.get("/reconciliation-template.csv")
def download_reconciliation_template(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对账导入模板（可用 Excel 打开编辑）。"""
    if err := _admin_only(current_user):
        return err
    csv_text = FinanceService(db).reconciliation_template_csv()
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="finance_reconciliation_template.csv"',
        },
    )


@router.get("/export.csv")
def export_finance_csv(
    request: Request,
    entry_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """财务台账 CSV 导出（超管）。"""
    from app.core.data_export_guard import assert_export_allowed
    if err := _admin_only(current_user):
        return err
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="finance_ledger_csv",
        scope="platform",
    )
    csv_text = FinanceService(db).export_ledger_csv(entry_type=entry_type)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="finance_ledger.csv"'},
    )


@router.get("/cost-by-category")
def cost_by_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """成本按类目汇总（D-05）"""
    if err := _admin_only(current_user):
        return err
    rows = (
        db.query(
            FinanceLedgerEntry.category,
            func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0),
        )
        .filter(FinanceLedgerEntry.entry_type.in_(ENTRY_TYPE_COST))
        .group_by(FinanceLedgerEntry.category)
        .all()
    )
    return success_response(
        data={
            "categories": [
                {"category": cat or "uncategorized", "amount_cents": int(amt or 0)}
                for cat, amt in rows
            ],
            "total_cost_cents": sum(int(amt or 0) for _, amt in rows),
        }
    )


@router.get("/commissions")
def list_commissions(
    period: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """代理分润结算单列表（D-06）"""
    agent_roles = frozenset({"agent", "l2", "l3"})
    if current_user.role not in ("admin", "super_admin", "tenant_admin", *agent_roles):
        return error_response(403, "权限不足")
    q = db.query(AgentCommissionSettlement)
    if current_user.role in agent_roles:
        from app.services.agent_portal_service import AgentPortalService
        node_id = AgentPortalService(db).resolve_node_id(current_user)
        q = q.filter(AgentCommissionSettlement.agent_node_id == node_id)
    if period:
        q = q.filter(AgentCommissionSettlement.period == period)
    if status:
        q = q.filter(AgentCommissionSettlement.status == status)
    total = q.count()
    items = (
        q.order_by(AgentCommissionSettlement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    settled = (
        db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
        .filter(AgentCommissionSettlement.status == "settled")
        .scalar()
    )
    pending = (
        db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
        .filter(AgentCommissionSettlement.status == "pending")
        .scalar()
    )
    rejected = (
        db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
        .filter(AgentCommissionSettlement.status == "rejected")
        .scalar()
    )
    return success_response(
        data={
            "items": [
                {
                    "id": i.id,
                    "agent_node_id": i.agent_node_id,
                    "period": i.period,
                    "revenue_cents": i.revenue_cents,
                    "commission_cents": i.commission_cents,
                    "commission_rate_bp": i.commission_rate_bp,
                    "status": i.status,
                    "note": i.note,
                    "reject_reason": getattr(i, "reject_reason", None),
                    "settled_at": i.settled_at.isoformat() if i.settled_at else None,
                }
                for i in items
            ],
            "total": total,
            "stats": {
                "settled_cents": int(settled or 0),
                "pending_cents": int(pending or 0),
                "rejected_cents": int(rejected or 0),
                "total_cents": int(settled or 0) + int(pending or 0),
            },
        }
    )


class CommissionCreate(BaseModel):
    agent_node_id: str
    period: str
    revenue_cents: int = Field(..., gt=0)
    commission_rate_bp: int = Field(3000, ge=0, le=10000)


class CommissionRejectBody(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class CommissionCancelBody(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class CommissionUpdate(BaseModel):
    revenue_cents: Optional[int] = Field(None, gt=0)
    commission_rate_bp: Optional[int] = Field(None, ge=0, le=10000)
    commission_cents: Optional[int] = Field(None, ge=0)
    note: Optional[str] = Field(None, max_length=500)


# 有向迁移：from → 允许的 to（禁止 frozenset 无序边表）
COMMISSION_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"settled", "rejected", "cancelled"}),
    "settled": frozenset({"cancelled"}),
    "rejected": frozenset(),
    "cancelled": frozenset(),
}


def _commission_can_transition(from_status: str, to_status: str) -> bool:
    return to_status in COMMISSION_TRANSITIONS.get(from_status, frozenset())


def _commission_row_to_dict(row: AgentCommissionSettlement) -> dict:
    return {
        "id": row.id,
        "agent_node_id": row.agent_node_id,
        "period": row.period,
        "revenue_cents": row.revenue_cents,
        "commission_cents": row.commission_cents,
        "commission_rate_bp": row.commission_rate_bp,
        "status": row.status,
        "note": row.note,
        "reject_reason": row.reject_reason,
        "settled_at": row.settled_at.isoformat() if row.settled_at else None,
        "allowed_next": sorted(COMMISSION_TRANSITIONS.get(row.status or "", frozenset())),
    }


@router.post("/commissions")
def create_commission(
    req: CommissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_commission）：处理相关业务逻辑并返回结果。

    :param req: 入参 (CommissionCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _admin_only(current_user):
        return err
    commission_cents = req.revenue_cents * req.commission_rate_bp // 10000
    row = AgentCommissionSettlement(
        agent_node_id=req.agent_node_id,
        period=req.period,
        revenue_cents=req.revenue_cents,
        commission_cents=commission_cents,
        commission_rate_bp=req.commission_rate_bp,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data={"id": row.id}, message="结算单已创建")


@router.put("/commissions/{settlement_id}")
def update_commission(
    settlement_id: str,
    body: CommissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """佣金单修正（仅 pending 可改；已结算/驳回/取消不可改）。"""
    if err := _admin_only(current_user):
        return err
    row = db.query(AgentCommissionSettlement).filter_by(id=settlement_id).first()
    if not row:
        return error_response(404, "结算单不存在")
    if row.status != "pending":
        return error_response(400, f"当前状态 {row.status} 不可修正，仅待结算可改")
    if body.revenue_cents is not None:
        row.revenue_cents = body.revenue_cents
    if body.commission_rate_bp is not None:
        row.commission_rate_bp = body.commission_rate_bp
    if body.commission_cents is not None:
        row.commission_cents = body.commission_cents
    elif body.revenue_cents is not None or body.commission_rate_bp is not None:
        row.commission_cents = int(row.revenue_cents or 0) * int(row.commission_rate_bp or 0) // 10000
    if body.note is not None:
        row.note = body.note.strip()[:500]
    db.commit()
    db.refresh(row)
    return success_response(data=_commission_row_to_dict(row), message="结算单已修正")


@router.delete("/commissions/{settlement_id}")
def delete_commission(
    settlement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除佣金单（仅 pending 可删；已结算须走 cancel 留痕）。"""
    if err := _admin_only(current_user):
        return err
    row = db.query(AgentCommissionSettlement).filter_by(id=settlement_id).first()
    if not row:
        return error_response(404, "结算单不存在")
    if row.status != "pending":
        return error_response(400, f"当前状态 {row.status} 不可删除，仅待结算可删")
    db.delete(row)
    db.commit()
    return success_response(message="结算单已删除")


@router.post("/commissions/{settlement_id}/settle")
def settle_commission(
    settlement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 settle_commission 相关业务逻辑。

    :param settlement_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _admin_only(current_user):
        return err
    row = db.query(AgentCommissionSettlement).filter_by(id=settlement_id).first()
    if not row:
        return error_response(404, "结算单不存在")
    if not _commission_can_transition(row.status or "", "settled"):
        return error_response(400, f"当前状态 {row.status} 不可结算")
    row.status = "settled"
    row.settled_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(data=_commission_row_to_dict(row), message="已标记为已结算")


@router.post("/commissions/{settlement_id}/reject")
def reject_commission(
    settlement_id: str,
    body: CommissionRejectBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """佣金单驳回（带原因；pending → rejected）。"""
    if err := _admin_only(current_user):
        return err
    row = db.query(AgentCommissionSettlement).filter_by(id=settlement_id).first()
    if not row:
        return error_response(404, "结算单不存在")
    if not _commission_can_transition(row.status or "", "rejected"):
        return error_response(400, f"当前状态 {row.status} 不可驳回")
    row.status = "rejected"
    row.reject_reason = body.reason.strip()[:500]
    db.commit()
    db.refresh(row)
    return success_response(data=_commission_row_to_dict(row), message="结算单已驳回")


@router.post("/commissions/{settlement_id}/cancel")
def cancel_commission(
    settlement_id: str,
    body: CommissionCancelBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """佣金单取消（pending|settled → cancelled，带原因留痕）。"""
    if err := _admin_only(current_user):
        return err
    row = db.query(AgentCommissionSettlement).filter_by(id=settlement_id).first()
    if not row:
        return error_response(404, "结算单不存在")
    if not _commission_can_transition(row.status or "", "cancelled"):
        return error_response(400, f"当前状态 {row.status} 不可取消")
    # 取消已结算单：保留 settled_at 作审计痕迹，不抹除
    row.status = "cancelled"
    row.note = (body.reason.strip()[:500])
    db.commit()
    db.refresh(row)
    return success_response(data=_commission_row_to_dict(row), message="结算单已取消")


# ---------------------------------------------------------------------------
# P1-07: 利润与分层看板
# ---------------------------------------------------------------------------

@router.get("/profit-dashboard")
def profit_dashboard(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管/省代/租户三层利润看板。
    
    - 超管：全局汇总 + 按租户分组
    - 省代(agent)：仅展示自己代理下的租户贡献及分润
    - 租户管理员：仅展示本租户数据
    """
    from sqlalchemy import and_
    svc = FinanceService(db)
    if current_user.role in ("admin", "super_admin"):
        # 全局看板
        summary = svc.profit_summary()
        top_tenants = svc.revenue_by_tenant(limit=20)
        commissions_pending = (
            db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
            .filter(AgentCommissionSettlement.status == "pending")
            .scalar()
        )
        commissions_settled = (
            db.query(func.coalesce(func.sum(AgentCommissionSettlement.commission_cents), 0))
            .filter(AgentCommissionSettlement.status == "settled")
            .scalar()
        )
        return success_response(
            data={
                "role": "super_admin",
                "profit_summary": summary,
                "top_tenants_by_revenue": top_tenants,
                "commission_stats": {
                    "pending_cents": int(commissions_pending or 0),
                    "settled_cents": int(commissions_settled or 0),
                },
            }
        )

    elif current_user.role in ("agent", "l2", "l3"):
        from app.services.agent_portal_service import AgentPortalService
        node_id = AgentPortalService(db).resolve_node_id(current_user)
        q = db.query(AgentCommissionSettlement).filter(
            AgentCommissionSettlement.agent_node_id == node_id
        )
        if period:
            q = q.filter(AgentCommissionSettlement.period == period)
        settlements = q.order_by(AgentCommissionSettlement.created_at.desc()).limit(12).all()
        total_commission = sum(s.commission_cents for s in settlements)
        pending_commission = sum(
            s.commission_cents for s in settlements if s.status == "pending"
        )
        return success_response(
            data={
                "role": current_user.role,
                "agent_node_id": node_id,
                "settlements": [
                    {
                        "period": s.period,
                        "revenue_cents": s.revenue_cents,
                        "commission_cents": s.commission_cents,
                        "status": s.status,
                    }
                    for s in settlements
                ],
                "total_commission_cents": total_commission,
                "pending_commission_cents": pending_commission,
            }
        )

    else:
        # 租户管理员：展示本租户财务数据
        from app.models.finance_ledger import FinanceLedgerEntry
        from app.models.tenant import UserTenant
        tenant_ids = [
            ut.tenant_id
            for ut in db.query(UserTenant)
            .filter(UserTenant.user_id == current_user.id, UserTenant.is_active)
            .all()
        ]
        if not tenant_ids:
            return success_response(data={"role": "tenant", "revenue_cents": 0, "entries": []})
        q = db.query(
            func.coalesce(func.sum(FinanceLedgerEntry.amount_cents), 0)
        ).filter(
            FinanceLedgerEntry.tenant_id.in_(tenant_ids),
            FinanceLedgerEntry.entry_type.in_(ENTRY_TYPE_REVENUE),
        )
        revenue = int(q.scalar() or 0)
        return success_response(
            data={
                "role": "tenant",
                "tenant_ids": tenant_ids,
                "revenue_cents": revenue,
            }
        )


# ---------------------------------------------------------------------------
# P1-08: Excel对账导出（增强版）
# ---------------------------------------------------------------------------

@router.get("/export/excel-report")
def export_excel_report(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出财务对账报表（CSV格式，兼容Excel导入）。
    
    提供营收+成本+分润的完整对账单，
    适合月末财务核查。
    """
    if err := _admin_only(current_user):
        return err
    from app.core.data_export_guard import assert_export_allowed
    assert_export_allowed(
        db,
        current_user,
        request,
        export_kind="finance_excel_report",
        scope="tenant" if tenant_id else "platform",
    )
    svc = FinanceService(db)
    csv_content = svc.export_ledger_csv(
        from_date=from_date,
        to_date=to_date,
        tenant_id=tenant_id,
    )
    filename = f"finance_report_{from_date or 'all'}_{to_date or 'all'}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
