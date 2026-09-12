"""CRM 销售管线路由 — 商机（Opportunity）管理

端点：
- GET    /api/v1/opportunities                       商机列表（分页/筛选/排序）
- POST   /api/v1/opportunities                       创建商机
- GET    /api/v1/opportunities/stages                阶段配置列表
- GET    /api/v1/opportunities/{opportunity_id}      商机详情
- PATCH  /api/v1/opportunities/{opportunity_id}      更新商机（部分字段）
- POST   /api/v1/opportunities/{opportunity_id}/stages  推进阶段
- GET    /api/v1/pipeline/stats                      管线统计

阶段定义：
Lead → Qualified → Contacted → Engaged → RFQ → Quote → Negotiation → Won / Lost

存储说明（BUG-05 修复）：
原 MVP 实现为进程内存 dict（重启清零、多 worker 分裂、无审计）。
现已迁移到 ORM `Opportunity` + `OpportunityStage` 落库，接口契约与原版完全一致。
阶段历史写入 opportunity_stages 表；商机带 tenant_id 租户隔离。
"""
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import APIResponse, error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.opportunity import Opportunity, OpportunityStage
from app.models.user import User

router = APIRouter(tags=["CRM管线"])

# ─────────────────────────────────────────────
# 阶段配置
# ─────────────────────────────────────────────
STAGE_ORDER: list[str] = [
    "Lead", "Qualified", "Contacted", "Engaged",
    "RFQ", "Quote", "Negotiation", "Won", "Lost",
]

STAGE_LABELS: dict[str, str] = {
    "Lead": "线索",
    "Qualified": "已验证",
    "Contacted": "已联系",
    "Engaged": "深度沟通",
    "RFQ": "询价",
    "Quote": "报价",
    "Negotiation": "谈判",
    "Won": "赢单",
    "Lost": "输单",
}

# 各阶段赢单概率（用于加权金额）
STAGE_PROBABILITY: dict[str, float] = {
    "Lead": 0.05,
    "Qualified": 0.10,
    "Contacted": 0.20,
    "Engaged": 0.30,
    "RFQ": 0.45,
    "Quote": 0.60,
    "Negotiation": 0.75,
    "Won": 1.00,
    "Lost": 0.00,
}

TERMINAL_STAGES = frozenset({"Won", "Lost"})

_SORTABLE_FIELDS = {"created_at", "updated_at", "amount", "name", "expected_close_date", "stage"}

_STAGE_INDEX = {s: i for i, s in enumerate(STAGE_ORDER)}


# ─────────────────────────────────────────────
# Pydantic v2 Schemas
# ─────────────────────────────────────────────
class OpportunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="商机名称")
    company_id: Optional[str] = Field(None, description="关联企业（客户）ID")
    contact_id: Optional[str] = Field(None, description="关联联系人 ID")
    amount: float = Field(0.0, ge=0, description="商机金额")
    currency: str = Field("USD", max_length=8, description="币种（ISO 4217）")
    expected_close_date: Optional[date] = Field(None, description="预计成交日期")
    source: Optional[str] = Field(None, max_length=64, description="来源（询盘/展会/官网等）")


class OpportunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=8)
    expected_close_date: Optional[date] = None
    source: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = Field(None, max_length=2000)


class OpportunityResponse(BaseModel):
    id: str
    name: str
    company_id: Optional[str] = None
    contact_id: Optional[str] = None
    amount: float = 0.0
    currency: str = "USD"
    expected_close_date: Optional[str] = None
    source: Optional[str] = None
    stage: str = "Lead"
    notes: Optional[str] = None
    stage_history: list[dict[str, Any]] = []
    created_by: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class StageAdvanceRequest(BaseModel):
    stage: str = Field(..., description="目标阶段（STAGE_ORDER 之一）")
    notes: Optional[str] = Field(None, max_length=2000, description="阶段备注")


class StageStat(BaseModel):
    stage: str
    label: str
    order: int
    probability: float
    count: int = 0
    amount: float = 0.0
    weighted_amount: float = 0.0


class PipelineStats(BaseModel):
    total: int = 0
    open: int = 0
    won: int = 0
    lost: int = 0
    total_amount: float = 0.0
    weighted_amount: float = 0.0
    conversion_rate: float = Field(0.0, description="转化率 = Won / (Won + Lost)，无成交单时为 0")
    win_rate: float = Field(0.0, description="赢单率 = Won / 全部商机")
    stages: list[StageStat] = []


# ─────────────────────────────────────────────
# ORM 辅助
# ─────────────────────────────────────────────
def _serialize(db: Session, o: Opportunity, with_history: bool = False) -> dict[str, Any]:
    """
    处理 _serialize 相关业务逻辑。

    :param db: 入参 (Session)。
    :param o: 入参 (Opportunity)。
    :param with_history: 入参 (bool)。

    :return: 返回 dict[str, Any] 类型的结果。
    """
    data: dict[str, Any] = {
        "id": str(o.id),
        "name": o.name,
        "company_id": str(o.company_id) if o.company_id else None,
        "contact_id": str(o.contact_id) if o.contact_id else None,
        "amount": float(o.value or 0.0),
        "currency": o.currency or "USD",
        "expected_close_date": o.expected_close_date.isoformat() if o.expected_close_date else None,
        "source": o.source,
        "stage": o.stage or "Lead",
        "notes": o.notes,
        "created_by": str(o.created_by) if o.created_by else None,
        "created_at": o.created_at.isoformat() if o.created_at else "",
        "updated_at": o.updated_at.isoformat() if o.updated_at else "",
    }
    if with_history:
        rows = (
            db.query(OpportunityStage)
            .filter(OpportunityStage.opportunity_id == o.id)
            .order_by(OpportunityStage.changed_at.asc())
            .all()
        )
        data["stage_history"] = [
            {
                "stage": r.stage,
                "notes": r.notes,
                "at": r.changed_at.isoformat() if r.changed_at else None,
            }
            for r in rows
        ]
    else:
        data["stage_history"] = []
    return data


def _tenant_filter(query, current_user: User):
    """租户隔离：普通用户只看本租户商机，平台管理员看全部。"""
    role = str(getattr(current_user, "role", "") or "")
    if role in ("admin", "super_admin"):
        return query
    tenant_id = str(getattr(current_user, "tenant_id", "") or "")
    if tenant_id:
        return query.filter(Opportunity.tenant_id == tenant_id)
    return query.filter(Opportunity.tenant_id.is_(None))


def _get_or_404(db: Session, opportunity_id: str, current_user: User) -> Optional[Opportunity]:
    """
    处理 _get_or_404 相关业务逻辑。

    :param db: 入参 (Session)。
    :param opportunity_id: 入参 (str)。
    :param current_user: 入参 (User)。

    :return: 返回 Optional[Opportunity] 类型的结果。
    """
    q = db.query(Opportunity).filter(Opportunity.id == opportunity_id)
    q = _tenant_filter(q, current_user)
    return q.first()


# ─────────────────────────────────────────────
# 路由（静态路径 /opportunities/stages 必须先于 /{opportunity_id} 声明）
# ─────────────────────────────────────────────
@router.get(
    "/opportunities/stages",
    operation_id="crm_pipeline_list_stages",
    response_model=APIResponse,
    summary="阶段配置列表 (CRM管线)",
    description="返回商机管线全部阶段配置（顺序、中文名、赢单概率、是否终态）。\n\n认证: 需要有效 JWT",
)
def list_stage_configs(current_user: User = Depends(get_current_user)):
    """阶段配置：Lead → ... → Won / Lost。"""
    stages = [
        {
            "stage": s,
            "label": STAGE_LABELS[s],
            "order": i,
            "probability": STAGE_PROBABILITY[s],
            "is_terminal": s in TERMINAL_STAGES,
        }
        for i, s in enumerate(STAGE_ORDER)
    ]
    return success_response(data=stages)


@router.get(
    "/pipeline/stats",
    operation_id="crm_pipeline_stats",
    response_model=APIResponse,
    summary="管线统计 (CRM管线)",
    description="各阶段商机数量、总金额、加权金额（金额×阶段赢单概率）与转化率。\n\n认证: 需要有效 JWT",
)
def pipeline_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管线统计：各阶段数量 / 总金额 / 加权金额 / 转化率（DB 聚合）。"""
    rows = (
        _tenant_filter(db.query(
            Opportunity.stage,
            func.count(Opportunity.id),
            func.coalesce(func.sum(Opportunity.value), 0.0),
        ), current_user)
        .group_by(Opportunity.stage)
        .all()
    )
    by_stage: dict[str, tuple[int, float]] = {
        str(stage or "Lead"): (int(cnt), float(total or 0.0)) for stage, cnt, total in rows
    }
    stage_stats: list[dict[str, Any]] = []
    total_amount = 0.0
    weighted_amount = 0.0
    won = lost = 0
    total = 0
    for i, s in enumerate(STAGE_ORDER):
        cnt, amount = by_stage.get(s, (0, 0.0))
        weighted = amount * STAGE_PROBABILITY[s]
        total_amount += amount
        weighted_amount += weighted
        total += cnt
        if s == "Won":
            won = cnt
        elif s == "Lost":
            lost = cnt
        stage_stats.append({
            "stage": s,
            "label": STAGE_LABELS[s],
            "order": i,
            "probability": STAGE_PROBABILITY[s],
            "count": cnt,
            "amount": round(amount, 2),
            "weighted_amount": round(weighted, 2),
        })

    closed = won + lost
    stats: dict[str, Any] = {
        "total": total,
        "open": total - closed,
        "won": won,
        "lost": lost,
        "total_amount": round(total_amount, 2),
        "weighted_amount": round(weighted_amount, 2),
        "conversion_rate": round(won / closed, 4) if closed else 0.0,
        "win_rate": round(won / total, 4) if total else 0.0,
        "stages": stage_stats,
    }
    return success_response(data=stats)


@router.get(
    "/opportunities",
    operation_id="crm_pipeline_list_opportunities",
    response_model=APIResponse,
    summary="商机列表 (CRM管线)",
    description="分页查询商机，支持按阶段/企业/来源筛选，按字段排序。\n\n认证: 需要有效 JWT",
)
def list_opportunities(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    company_id: Optional[str] = Query(None, description="企业（客户）ID 筛选"),
    source: Optional[str] = Query(None, description="来源筛选"),
    sort_by: str = Query("created_at", description=f"排序字段: {', '.join(sorted(_SORTABLE_FIELDS))}"),
    sort_order: str = Query("desc", description="排序方向: asc / desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """商机列表（分页 + 筛选 + 排序，DB 查询）。"""
    if stage is not None and stage not in STAGE_PROBABILITY:
        return error_response(400, f"无效阶段: {stage}，可选: {', '.join(STAGE_ORDER)}")
    if sort_by not in _SORTABLE_FIELDS:
        return error_response(400, f"无效排序字段: {sort_by}，可选: {', '.join(sorted(_SORTABLE_FIELDS))}")

    query = _tenant_filter(db.query(Opportunity), current_user)
    if stage:
        query = query.filter(Opportunity.stage == stage)
    if company_id:
        query = query.filter(Opportunity.company_id == company_id)
    if source:
        query = query.filter(Opportunity.source == source)

    column_map = {
        "created_at": Opportunity.created_at,
        "updated_at": Opportunity.updated_at,
        "amount": Opportunity.value,
        "name": Opportunity.name,
        "expected_close_date": Opportunity.expected_close_date,
        "stage": Opportunity.stage,
    }
    order_col = column_map[sort_by]
    query = query.order_by(order_col.desc() if sort_order.lower() != "asc" else order_col.asc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()
    page_items = [_serialize(db, o) for o in rows]
    return success_response(data=page_items, total=total, page=page, page_size=page_size)


@router.post(
    "/opportunities",
    operation_id="crm_pipeline_create_opportunity",
    response_model=APIResponse,
    summary="创建商机 (CRM管线)",
    description="创建商机，初始阶段为 Lead。\n\n认证: 需要有效 JWT",
)
def create_opportunity(
    payload: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建商机（初始阶段 Lead，落库 + 阶段历史）。"""
    now = datetime.now(timezone.utc)
    item = Opportunity(
        name=payload.name.strip(),
        company_id=payload.company_id,
        contact_id=payload.contact_id,
        value=float(payload.amount or 0.0),
        currency=(payload.currency or "USD").upper(),
        expected_close_date=(
            datetime.combine(payload.expected_close_date, datetime.min.time(), tzinfo=timezone.utc)
            if payload.expected_close_date else None
        ),
        source=payload.source,
        stage="Lead",
        probability=int(STAGE_PROBABILITY["Lead"] * 100),
        notes=None,
        created_by=str(getattr(current_user, "id", "") or ""),
        tenant_id=str(getattr(current_user, "tenant_id", "") or "") or None,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    db.flush()
    db.add(OpportunityStage(
        opportunity_id=item.id,
        stage="Lead",
        changed_by=str(getattr(current_user, "id", "") or ""),
        notes=None,
        changed_at=now,
    ))
    db.commit()
    db.refresh(item)
    return success_response(data=_serialize(db, item, with_history=True), message="商机创建成功")


@router.get(
    "/opportunities/{opportunity_id}",
    operation_id="crm_pipeline_get_opportunity",
    response_model=APIResponse,
    summary="商机详情 (CRM管线)",
    description="按 ID 获取商机详情。\n\n认证: 需要有效 JWT",
)
def get_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """商机详情。"""
    item = _get_or_404(db, opportunity_id, current_user)
    if not item:
        return error_response(404, "商机不存在")
    return success_response(data=_serialize(db, item, with_history=True))


@router.patch(
    "/opportunities/{opportunity_id}",
    operation_id="crm_pipeline_update_opportunity",
    response_model=APIResponse,
    summary="更新商机 (CRM管线)",
    description="部分字段更新商机（阶段推进请使用 POST /opportunities/{id}/stages）。\n\n认证: 需要有效 JWT",
)
def update_opportunity(
    opportunity_id: str,
    payload: OpportunityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新商机（部分字段，DB 持久化）。"""
    item = _get_or_404(db, opportunity_id, current_user)
    if not item:
        return error_response(404, "商机不存在")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return error_response(400, "未提供任何需要更新的字段")

    field_map = {
        "name": "name",
        "company_id": "company_id",
        "contact_id": "contact_id",
        "amount": "value",
        "currency": "currency",
        "source": "source",
        "notes": "notes",
    }
    for key, value in updates.items():
        attr = field_map.get(key)
        if attr is None:
            continue
        if key == "currency" and value:
            value = str(value).upper()
        if key == "amount" and value is not None:
            value = float(value)
        setattr(item, attr, value)
    if "expected_close_date" in updates:
        ecd = updates["expected_close_date"]
        item.expected_close_date = (
            datetime.combine(ecd, datetime.min.time(), tzinfo=timezone.utc)
            if ecd else None
        )
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return success_response(data=_serialize(db, item, with_history=True), message="商机更新成功")


@router.post(
    "/opportunities/{opportunity_id}/stages",
    operation_id="crm_pipeline_advance_stage",
    response_model=APIResponse,
    summary="推进阶段 (CRM管线)",
    description="将商机推进到指定阶段并记录阶段历史与备注。\n\n认证: 需要有效 JWT",
)
def advance_stage(
    opportunity_id: str,
    payload: StageAdvanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """推进商机阶段（DB 事务 + 阶段历史落库）。"""
    target = (payload.stage or "").strip()
    if target not in STAGE_PROBABILITY:
        return error_response(400, f"无效阶段: {target}，可选: {', '.join(STAGE_ORDER)}")
    item = _get_or_404(db, opportunity_id, current_user)
    if not item:
        return error_response(404, "商机不存在")

    now = datetime.now(timezone.utc)
    previous = item.stage
    if previous == target:
        return error_response(400, f"商机已处于 {target} 阶段")

    # 状态机守卫：终态（Won/Lost）不允许再流转
    if previous in TERMINAL_STAGES:
        return error_response(400, f"商机已处于终态 {previous}，不可再推进")

    item.stage = target
    item.probability = int(STAGE_PROBABILITY[target] * 100)
    if payload.notes:
        item.notes = payload.notes
    item.updated_at = now
    db.add(OpportunityStage(
        opportunity_id=item.id,
        stage=target,
        changed_by=str(getattr(current_user, "id", "") or ""),
        notes=payload.notes,
        changed_at=now,
    ))
    db.commit()
    db.refresh(item)
    snapshot = _serialize(db, item, with_history=True)
    return success_response(
        data={
            "opportunity": snapshot,
            "previous_stage": previous,
            "current_stage": target,
            "advanced_at": now.isoformat(),
        },
        message=f"商机阶段已推进: {previous} → {target}",
    )
