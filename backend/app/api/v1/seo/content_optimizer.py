from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user, optional_auth
from app.models.user import User
from app.services.content_optimizer import ContentOptimizer
from app.services.ai_engine import get_ai_engine

router = APIRouter()


class OptimizeRequest(BaseModel):
    content: str = ""
    title: str = ""
    description: str = ""
    opt_type: str = "content"
    keywords: list[str] = []
    model: str = "deepseek-chat"


class ValidateRequest(BaseModel):
    original: str
    optimized: str


@router.post("/optimize")
async def optimize_content(req: OptimizeRequest, db: Session = Depends(get_db), current_user: User = Depends(optional_auth)):
    # 支持优化meta标签（title/description）的情况
    content_to_optimize = req.content or req.title or req.description
    
    if not content_to_optimize:
        raise HTTPException(status_code=400, detail="请提供要优化的内容、标题或描述")
    
    if req.opt_type not in ["title", "description", "alt_text", "content"]:
        raise HTTPException(status_code=400, detail="优化类型不支持，支持: title/description/alt_text/content")
    
    ai_engine = get_ai_engine()
    optimizer = ContentOptimizer(ai_engine=ai_engine)
    return await optimizer.optimize(
        content=content_to_optimize,
        opt_type=req.opt_type,
        keywords=req.keywords,
        model=req.model,
        db=db,
    )


@router.post("/validate-content")
def validate_content(req: ValidateRequest, current_user: User = Depends(optional_auth)):
    optimizer = ContentOptimizer()
    result = optimizer.validate_compliance(req.original, req.optimized)
    return result


class ExtractParamsRequest(BaseModel):
    content: str


@router.post("/extract-params")
def extract_params(req: ExtractParamsRequest, current_user: User = Depends(optional_auth)):
    optimizer = ContentOptimizer()
    params = optimizer.extract_technical_params(req.content)
    return {"technical_params": params, "found": len(params) > 0}
