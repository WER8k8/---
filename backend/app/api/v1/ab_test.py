# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import require_admin
from app.models.ab_test import (ABTest, ABTestConversion, ABTestEvent,
                                ABTestVariant)
from app.schemas.ab_test import (ABTestConversionResponse, ABTestCreate,
                                 ABTestDetailResponse, ABTestEventResponse,
                                 ABTestResponse, ABTestUpdate,
                                 ABTestVariantCreate, ABTestVariantResponse,
                                 ABTestVariantUpdate, BatchDeleteRequest)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/ab-test"
ROUTE_TAGS = ["A/B测试"]

router = APIRouter()


@router.get("")
def list_ab_tests(
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """list_ab_tests。

    参数说明：
    :param status: 参数 status
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    q = db.query(ABTest)
    if status:
        q = q.filter(ABTest.status == status)

    total = q.count()
    items = q.order_by(ABTest.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size})


@router.get("/{test_id}", response_model=ABTestDetailResponse)
def get_ab_test(test_id: int, db: Session = Depends(get_db)):
    """get_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    variants = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id).all()

    # Serialize via Pydantic model_validate on the ORM object directly
    # (NOT __dict__ which includes _sa_instance_state etc.)
    result = ABTestDetailResponse.model_validate(test)
    result.variants = [
        ABTestVariantResponse.model_validate(v) for v in variants]
    return result


@router.post("", response_model=ABTestResponse)
def create_ab_test(
        req: ABTestCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_ab_test。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    variants_config_json = (
        json.dumps(
            req.variants_config) if isinstance(
            req.variants_config,
            dict) else req.variants_config)
    secondary_metrics_json = json.dumps(
        req.secondary_metrics) if req.secondary_metrics else None

    test = ABTest(variants_config=variants_config_json,
                  secondary_metrics=secondary_metrics_json,
                  **{k: v for k,
                      v in req.model_dump().items() if k not in ["variants_config",
                                                                 "secondary_metrics"]},
                  )
    db.add(test)
    db.commit()
    db.refresh(test)
    for variant in req.variants_config.get("variants", []):
        ab_variant = ABTestVariant(
            experiment_id=test.id,
            variant_id=variant.get("id"),
            name=variant.get("name"),
            weight=variant.get("weight", 50.0),
            is_control=variant.get("id") == "A",
        )
        db.add(ab_variant)

    db.commit()
    return test


@router.put("/{test_id}", response_model=ABTestResponse)
def update_ab_test(
        test_id: int,
        req: ABTestUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    update_data = req.model_dump(exclude_unset=True)
    if "variants_config" in update_data and isinstance(
            update_data["variants_config"], dict):
        update_data["variants_config"] = json.dumps(
            update_data["variants_config"])
    if "secondary_metrics" in update_data:
        update_data["secondary_metrics"] = json.dumps(
            update_data["secondary_metrics"])

    for k, v in update_data.items():
        setattr(test, k, v)
    db.commit()
    db.refresh(test)
    return test


@router.delete("/{test_id}")
def delete_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    db.delete(test)
    db.commit()
    return success_response(message="删除成功")


@router.post("/{test_id}/start")
def start_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """start_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    if test.status == "running":
        raise HTTPException(status_code=400, detail="测试已在运行中")

    test.status = "running"
    test.start_date = datetime.now(timezone.utc)
    db.commit()
    return success_response(message="测试已启动")


@router.post("/{test_id}/pause")
def pause_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """pause_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    if test.status != "running":
        raise HTTPException(status_code=400, detail="测试未在运行中")

    test.status = "paused"
    db.commit()
    return success_response(message="测试已暂停")


@router.post("/{test_id}/complete")
def complete_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """complete_ab_test。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    test.status = "completed"
    test.end_date = datetime.now(timezone.utc)
    variants = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id).all()
    if variants:
        winner = max(variants, key=lambda v: v.conversion_rate)
        test.winner_variant = winner.variant_id

    db.commit()
    return success_response(data={"message": "测试已完成", "winner_variant": test.winner_variant})


@router.get("/{test_id}/variants", response_model=List[ABTestVariantResponse])
def list_variants(test_id: int, db: Session = Depends(get_db)):
    """list_variants。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    return (
        db.query(ABTestVariant).filter(
            ABTestVariant.experiment_id == test_id).order_by(
            ABTestVariant.variant_id).all())


@router.post("/{test_id}/variants", response_model=ABTestVariantResponse)
def create_variant(
        test_id: int,
        req: ABTestVariantCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """create_variant。

    参数说明：
    :param test_id: 参数 test_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    existing = (
        db.query(ABTestVariant) .filter(
            ABTestVariant.experiment_id == test_id,
            ABTestVariant.variant_id == req.variant_id) .first())
    if existing:
        raise HTTPException(status_code=400, detail="变体ID已存在")

    content_config_json = json.dumps(
        req.content_config) if req.content_config else None
    variant = ABTestVariant(
        experiment_id=test_id,
        content_config=content_config_json,
        **{k: v for k, v in req.model_dump().items() if k != "content_config"},
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.put("/{test_id}/variants/{variant_id}",
            response_model=ABTestVariantResponse)
def update_variant(
        test_id: int,
        variant_id: int,
        req: ABTestVariantUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """update_variant。

    参数说明：
    :param test_id: 参数 test_id
    :param variant_id: 参数 variant_id
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    variant = (
        db.query(ABTestVariant).filter(
            ABTestVariant.id == variant_id,
            ABTestVariant.experiment_id == test_id).first())
    if not variant:
        raise HTTPException(status_code=404, detail="变体不存在")

    update_data = req.model_dump(exclude_unset=True)
    if "content_config" in update_data:
        update_data["content_config"] = json.dumps(
            update_data["content_config"])

    for k, v in update_data.items():
        setattr(variant, k, v)
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/{test_id}/variants/{variant_id}")
def delete_variant(
        test_id: int,
        variant_id: int,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """delete_variant。

    参数说明：
    :param test_id: 参数 test_id
    :param variant_id: 参数 variant_id
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    variant = (
        db.query(ABTestVariant).filter(
            ABTestVariant.id == variant_id,
            ABTestVariant.experiment_id == test_id).first())
    if not variant:
        raise HTTPException(status_code=404, detail="变体不存在")

    db.delete(variant)
    db.commit()
    return success_response(message="删除成功")


@router.get("/{test_id}/events", response_model=List[ABTestEventResponse])
def list_events(
        test_id: int,
        event_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """list_events。

    参数说明：
    :param test_id: 参数 test_id
    :param event_type: 参数 event_type
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    q = db.query(ABTestEvent).filter(ABTestEvent.experiment_id == test_id)
    if event_type:
        q = q.filter(ABTestEvent.event_type == event_type)

    return q.order_by(ABTestEvent.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()


@router.get("/{test_id}/conversions",
            response_model=List[ABTestConversionResponse])
def list_conversions(
        test_id: int,
        variant_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_db)):
    """list_conversions。

    参数说明：
    :param test_id: 参数 test_id
    :param variant_id: 参数 variant_id
    :param page: 参数 page
    :param page_size: 参数 page_size
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    q = db.query(ABTestConversion).filter(
        ABTestConversion.experiment_id == test_id)
    if variant_id:
        q = q.filter(ABTestConversion.variant_id == variant_id)

    return q.order_by(
        ABTestConversion.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()


@router.post("/{test_id}/track-event")
def track_event(
    test_id: int,
    session_id: str,
    variant_id: str,
    event_type: str,
    user_id: Optional[str] = None,
    page_url: Optional[str] = None,
    referrer: Optional[str] = None,
    device_type: Optional[str] = None,
    browser: Optional[str] = None,
    event_data: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """track_event。

    参数说明：
    :param test_id: 参数 test_id
    :param session_id: 参数 session_id
    :param variant_id: 参数 variant_id
    :param event_type: 参数 event_type
    :param user_id: 参数 user_id
    :param page_url: 参数 page_url
    :param referrer: 参数 referrer
    :param device_type: 参数 device_type
    :param browser: 参数 browser
    :param event_data: 参数 event_data
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(
        ABTest.id == test_id,
        ABTest.status == "running").first()
    if not test:
        raise HTTPException(status_code=400, detail="测试未在运行中")

    event_data_json = json.dumps(event_data) if event_data else None
    event = ABTestEvent(
        experiment_id=test_id,
        session_id=session_id,
        user_id=user_id,
        variant_id=variant_id,
        event_type=event_type,
        event_data=event_data_json,
        page_url=page_url,
        referrer=referrer,
        device_type=device_type,
        browser=browser,
    )
    db.add(event)
    if event_type == "conversion":
        conversion = ABTestConversion(
            experiment_id=test_id,
            variant_id=variant_id,
            session_id=session_id,
            user_id=user_id,
            conversion_type="click",
            conversion_data=event_data_json,
        )
        db.add(conversion)
        variant = (
            db.query(ABTestVariant) .filter(
                ABTestVariant.experiment_id == test_id,
                ABTestVariant.variant_id == variant_id) .first())
        if variant:
            variant.conversions += 1

    db.commit()
    return success_response(message="事件已记录")


@router.get("/{test_id}/stats")
def get_test_stats(test_id: int, db: Session = Depends(get_db)):
    """get_test_stats。

    参数说明：
    :param test_id: 参数 test_id
    :param db: 参数 db
    :return: 返回处理结果。
    """
    test = db.query(ABTest).filter(ABTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="A/B测试不存在")

    variants = db.query(ABTestVariant).filter(
        ABTestVariant.experiment_id == test_id).all()

    stats = []
    for variant in variants:
        events_count = (
            db.query(ABTestEvent) .filter(
                ABTestEvent.experiment_id == test_id,
                ABTestEvent.variant_id == variant.variant_id) .count())
        conversions = (
            db.query(ABTestConversion) .filter(
                ABTestConversion.experiment_id == test_id,
                ABTestConversion.variant_id == variant.variant_id) .count())

        stats.append(
            {
                "variant_id": variant.variant_id,
                "name": variant.name,
                "visitors": variant.visitors,
                "conversions": conversions,
                "conversion_rate": round((conversions / max(variant.visitors, 1)) * 100, 2),
            }
        )

    return success_response(data={
        "test_id": test_id,
        "name": test.name,
        "stats": stats,
        "total_visitors": test.total_visitors})


@router.post("/batch-delete")
def batch_delete_tests(
        req: BatchDeleteRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)):
    """batch_delete_tests。

    参数说明：
    :param req: 参数 req
    :param db: 参数 db
    :param admin: 参数 admin
    :return: 返回处理结果。
    """
    if not req.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的测试")

    deleted = db.query(ABTest).filter(
        ABTest.id.in_(
            req.ids)).delete(
        synchronize_session=False)
    db.commit()
    return success_response(data={"message": f"成功删除 {deleted} 个测试", "deleted_count": deleted})
