from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.seo import SiteAudit, AiOptimizationLog
from app.schemas.seo import SiteAuditResponse, SiteAuditCreate
from app.services.site_audit import run_full_audit_service, run_quick_audit_service

router = APIRouter(prefix="/site-audit", tags=["站点审计"])


@router.post("", response_model=SiteAuditResponse)
def create_audit(audit_data: SiteAuditCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if audit_data.audit_type == "full":
        result = run_full_audit_service(db, audit_data)
    elif audit_data.audit_type == "quick":
        result = run_quick_audit_service(db, audit_data)
    else:
        raise HTTPException(status_code=400, detail="无效的审计类型，支持 full / quick")
    return result


@router.get("", response_model=list[SiteAuditResponse])
def list_audits(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{audit_id}", response_model=SiteAuditResponse)
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    record = db.query(SiteAudit).filter(SiteAudit.id == audit_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="审计记录不存在")
    return record
