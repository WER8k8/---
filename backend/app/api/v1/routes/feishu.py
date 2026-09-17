# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.response import APIResponse, success_response
from app.core.security import get_current_user
from app.models.feishu import FeishuBinding, FeishuMessageLog
from app.models.inquiry import Inquiry
from app.models.user import User
from app.services.feishu import card_builder, feishu_client, message_handler
from app.services.feishu.report import FeishuReportService

logger = logging.getLogger(__name__)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/feishu", tags=["飞书机器人"])


@router.post("/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    处理 feishu_webhook 相关业务逻辑。

    :param request: 入参 (Request)。
    :param background_tasks: 入参 (BackgroundTasks)。

    :return: 返回处理结果（或 None）。

    :raises HTTPException: 当相应错误条件触发时抛出。
    """
    body = await request.json()
    if settings.FEISHU_VERIFICATION_TOKEN:
        token = body.get("token", "")
        if token != settings.FEISHU_VERIFICATION_TOKEN:
            logger.warning("飞书Webhook验证Token不匹配")
            raise HTTPException(
                status_code=403,
                detail="Invalid verification token")
    elif (settings.ENVIRONMENT or "").strip().lower() == "production":
        logger.warning("生产环境未配置 FEISHU_VERIFICATION_TOKEN，拒绝飞书事件")
        raise HTTPException(status_code=503, detail="Feishu webhook not configured")

    challenge = body.get("challenge", "")
    if challenge:
        return {"challenge": challenge}

    event_type = body.get("type", "")
    if event_type == "url_preview":
        return {"challenge": body.get("challenge", "")}

    background_tasks.add_task(message_handler.handle_event, body)
    return {"code": 0, "message": "success"}


@router.post("/send")
async def send_feishu_message(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发送（send_feishu_message）：处理相关业务逻辑并返回结果。

    :param request: 入参 (Request)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    body = await request.json()
    open_id = body.get("open_id", "")
    msg_type = body.get("msg_type", "text")
    content = body.get("content", "")
    if not open_id or not content:
        return APIResponse.error(400, "open_id和content不能为空")

    if msg_type == "text":
        result = await feishu_client.send_text_message(open_id, content)
    elif msg_type == "interactive":
        try:
            card = json.loads(content) if isinstance(content, str) else content
            result = await feishu_client.send_card_message(open_id, card)
        except json.JSONDecodeError:
            return APIResponse.error(400, "卡片消息内容必须是有效的JSON")
    else:
        return APIResponse.error(400, f"不支持的消息类型: {msg_type}")

    if result.get("code") == 0:
        return success_response(
            {"message_id": result.get("data", {}).get("message_id", "")})
    return APIResponse.error(500, f"发送失败: {result.get('msg', '未知错误')}")


@router.post("/send/inquiry/{inquiry_id}")
async def send_inquiry_notification(
    inquiry_id: str,
    open_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发送（send_inquiry_notification）：处理相关业务逻辑并返回结果。

    :param inquiry_id: 入参 (str)。
    :param open_id: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        return APIResponse.error(404, "询盘不存在")

    inquiry_dict = {
        "id": str(inquiry.id),
        "name": inquiry.name,
        "phone": inquiry.phone,
        "email": inquiry.email or "",
        "product": inquiry.product or "",
        "message": inquiry.message,
        "status": inquiry.status,
        "created_at": inquiry.created_at,
    }
    card = card_builder.build_inquiry_notification(inquiry_dict)
    if open_id:
        result = await feishu_client.send_card_message(open_id, card)
    else:
        bindings = db.query(FeishuBinding).filter(
            FeishuBinding.is_active).all()
        results = []
        for binding in bindings:
            result = await feishu_client.send_card_message(binding.feishu_open_id, card)
            results.append({"open_id": binding.feishu_open_id,
                           "status": result.get("code") == 0})
        return success_response(
            {"sent_count": len(results), "results": results})

    if result.get("code") == 0:
        return success_response(
            {"message_id": result.get("data", {}).get("message_id", "")})
    return APIResponse.error(500, f"发送失败: {result.get('msg', '未知错误')}")


@router.get("/bind")
async def get_bindings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_bindings）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    bindings = (
        db.query(FeishuBinding)
        .filter(
            FeishuBinding.bound_user_id == str(current_user.id),
            FeishuBinding.is_active,
        )
        .all()
    )
    return success_response(
        [
            {
                "id": str(b.id),
                "feishu_open_id": b.feishu_open_id,
                "feishu_user_name": b.feishu_user_name,
                "bound_username": b.bound_username,
                "created_at": b.created_at.isoformat() if b.created_at else "",
            }
            for b in bindings
        ]
    )


@router.post("/bind")
async def bind_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 bind_account 相关业务逻辑。

    :param request: 入参 (Request)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    body = await request.json()
    open_id = body.get("open_id", "")
    user_name = body.get("user_name", "")
    system_user_id = body.get("user_id", str(current_user.id))
    if not open_id:
        return APIResponse.error(400, "open_id不能为空")

    existing = (
        db.query(FeishuBinding)
        .filter(
            FeishuBinding.feishu_open_id == open_id,
            FeishuBinding.is_active,
        )
        .first()
    )
    if existing:
        return APIResponse.error(
            400, f"该飞书账号已绑定系统用户: {existing.bound_username}")

    binding = FeishuBinding(
        feishu_open_id=open_id,
        feishu_user_name=user_name,
        bound_user_id=system_user_id,
        bound_username=current_user.username,
    )
    db.add(binding)
    db.commit()
    return success_response({"message": "绑定成功"})


@router.post("/unbind")
async def unbind_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 unbind_account 相关业务逻辑。

    :param request: 入参 (Request)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    body = await request.json()
    open_id = body.get("open_id", "")
    binding = (
        db.query(FeishuBinding)
        .filter(
            FeishuBinding.feishu_open_id == open_id,
            FeishuBinding.bound_user_id == str(current_user.id),
            FeishuBinding.is_active,
        )
        .first()
    )
    if not binding:
        return APIResponse.error(404, "未找到绑定记录")

    binding.is_active = False
    db.commit()
    return success_response({"message": "解绑成功"})


@router.get("/logs")
async def get_message_logs(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_message_logs）：处理相关业务逻辑并返回结果。

    :param page: 入参 (int)。
    :param page_size: 入参 (int)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    query = db.query(FeishuMessageLog).order_by(
        FeishuMessageLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    return APIResponse.paginated(
        data=[
            {
                "id": str(log.id),
                "feishu_open_id": log.feishu_open_id,
                "message_type": log.message_type,
                "content": log.content[:200],
                "direction": log.direction,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/report/daily")
async def get_daily_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取每日报告数据"""
    report_service = FeishuReportService(db)
    data = report_service.get_report_data()
    return success_response(data)


@router.post("/report/daily/send")
async def send_daily_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送每日报告到飞书"""
    body = await request.json()
    open_id = body.get("open_id", "")
    if not open_id:
        return APIResponse.error(400, "open_id不能为空")

    report_service = FeishuReportService(db)
    result = await report_service.send_daily_report(open_id)
    if result.get("code") == 0:
        return success_response(
            {"message_id": result.get("data", {}).get("message_id", "")})
    return APIResponse.error(500, f"发送失败: {result.get('msg', '未知错误')}")


@router.post("/report/daily/send/all")
async def send_daily_report_to_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送每日报告到所有已绑定的飞书用户"""
    bindings = db.query(FeishuBinding).filter(FeishuBinding.is_active).all()
    if not bindings:
        return APIResponse.error(404, "没有找到已绑定的飞书账号")

    report_service = FeishuReportService(db)
    results = []
    for binding in bindings:
        result = await report_service.send_daily_report(binding.feishu_open_id)
        results.append(
            {
                "open_id": binding.feishu_open_id,
                "user_name": binding.feishu_user_name,
                "success": result.get("code") == 0,
                "message": result.get("msg", ""),
            }
        )

    success_count = sum(1 for r in results if r["success"])
    return success_response(
        {
            "sent_count": len(results),
            "success_count": success_count,
            "results": results,
        }
    )
