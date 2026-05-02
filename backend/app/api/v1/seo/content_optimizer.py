from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.content_optimizer import ContentOptimizer
from app.services.ai_engine import get_ai_engine

router = APIRouter()


class OptimizeRequest(BaseModel):
    content: str
    opt_type: str = "content"
    keywords: list[str] = []
    model: str = "deepseek-chat"


class ValidateRequest(BaseModel):
    original: str
    optimized: str


@router.post("/optimize-content")
async def optimize_content(req: OptimizeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if len(req.content) < 10:
        raise HTTPException(status_code=400, detail="内容过短，至少10个字符")
    if req.opt_type not in ["title", "description", "alt_text", "content"]:
        raise HTTPException(status_code=400, detail="优化类型不支持，支持: title/description/alt_text/content")
    if not req.keywords:
        raise HTTPException(status_code=400, detail="至少需要一个关键词")

    provider = "deepseek" if "deepseek" in req.model.lower() else "openai"
    ai_engine = get_ai_engine(provider)
    optimizer = ContentOptimizer(ai_engine=ai_engine)
    return await optimizer.optimize(
        content=req.content,
        opt_type=req.opt_type,
        keywords=req.keywords,
        model=req.model,
        db=db,
    )


@router.post("/validate-content")
def validate_content(req: ValidateRequest, current_user: User = Depends(get_current_user)):
    optimizer = ContentOptimizer()
    result = optimizer.validate_compliance(req.original, req.optimized)
    return result


class ExtractParamsRequest(BaseModel):
    content: str


@router.post("/extract-params")
def extract_params(req: ExtractParamsRequest, current_user: User = Depends(get_current_user)):
    optimizer = ContentOptimizer()
    params = optimizer.extract_technical_params(req.content)
    return {"technical_params": params, "found": len(params) > 0}
