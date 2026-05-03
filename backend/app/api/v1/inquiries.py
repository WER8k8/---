from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import require_admin
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate, InquiryUpdate, InquiryResponse
from app.services.email_service import email_service
import re

router = APIRouter()


def sanitize_input(value: str) -> str:
    """清理输入，防止XSS攻击"""
    if not value:
        return value
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
    return value.strip()


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    inquiry: InquiryCreate,
    db: Session = Depends(get_db),
):
    name = sanitize_input(inquiry.name)
    phone = sanitize_input(inquiry.phone)
    email = sanitize_input(inquiry.email) if inquiry.email else None
    product = sanitize_input(inquiry.product) if inquiry.product else None
    message = sanitize_input(inquiry.message)
    
    db_inquiry = Inquiry(
        name=name,
        phone=phone,
        email=email,
        product=product,
        message=message,
        status="pending",
    )
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
    
    inquiry_data = {
        "name": db_inquiry.name,
        "phone": db_inquiry.phone,
        "email": db_inquiry.email,
        "product": db_inquiry.product,
        "message": db_inquiry.message,
    }
    
    try:
        email_service.send_inquiry_notification(inquiry_data)
        if db_inquiry.email:
            email_service.send_inquiry_confirmation(inquiry_data)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"邮件通知发送失败: {str(e)}")
    
    return db_inquiry


@router.get("")
def list_inquiries(
    search: str = "",
    status: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    q = db.query(Inquiry).filter(Inquiry.is_active == True)
    if status:
        q = q.filter(Inquiry.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Inquiry.name.ilike(like)) |
            (Inquiry.phone.ilike(like)) |
            (Inquiry.email.ilike(like)) |
            (Inquiry.product.ilike(like)) |
            (Inquiry.message.ilike(like))
        )
    
    total = q.count()
    items = q.order_by(Inquiry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result_items = []
    for item in items:
        item_dict = item.__dict__
        item_dict["customer_name"] = item_dict.get("name", "")
        item_dict["product_interest"] = item_dict.get("product", "")
        result_items.append(item_dict)
    
    return {"items": result_items, "total": total}


@router.get("/stats")
def get_inquiry_stats(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    total = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True).scalar() or 0
    pending = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True, Inquiry.status == "pending").scalar() or 0
    contacted = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True, Inquiry.status == "contacted").scalar() or 0
    converted = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active == True, Inquiry.status == "converted").scalar() or 0
    
    today = datetime.now().date()
    today_count = db.query(func.count(Inquiry.id)).filter(
        Inquiry.is_active == True,
        func.date(Inquiry.created_at) == today
    ).scalar() or 0
    
    week_ago = today - timedelta(days=7)
    week_count = db.query(func.count(Inquiry.id)).filter(
        Inquiry.is_active == True,
        func.date(Inquiry.created_at) >= week_ago
    ).scalar() or 0
    
    status_stats = db.query(
        Inquiry.status,
        func.count(Inquiry.id).label('count')
    ).filter(Inquiry.is_active == True).group_by(Inquiry.status).all()
    
    status_dict = {s: count for s, count in status_stats}
    
    return {
        "total": total,
        "pending": pending,
        "contacted": contacted,
        "converted": converted,
        "today": today_count,
        "this_week": week_count,
        "status_stats": status_dict,
    }


@router.post("/batch-delete")
def batch_delete_inquiries(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要删除的询盘ID")
    
    inquiries = db.query(Inquiry).filter(Inquiry.id.in_(ids), Inquiry.is_active == True).all()
    if not inquiries:
        raise HTTPException(status_code=404, detail="未找到指定询盘")
    
    for inquiry in inquiries:
        inquiry.is_active = False
    
    db.commit()
    return {"message": f"成功删除 {len(inquiries)} 个询盘", "deleted_count": len(inquiries)}


@router.post("/batch-update-status")
def batch_update_status(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    new_status = req.get("status")
    
    if not ids or not new_status:
        raise HTTPException(status_code=400, detail="请提供询盘ID和目标状态")
    
    if new_status not in ["pending", "contacted", "converted", "closed"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    inquiries = db.query(Inquiry).filter(Inquiry.id.in_(ids), Inquiry.is_active == True).all()
    if not inquiries:
        raise HTTPException(status_code=404, detail="未找到指定询盘")
    
    for inquiry in inquiries:
        inquiry.status = new_status
    
    db.commit()
    return {"message": f"成功更新 {len(inquiries)} 个询盘状态", "updated_count": len(inquiries)}


@router.get("/export")
def export_inquiries(
    status_filter: str = "",
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    q = db.query(Inquiry).filter(Inquiry.is_active == True)
    if status_filter:
        q = q.filter(Inquiry.status == status_filter)
    inquiries = q.order_by(Inquiry.created_at.desc()).all()
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "姓名", "电话", "邮箱", "产品", "留言", "状态", "创建时间"])
    for i in inquiries:
        writer.writerow([i.id, i.name, i.phone, i.email or "", i.product or "", i.message, i.status, i.created_at.strftime("%Y-%m-%d %H:%M")])
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inquiries.csv"},
    )


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(
    inquiry_id: str,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id, Inquiry.is_active == True).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="询盘不存在")
    return inquiry


@router.put("/{inquiry_id}/status", response_model=InquiryResponse)
def update_inquiry_status(
    inquiry_id: str,
    req: InquiryUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id, Inquiry.is_active == True).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="询盘不存在")
    if req.status is not None:
        inquiry.status = req.status
    db.commit()
    db.refresh(inquiry)
    return inquiry


@router.put("/{inquiry_id}", response_model=InquiryResponse)
def update_inquiry(
    inquiry_id: str,
    req: InquiryUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id, Inquiry.is_active == True).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="询盘不存在")
    
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if k in ["name", "phone", "email", "product", "message"]:
            setattr(inquiry, k, sanitize_input(v))
        else:
            setattr(inquiry, k, v)
    
    db.commit()
    db.refresh(inquiry)
    return inquiry


@router.delete("/{inquiry_id}")
def delete_inquiry(inquiry_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id, Inquiry.is_active == True).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="询盘不存在")
    inquiry.is_active = False
    db.commit()
    return {"message": "删除成功"}
