from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_admin, optional_auth
from app.models.user import User
from app.models.schema_markup import SchemaMarkup, SchemaTemplate
from app.schemas.schema_markup import (
    SchemaMarkupCreate,
    SchemaMarkupUpdate,
    SchemaMarkupResponse,
    SchemaTemplateResponse,
    GenerateSchemaRequest,
    ValidateSchemaRequest,
    SchemaValidationResult,
)
from app.services.schema_generator import SchemaGenerator

router = APIRouter(tags=["seo-schema"])
schema_generator = SchemaGenerator()


@router.get("/types")
def get_schema_types():
    """获取支持的Schema类型列表"""
    return {"types": schema_generator.get_schema_types()}


@router.get("/template/{schema_type}")
def get_schema_template(schema_type: str):
    """获取指定类型的Schema模板"""
    template = schema_generator.get_schema_template(schema_type)
    if not template:
        raise HTTPException(status_code=404, detail="不支持的Schema类型")
    return {"schema_type": schema_type, "template": template}


@router.post("/generate")
def generate_schema(req: GenerateSchemaRequest, current_user: User = Depends(optional_auth)):
    """根据业务数据生成Schema标记"""
    try:
        # 支持测试中的字段格式
        schema_type = req.schema_type or req.type or "Product"
        data = req.data if req.data else {
            "name": req.name,
            "description": req.description,
            "price": req.price
        }
        
        schema = schema_generator.generate_schema(
            schema_type=schema_type,
            data=data,
            include_context=req.include_context,
        )
        return {
            "success": True,
            "schema": schema,
            "json_ld": schema_generator.convert_to_json_ld(schema),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=SchemaValidationResult)
def validate_schema(req: ValidateSchemaRequest, current_user: User = Depends(optional_auth)):
    """验证Schema标记的有效性"""
    result = schema_generator.validate_schema(req.content)
    return SchemaValidationResult(**result)


@router.get("", response_model=list[SchemaMarkupResponse])
def list_schema_markups(db: Session = Depends(get_db)):
    """获取所有Schema标记记录"""
    return db.query(SchemaMarkup).filter(SchemaMarkup.is_active == True).order_by(SchemaMarkup.created_at.desc()).all()


@router.get("/{markup_id}", response_model=SchemaMarkupResponse)
def get_schema_markup(markup_id: str, db: Session = Depends(get_db)):
    """获取单个Schema标记记录"""
    markup = db.query(SchemaMarkup).filter(SchemaMarkup.id == markup_id).first()
    if not markup:
        raise HTTPException(status_code=404, detail="Schema标记不存在")
    return markup


@router.post("", response_model=SchemaMarkupResponse)
def create_schema_markup(
    req: SchemaMarkupCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """创建新的Schema标记记录"""
    # 先验证Schema内容
    validation = schema_generator.validate_schema(req.content)
    if not validation["is_valid"]:
        error_messages = "; ".join([e["message"] for e in validation["errors"]])
        raise HTTPException(status_code=400, detail=f"Schema验证失败: {error_messages}")

    markup = SchemaMarkup(**req.model_dump())
    db.add(markup)
    db.commit()
    db.refresh(markup)
    return markup


@router.put("/{markup_id}", response_model=SchemaMarkupResponse)
def update_schema_markup(
    markup_id: str,
    req: SchemaMarkupUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """更新Schema标记记录"""
    markup = db.query(SchemaMarkup).filter(SchemaMarkup.id == markup_id).first()
    if not markup:
        raise HTTPException(status_code=404, detail="Schema标记不存在")

    # 如果更新了content，先验证
    if req.content:
        validation = schema_generator.validate_schema(req.content)
        if not validation["is_valid"]:
            error_messages = "; ".join([e["message"] for e in validation["errors"]])
            raise HTTPException(status_code=400, detail=f"Schema验证失败: {error_messages}")

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(markup, k, v)
    db.commit()
    db.refresh(markup)
    return markup


@router.delete("/{markup_id}")
def delete_schema_markup(
    markup_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """删除Schema标记记录"""
    markup = db.query(SchemaMarkup).filter(SchemaMarkup.id == markup_id).first()
    if not markup:
        raise HTTPException(status_code=404, detail="Schema标记不存在")
    db.delete(markup)
    db.commit()
    return {"message": "删除成功"}


@router.get("/export/{markup_id}")
def export_schema_markup(markup_id: str, db: Session = Depends(get_db)):
    """导出Schema标记为JSON-LD格式"""
    markup = db.query(SchemaMarkup).filter(SchemaMarkup.id == markup_id).first()
    if not markup:
        raise HTTPException(status_code=404, detail="Schema标记不存在")

    json_ld = schema_generator.convert_to_json_ld(markup.content)
    return {
        "name": markup.name,
        "schema_type": markup.schema_type,
        "json_ld": json_ld,
    }


@router.get("/templates", response_model=list[SchemaTemplateResponse])
def list_schema_templates(db: Session = Depends(get_db)):
    """获取所有Schema模板"""
    return db.query(SchemaTemplate).filter(SchemaTemplate.is_active == True).all()
