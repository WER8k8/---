from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate, InquiryUpdate, InquiryResponse

router = APIRouter()


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    inquiry: InquiryCreate,
    db: Session = Depends(get_db),
):
    db_inquiry = Inquiry(
        name=inquiry.name,
        phone=inquiry.phone,
        email=inquiry.email,
        product=inquiry.product,
        message=inquiry.message,
        status="pending",
    )
    db.add(db_inquiry)
    db.commit()
    db.refresh(db_inquiry)
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
    
    # 转换字段以匹配前端期望
    result_items = []
    for item in items:
        item_dict = item.__dict__
        item_dict["customer_name"] = item_dict.get("name", "")
        item_dict["product_interest"] = item_dict.get("product", "")
        result_items.append(item_dict)
    
    return {"items": result_items, "total": total}


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


@router.delete("/{inquiry_id}")
def delete_inquiry(inquiry_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id, Inquiry.is_active == True).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="询盘不存在")
    inquiry.is_active = False
    db.commit()
    return {"message": "删除成功"}
