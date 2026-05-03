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
from app.api.v1.seo.llms_txt_generator import router as llms_txt_gen_router

router = APIRouter()
router.include_router(dashboard_router, tags=["seo-dashboard"])
router.include_router(content_optimizer_router, prefix="/content-optimizer", tags=["seo-content"])
router.include_router(llms_txt_router, prefix="/llms-txt", tags=["seo-llms"])
router.include_router(llms_txt_gen_router, tags=["seo-llms-generator"])
router.include_router(batch_seo_router, tags=["seo-batch"])
router.include_router(site_audit_router, prefix="/site-audit", tags=["seo-audit"])
router.include_router(schema_markup_router, prefix="/schema-markup", tags=["seo-schema"])
router.include_router(eeat_router, tags=["seo-eeat"])
router.include_router(compliance_router, prefix="/compliance", tags=["seo-compliance"])
router.include_router(keyword_ranking_router, tags=["seo-keyword-ranking"])


@router.post("/audits", response_model=SiteAuditResponse)
def create_audit(req: SiteAuditCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """创建站点审计"""
    audit = SiteAudit(**req.model_dump())
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


@router.get("/audits", response_model=list[SiteAuditResponse])
def list_audits(db: Session = Depends(get_db)):
    """获取审计列表"""
    return db.query(SiteAudit).order_by(SiteAudit.created_at.desc()).all()


@router.get("/audits/{audit_id}", response_model=SiteAuditResponse)
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    """获取审计详情"""
    audit = db.query(SiteAudit).filter(SiteAudit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="审计记录不存在")
    return audit


@router.get("/llms", response_model=list[LlmsConfigResponse])
def list_llms_configs(db: Session = Depends(get_db)):
    """获取LLM配置列表"""
    return db.query(LlmsConfig).filter(LlmsConfig.is_active == True).all()


@router.post("/llms", response_model=LlmsConfigResponse)
def create_llms_config(req: LlmsConfigCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """创建LLM配置"""
    config = LlmsConfig(**req.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/llms/{config_id}", response_model=LlmsConfigResponse)
def update_llms_config(config_id: str, req: LlmsConfigUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    """更新LLM配置"""
    config = db.query(LlmsConfig).filter(LlmsConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(config, k, v)
    db.commit()
    db.refresh(config)
    return config
