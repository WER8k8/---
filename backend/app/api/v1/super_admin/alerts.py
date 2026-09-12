"""告警中心 API"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.alert import AlertEvent, AlertRule
from app.models.user import User
from app.services.alert_service import check_all_alerts, seed_default_alert_rules

router = APIRouter()


class AlertRuleCreate(BaseModel):
    name: str
    category: str
    metric_key: str
    operator: str = "gt"
    threshold: float
    enabled: bool = True
    notify_feishu: bool = True


@router.get("/rules")
def list_rules(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """告警规则列表"""
    rules = db.query(AlertRule).order_by(AlertRule.created_at.desc()).all()
    data = [{
        "id": str(r.id),
        "name": r.name,
        "category": r.category,
        "metric_key": r.metric_key,
        "operator": r.operator,
        "threshold": r.threshold,
        "duration_minutes": r.duration_minutes,
        "cooldown_minutes": r.cooldown_minutes,
        "enabled": r.enabled,
        "notify_feishu": r.notify_feishu,
    } for r in rules]
    return success_response(data=data)


@router.post("/rules")
def create_rule(
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """创建告警规则"""
    import uuid
    rule = AlertRule(
        id=str(uuid.uuid4()),
        name=body.name,
        category=body.category,
        metric_key=body.metric_key,
        operator=body.operator,
        threshold=body.threshold,
        enabled=body.enabled,
        notify_feishu=body.notify_feishu,
    )
    db.add(rule)
    db.commit()
    return success_response(data={"id": str(rule.id)}, message="规则创建成功")


@router.put("/rules/{rule_id}")
def update_rule(
    rule_id: str,
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """更新告警规则"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="规则不存在")
    for k, v in body.model_dump().items():
        setattr(rule, k, v)
    db.commit()
    return success_response(message="规则更新成功")


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """删除告警规则"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(rule)
    db.commit()
    return success_response(message="规则已删除")


@router.get("/events")
def list_events(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
):
    """告警事件列表"""
    query = db.query(AlertEvent)
    if status:
        query = query.filter(AlertEvent.status == status)
    if level:
        query = query.filter(AlertEvent.level == level)

    total = query.count()
    events = query.order_by(AlertEvent.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    data = [{
        "id": str(e.id),
        "rule_name": e.rule_name,
        "category": e.category,
        "level": e.level,
        "title": e.title,
        "message": e.message,
        "metric_value": e.metric_value,
        "threshold": e.threshold,
        "status": e.status,
        "acknowledged_by": e.acknowledged_by,
        "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in events]
    return success_response(data=data, total=total, page=page, page_size=page_size)


@router.post("/events/{event_id}/acknowledge")
def acknowledge_event(
    event_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """确认告警"""
    from datetime import datetime, timezone
    event = db.query(AlertEvent).filter(AlertEvent.id == event_id).first()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="事件不存在")
    event.status = "acknowledged"
    event.acknowledged_by = admin.username
    event.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(message="告警已确认")


@router.post("/events/{event_id}/resolve")
def resolve_event(
    event_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """解决告警"""
    from datetime import datetime, timezone
    event = db.query(AlertEvent).filter(AlertEvent.id == event_id).first()
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="事件不存在")
    event.status = "resolved"
    event.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return success_response(message="告警已解决")


@router.post("/check-now")
def trigger_alert_check(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """手动触发告警检测"""
    seed_default_alert_rules(db)
    events = check_all_alerts(db)
    return success_response(data={
        "checked": True,
        "new_events": len(events),
    })


@router.get("/summary")
def alert_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_super_admin),
):
    """告警摘要（给大盘用）"""
    open_count = db.query(AlertEvent).filter(AlertEvent.status == "open").count()
    critical_count = db.query(AlertEvent).filter(
        AlertEvent.status == "open", AlertEvent.level == "critical"
    ).count()
    recent = db.query(AlertEvent).filter(
        AlertEvent.status == "open"
    ).order_by(AlertEvent.created_at.desc()).limit(5).all()
    return success_response(data={
        "open_count": open_count,
        "critical_count": critical_count,
        "recent": [{
            "id": str(e.id),
            "title": e.title,
            "level": e.level,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in recent],
    })
