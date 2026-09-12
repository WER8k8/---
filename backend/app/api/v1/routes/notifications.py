"""通知管理路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/notifications"
ROUTE_TAGS = ["通知管理"]

router = APIRouter(tags=["通知管理"])


def _notification_to_dict(n: Notification) -> dict:
    """将通知对象转换为字典"""
    return {
        "id": n.id,
        "user_id": n.user_id,
        "title": n.title,
        "content": n.content,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.post("/")
def send_notification(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送通知（管理员或系统）"""
    if current_user.role not in ["admin", "super_admin"]:
        return error_response(403, "权限不足")

    user_id = req.get("user_id")
    title = req.get("title")
    content = req.get("content")
    notification_type = req.get("type", "info")
    if not user_id or not title or not content:
        return error_response(400, "用户ID、标题和内容不能为空")

    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=notification_type,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return success_response(
        data=_notification_to_dict(notification), message="通知发送成功"
    )


@router.get("/")
def list_notifications(
    page: int = 1,
    page_size: int = 20,
    is_read: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看当前用户的通知列表（分页）"""
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    total = query.count()
    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [_notification_to_dict(n) for n in notifications]
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/{notification_id}")
def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个通知详情"""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        return error_response(404, "通知不存在")

    return success_response(data=_notification_to_dict(notification))


@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记通知为已读"""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        return error_response(404, "通知不存在")

    notification.is_read = True
    db.commit()
    return success_response(message="通知已标记为已读")


@router.put("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记所有通知为已读"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return success_response(message="所有通知已标记为已读")


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除通知"""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        return error_response(404, "通知不存在")

    db.delete(notification)
    db.commit()
    return success_response(message="通知删除成功")


@router.get("/stats/summary")
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取通知统计信息"""
    total = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .count()
    )
    unread = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id, Notification.is_read == False
        )
        .count()
    )
    read = total - unread
    return success_response(
        data={
            "total": total,
            "unread": unread,
            "read": read,
        }
    )
