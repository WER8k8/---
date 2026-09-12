"""
建材垂直参数 API路由

提供建材产品结构化参数的CRUD接口，以及移动端合并接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.im_routing_and_specs import MerchantIMRouting, BuildingMaterialSpec
from app.schemas.im_routing_and_specs import (
    BuildingMaterialSpecCreate,
    BuildingMaterialSpecUpdate,
    BuildingMaterialSpecResponse,
    ProductSpecsResponse,
)
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/building-specs", tags=["建材参数管理"])


@router.post("/", response_model=BuildingMaterialSpecResponse, status_code=201)
def create_building_spec(
    spec: BuildingMaterialSpecCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建建材参数"""
    db_spec = BuildingMaterialSpec(
        product_id=spec.product_id,
        spec_key=spec.spec_key,
        spec_value=spec.spec_value,
        metric_unit=spec.metric_unit,
        imperial_unit=spec.imperial_unit,
        imperial_scale_factor=spec.imperial_scale_factor,
        trust_badges=spec.trust_badges
    )
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec


@router.get("/", response_model=List[BuildingMaterialSpecResponse])
def list_building_specs(
    product_id: Optional[int] = Query(None, description="按产品ID过滤"),
    spec_key: Optional[str] = Query(None, description="按参数名过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出建材参数"""
    query = db.query(BuildingMaterialSpec)
    if product_id:
        query = query.filter(BuildingMaterialSpec.product_id == product_id)
    if spec_key:
        query = query.filter(BuildingMaterialSpec.spec_key == spec_key)
    
    return query.order_by(BuildingMaterialSpec.product_id, BuildingMaterialSpec.spec_key).all()


@router.get("/{spec_id}", response_model=BuildingMaterialSpecResponse)
def get_building_spec(
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个建材参数详情"""
    spec = db.query(BuildingMaterialSpec).filter(
        BuildingMaterialSpec.id == spec_id
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="建材参数不存在")
    
    return spec


@router.put("/{spec_id}", response_model=BuildingMaterialSpecResponse)
def update_building_spec(
    spec_id: int,
    spec_update: BuildingMaterialSpecUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新建材参数"""
    spec = db.query(BuildingMaterialSpec).filter(
        BuildingMaterialSpec.id == spec_id
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="建材参数不存在")
    
    update_data = spec_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(spec, field, value)
    
    db.commit()
    db.refresh(spec)
    return spec


@router.delete("/{spec_id}", status_code=204)
def delete_building_spec(
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除建材参数"""
    spec = db.query(BuildingMaterialSpec).filter(
        BuildingMaterialSpec.id == spec_id
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="建材参数不存在")
    
    db.delete(spec)
    db.commit()


@router.get("/product/{product_id}/mobile", response_model=ProductSpecsResponse)
async def get_product_specs_mobile(
    product_id: int,
    use_imperial: bool = Query(False, description="是否使用英制单位（欧美IP自动切换）"),
    db: Session = Depends(get_db)
):
    """移动端合并接口：获取产品参数（含单位换算）
    
    这是核心接口，供Nuxt 3服务端调用。
    Nuxt 3根据访客IP判断使用公制还是英制，调用此接口获取产品参数。
    返回格式供移动端渲染折叠框（手风琴组件）。
    """
    specs = db.query(BuildingMaterialSpec).filter(
        BuildingMaterialSpec.product_id == product_id
    ).all()
    if not specs:
        raise HTTPException(status_code=404, detail="产品参数不存在")
    
    # 转换参数（含单位换算）
    specs_response = []
    trust_badges_set = set()
    for spec in specs:
        spec_dict = {
            "id": spec.id,
            "product_id": spec.product_id,
            "spec_key": spec.spec_key,
            "spec_value": float(spec.spec_value) * float(spec.imperial_scale_factor) if use_imperial and spec.imperial_scale_factor else float(spec.spec_value),
            "spec_unit": spec.imperial_unit if use_imperial and spec.imperial_unit else spec.metric_unit,
            "trust_badges": spec.trust_badges or []
        }
        specs_response.append(spec_dict)
        # 收集所有证书（去重）
        if spec.trust_badges:
            trust_badges_set.update(spec.trust_badges)
    
    return {
        "product_id": product_id,
        "specs": specs_response,
        "trust_badges": list(trust_badges_set)
    }
