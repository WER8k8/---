import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_admin
from app.models.case_study import CaseStudy, CaseImage
from app.schemas.case_study import CaseStudyCreate, CaseStudyUpdate, CaseStudyResponse, CaseImageCreate, CaseImageResponse

router = APIRouter()

@router.get("")
def list_case_studies(
    is_published: str = None,
    search: str = None,
    is_active: bool = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(CaseStudy)
    if is_active is not None:
        q = q.filter(CaseStudy.is_active == is_active)
    if is_published is not None:
        q = q.filter(CaseStudy.status == ("published" if is_published == "true" else "draft"))
    if search:
        q = q.filter(CaseStudy.project_name.ilike(f"%{search}%"))
    
    total = q.count()
    items = q.order_by(CaseStudy.sort_order, CaseStudy.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result_items = []
    for item in items:
        item_dict = item.__dict__
        item_dict["title"] = item_dict.get("project_name", "")
        item_dict["location"] = item_dict.get("location", "")
        item_dict["project_type"] = item_dict.get("project_type", "other")
        item_dict["is_published"] = item_dict.get("status", "") == "published"
        result_items.append(item_dict)
    
    return {"items": result_items, "total": total}

@router.get("/stats")
def get_case_stats(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    total = db.query(func.count(CaseStudy.id)).filter(CaseStudy.is_active == True).scalar() or 0
    published = db.query(func.count(CaseStudy.id)).filter(CaseStudy.is_active == True, CaseStudy.status == "published").scalar() or 0
    draft = db.query(func.count(CaseStudy.id)).filter(CaseStudy.is_active == True, CaseStudy.status == "draft").scalar() or 0
    
    total_images = db.query(func.count(CaseImage.id)).scalar() or 0
    
    status_stats = db.query(
        CaseStudy.status,
        func.count(CaseStudy.id).label('count')
    ).filter(CaseStudy.is_active == True).group_by(CaseStudy.status).all()
    
    status_dict = {s: count for s, count in status_stats}
    
    return {
        "total": total,
        "published": published,
        "draft": draft,
        "total_images": total_images,
        "status_stats": status_dict,
    }

@router.post("/batch-delete")
def batch_delete_cases(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要删除的案例ID")
    
    cases = db.query(CaseStudy).filter(CaseStudy.id.in_(ids), CaseStudy.is_active == True).all()
    if not cases:
        raise HTTPException(status_code=404, detail="未找到指定案例")
    
    for case in cases:
        case.is_active = False
    
    db.commit()
    return {"message": f"成功删除 {len(cases)} 个案例", "deleted_count": len(cases)}

@router.post("/batch-update-status")
def batch_update_case_status(
    req: dict,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    ids = req.get("ids", [])
    new_status = req.get("status")
    
    if not ids or not new_status:
        raise HTTPException(status_code=400, detail="请提供案例ID和目标状态")
    
    if new_status not in ["draft", "published"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    cases = db.query(CaseStudy).filter(CaseStudy.id.in_(ids), CaseStudy.is_active == True).all()
    if not cases:
        raise HTTPException(status_code=404, detail="未找到指定案例")
    
    for case in cases:
        case.status = new_status
    
    db.commit()
    return {"message": f"成功更新 {len(cases)} 个案例状态", "updated_count": len(cases)}

@router.get("/by-slug/{slug}", response_model=CaseStudyResponse)
def get_case_study_by_slug(slug: str, db: Session = Depends(get_db)):
    case = db.query(CaseStudy).filter(CaseStudy.slug == slug).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    case.view_count += 1
    db.commit()
    return case

@router.get("/slug/{slug}", response_model=CaseStudyResponse)
def get_case_study_by_slug_alt(slug: str, db: Session = Depends(get_db)):
    case = db.query(CaseStudy).filter(CaseStudy.slug == slug, CaseStudy.is_active == True).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    case.view_count += 1
    db.commit()
    return case

@router.get("/{case_id}", response_model=CaseStudyResponse)
def get_case_study(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case

@router.post("", response_model=CaseStudyResponse)
def create_case_study(data: CaseStudyCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    existing = db.query(CaseStudy).filter(CaseStudy.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="slug 已存在")
    case = CaseStudy(**data.model_dump(), id=str(uuid.uuid4()))
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

@router.put("/{case_id}", response_model=CaseStudyResponse)
def update_case_study(case_id: str, data: CaseStudyUpdate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    if data.slug and data.slug != case.slug:
        existing = db.query(CaseStudy).filter(CaseStudy.slug == data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="slug 已存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(case, k, v)
    db.commit()
    db.refresh(case)
    return case

@router.delete("/{case_id}")
def delete_case_study(case_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    case.is_active = False
    db.commit()
    return {"message": "删除成功"}

@router.post("/{case_id}/increment-view")
def increment_view(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id, CaseStudy.is_active == True).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    case.view_count += 1
    db.commit()
    return {"view_count": case.view_count}

@router.post("/{case_id}/images", response_model=CaseImageResponse)
def add_case_image(case_id: str, data: CaseImageCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    img = CaseImage(**data.model_dump(), case_id=case_id, id=str(uuid.uuid4()))
    db.add(img)
    db.commit()
    db.refresh(img)
    return img

@router.get("/{case_id}/images", response_model=list[CaseImageResponse])
def list_case_images(case_id: str, db: Session = Depends(get_db)):
    case = db.query(CaseStudy).filter(CaseStudy.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案例不存在")
    return db.query(CaseImage).filter(
        CaseImage.case_id == case_id
    ).order_by(CaseImage.sort_order).all()

@router.delete("/{case_id}/images/{image_id}")
def delete_case_image(case_id: str, image_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    img = db.query(CaseImage).filter(CaseImage.id == image_id, CaseImage.case_id == case_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")
    db.delete(img)
    db.commit()
    return {"message": "删除成功"}
