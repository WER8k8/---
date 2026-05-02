from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.models.seo import Keyword, KeywordRanking, SiteAudit, AiOptimizationLog, LlmsConfig
from app.schemas.seo import KeywordCreate, KeywordUpdate, KeywordResponse, SiteAuditCreate, SiteAuditResponse, LlmsConfigCreate, LlmsConfigUpdate, LlmsConfigResponse
from app.api.v1.seo.dashboard import router as dashboard_router
from app.api.v1.seo.content_optimizer import router as content_optimizer_router
from app.api.v1.seo.llms_txt import router as llms_txt_router
from app.api.v1.seo.site_audit import router as site_audit_router
from app.api.v1.seo.batch_seo import router as batch_seo_router
from app.api.v1.seo.schema_markup import router as schema_markup_router
from app.api.v1.seo.eeat import router as eeat_router
from app.api.v1.seo.compliance import router as compliance_router
from app.api.v1.seo.keyword_ranking import router as keyword_ranking_router

router = APIRouter()
router.include_router(dashboard_router, tags=["seo-dashboard"])
router.include_router(content_optimizer_router, tags=["seo-content"])
router.include_router(llms_txt_router, tags=["seo-llms"])
router.include_router(batch_seo_router, tags=["seo-batch"])
router.include_router(site_audit_router, tags=["seo-audit"])
router.include_router(schema_markup_router, tags=["seo-schema"])
router.include_router(eeat_router, tags=["seo-eeat"])
router.include_router(compliance_router, tags=["seo-compliance"])
router.include_router(keyword_ranking_router, prefix="", tags=["seo-keyword-ranking"])

@router.get("/keywords", response_model=list[KeywordResponse])
def list_keywords(db: Session = Depends(get_db)):
    return db.query(Keyword).order_by(Keyword.search_volume.desc()).all()

@router.post("/keywords", response_model=KeywordResponse)
def create_keyword(req: KeywordCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    kw = Keyword(**req.model_dump())
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return kw

@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(keyword_id: str, req: KeywordUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(kw, k, v)
    db.commit()
    db.refresh(kw)
    return kw

@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    db.delete(kw)
    db.commit()
    return {"message": "删除成功"}

@router.post("/audits", response_model=SiteAuditResponse)
def create_audit(req: SiteAuditCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    audit = SiteAudit(**req.model_dump())
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

@router.get("/audits", response_model=list[SiteAuditResponse])
def list_audits(db: Session = Depends(get_db)):
    return db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).all()

@router.get("/audits/{audit_id}", response_model=SiteAuditResponse)
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(SiteAudit).filter(SiteAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="审计记录不存在")
    return audit

@router.get("/llms", response_model=list[LlmsConfigResponse])
def list_llms_configs(db: Session = Depends(get_db)):
    return db.query(LlmsConfig).filter(LlmsConfig.is_active == True).all()

@router.post("/llms", response_model=LlmsConfigResponse)
def create_llms_config(req: LlmsConfigCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    config = LlmsConfig(**req.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config

@router.put("/llms/{config_id}", response_model=LlmsConfigResponse)
def update_llms_config(config_id: str, req: LlmsConfigUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    config = db.query(LlmsConfig).filter(LlmsConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(config, k, v)
    db.commit()
    db.refresh(config)
    return config
