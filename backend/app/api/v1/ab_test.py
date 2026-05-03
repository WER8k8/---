"""A/B 测试 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.ab_test import ABTest, ABTestVariant, ABTestEvent, ABTestConversion
from app.models.user import User
from app.schemas.ab_test import (
    ABTestCreate,
    ABTestUpdate,
    ABTestResponse,
    ABTestVariantCreate,
    ABTestVariantUpdate,
    ABTestVariantResponse,
    ABTestEventCreate,
    ABTestEventResponse,
    ABTestConversionCreate,
    ABTestConversionResponse,
)

router = APIRouter(prefix="/ab-test", tags=["A/B 测试"])


@router.get("/", response_model=List[ABTestResponse])
def get_ab_tests(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="按状态筛选: draft/running/paused/completed"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """获取 A/B 测试列表"""
    query = db.query(ABTest)
    
    if status_filter:
        query = query.filter(ABTest.status == status_filter)
    
    tests = query.order_by(desc(ABTest.created_at)).offset(skip).limit(limit).all()
    
    return tests


@router.get("/{test_id}", response_model=ABTestResponse)
def get_ab_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个 A/B 测试详情"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    return test


@router.post("/", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
def create_ab_test(
    test_data: ABTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "create")),
):
    """创建新的 A/B 测试"""
    # 创建测试
    test = ABTest(
        name=test_data.name,
        description=test_data.description,
        experiment_type=test_data.experiment_type,
        target_url=test_data.target_url,
        variants_config=test_data.variants_config.dict(),
        traffic_percentage=test_data.traffic_percentage,
        primary_metric=test_data.primary_metric,
        secondary_metrics=test_data.secondary_metrics,
        min_sample_size=test_data.min_sample_size,
        confidence_level=test_data.confidence_level,
        start_date=test_data.start_date,
        end_date=test_data.end_date,
        created_by=current_user.id,
    )
    
    db.add(test)
    db.commit()
    db.refresh(test)
    
    # 创建变体记录
    for variant_config in test_data.variants_config.variants:
        variant = ABTestVariant(
            experiment_id=test.id,
            variant_id=variant_config.id,
            name=variant_config.name,
            weight=variant_config.weight,
            is_control=(variant_config.id == "A"),
        )
        db.add(variant)
    
    db.commit()
    
    return test


@router.put("/{test_id}", response_model=ABTestResponse)
def update_ab_test(
    test_id: int,
    test_data: ABTestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """更新 A/B 测试"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    # 更新字段
    if test_data.name is not None:
        test.name = test_data.name
    if test_data.description is not None:
        test.description = test_data.description
    if test_data.experiment_type is not None:
        test.experiment_type = test_data.experiment_type
    if test_data.target_url is not None:
        test.target_url = test_data.target_url
    if test_data.status is not None:
        test.status = test_data.status
    if test_data.variants_config is not None:
        test.variants_config = test_data.variants_config.dict()
    if test_data.traffic_percentage is not None:
        test.traffic_percentage = test_data.traffic_percentage
    if test_data.primary_metric is not None:
        test.primary_metric = test_data.primary_metric
    if test_data.secondary_metrics is not None:
        test.secondary_metrics = test_data.secondary_metrics
    if test_data.min_sample_size is not None:
        test.min_sample_size = test_data.min_sample_size
    if test_data.confidence_level is not None:
        test.confidence_level = test_data.confidence_level
    if test_data.start_date is not None:
        test.start_date = test_data.start_date
    if test_data.end_date is not None:
        test.end_date = test_data.end_date
    if test_data.winner_variant is not None:
        test.winner_variant = test_data.winner_variant
    
    db.commit()
    db.refresh(test)
    
    return test


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ab_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "delete")),
):
    """删除 A/B 测试"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    db.delete(test)
    db.commit()


@router.get("/{test_id}/variants", response_model=List[ABTestVariantResponse])
def get_test_variants(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取测试的所有变体"""
    variants = db.query(ABTestVariant).filter(ABTestVariant.experiment_id == test_id).all()
    
    return variants


@router.post("/{test_id}/variants", response_model=ABTestVariantResponse, status_code=status.HTTP_201_CREATED)
def create_variant(
    test_id: int,
    variant_data: ABTestVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """为测试添加变体"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    variant = ABTestVariant(
        experiment_id=test_id,
        variant_id=variant_data.variant_id,
        name=variant_data.name,
        description=variant_data.description,
        content_config=variant_data.content_config,
        weight=variant_data.weight,
        is_control=variant_data.is_control,
    )
    
    db.add(variant)
    db.commit()
    db.refresh(variant)
    
    return variant


@router.put("/{test_id}/variants/{variant_id}", response_model=ABTestVariantResponse)
def update_variant(
    test_id: int,
    variant_id: str,
    variant_data: ABTestVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """更新变体"""
    variant = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id,
        ABTestVariant.variant_id == variant_id
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="变体不存在"
        )
    
    if variant_data.name is not None:
        variant.name = variant_data.name
    if variant_data.description is not None:
        variant.description = variant_data.description
    if variant_data.content_config is not None:
        variant.content_config = variant_data.content_config
    if variant_data.weight is not None:
        variant.weight = variant_data.weight
    if variant_data.is_control is not None:
        variant.is_control = variant_data.is_control
    
    db.commit()
    db.refresh(variant)
    
    return variant


@router.delete("/{test_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    test_id: int,
    variant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """删除变体"""
    variant = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id,
        ABTestVariant.variant_id == variant_id
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="变体不存在"
        )
    
    db.delete(variant)
    db.commit()


@router.post("/{test_id}/events", response_model=ABTestEventResponse, status_code=status.HTTP_201_CREATED)
def track_event(
    test_id: int,
    event_data: ABTestEventCreate,
    db: Session = Depends(get_db),
):
    """追踪用户事件（公开接口）"""
    # 验证测试存在且正在运行
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    if test.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="测试未运行"
        )
    
    event = ABTestEvent(
        experiment_id=test_id,
        session_id=event_data.session_id,
        user_id=event_data.user_id,
        variant_id=event_data.variant_id,
        event_type=event_data.event_type,
        event_data=event_data.event_data,
        page_url=event_data.page_url,
        referrer=event_data.referrer,
        device_type=event_data.device_type,
        browser=event_data.browser,
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # 更新测试总访问数（只在首次访问时）
    if event_data.event_type == "impression":
        test.total_visitors = func.coalesce(test.total_visitors, 0) + 1
        db.commit()
    
    return event


@router.post("/{test_id}/conversions", response_model=ABTestConversionResponse, status_code=status.HTTP_201_CREATED)
def track_conversion(
    test_id: int,
    conversion_data: ABTestConversionCreate,
    db: Session = Depends(get_db),
):
    """追踪转化事件（公开接口）"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    if test.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="测试未运行"
        )
    
    conversion = ABTestConversion(
        experiment_id=test_id,
        variant_id=conversion_data.variant_id,
        session_id=conversion_data.session_id,
        user_id=conversion_data.user_id,
        conversion_type=conversion_data.conversion_type,
        conversion_value=conversion_data.conversion_value,
        conversion_data=conversion_data.conversion_data,
    )
    
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    
    # 更新变体转化统计
    variant = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id,
        ABTestVariant.variant_id == conversion_data.variant_id
    ).first()
    
    if variant:
        variant.conversions = func.coalesce(variant.conversions, 0) + 1
        variant.conversion_rate = (variant.conversions / max(variant.visitors, 1)) * 100
        db.commit()
    
    return conversion


@router.get("/{test_id}/results")
def get_test_results(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取测试结果分析"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    # 获取所有变体的统计数据
    variants = db.query(ABTestVariant).filter(ABTestVariant.experiment_id == test_id).all()
    
    results = []
    for variant in variants:
        # 计算转化相关数据
        conversions = db.query(ABTestConversion).filter(
            ABTestConversion.experiment_id == test_id,
            ABTestConversion.variant_id == variant.variant_id
        ).count()
        
        impressions = db.query(ABTestEvent).filter(
            ABTestEvent.experiment_id == test_id,
            ABTestEvent.variant_id == variant.variant_id,
            ABTestEvent.event_type == "impression"
        ).count()
        
        conversion_rate = (conversions / max(impressions, 1)) * 100
        
        results.append({
            "variant_id": variant.variant_id,
            "name": variant.name,
            "is_control": variant.is_control,
            "visitors": impressions,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 2),
            "weight": variant.weight,
        })
    
    # 计算统计显著性（简化版）
    if len(results) >= 2 and all(r["visitors"] >= test.min_sample_size for r in results):
        control = next((r for r in results if r["is_control"]), results[0])
        best_variant = max(results, key=lambda r: r["conversion_rate"])
        
        if control["conversion_rate"] != 0:
            lift = ((best_variant["conversion_rate"] - control["conversion_rate"]) / control["conversion_rate"]) * 100
        else:
            lift = float("inf") if best_variant["conversion_rate"] > 0 else 0
        
        significance = min(1.0, max(0.0, lift / 10))  # 简化的显著性计算
    else:
        lift = None
        significance = 0.0
        best_variant = None
    
    return {
        "test_id": test.id,
        "test_name": test.name,
        "status": test.status,
        "primary_metric": test.primary_metric,
        "total_visitors": test.total_visitors,
        "min_sample_size": test.min_sample_size,
        "results": results,
        "statistical_significance": round(significance, 4),
        "lift_percentage": round(lift, 2) if lift is not None else None,
        "best_variant": best_variant["variant_id"] if best_variant else None,
        "confidence_level": test.confidence_level,
    }


@router.post("/{test_id}/start")
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """启动 A/B 测试"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    if test.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="测试已在运行中"
        )
    
    test.status = "running"
    test.start_date = datetime.now()
    db.commit()
    db.refresh(test)
    
    return {"message": "测试已启动", "test": ABTestResponse.model_validate(test)}


@router.post("/{test_id}/pause")
def pause_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """暂停 A/B 测试"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    if test.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="测试未在运行中"
        )
    
    test.status = "paused"
    db.commit()
    db.refresh(test)
    
    return {"message": "测试已暂停", "test": ABTestResponse.model_validate(test)}


@router.post("/{test_id}/complete")
def complete_test(
    test_id: int,
    winner_variant: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ab_test", "update")),
):
    """完成 A/B 测试"""
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B 测试不存在"
        )
    
    test.status = "completed"
    test.end_date = datetime.now()
    test.winner_variant = winner_variant
    db.commit()
    db.refresh(test)
    
    return {"message": "测试已完成", "test": ABTestResponse.model_validate(test)}