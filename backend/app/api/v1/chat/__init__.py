# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""聊天模块API路由"""

import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import (APIRouter, Depends, HTTPException, WebSocket,
                     WebSocketDisconnect)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.security import get_current_user, optional_auth
from app.models.im_chat import IMMessage as ChatMessage, IMSession as ChatSession, UserStatus
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["聊天"])


# ==================== Pydantic Schemas ====================
class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    sender_avatar: str
    receiver_id: str
    content: str
    message_type: str
    is_read: bool
    created_at: datetime


class SessionResponse(BaseModel):
    id: str
    partner_id: str
    partner_name: str
    partner_avatar: str
    partner_status: str
    last_message: str
    last_message_time: datetime
    unread_count: int


class UserStatusResponse(BaseModel):
    user_id: str
    user_name: str
    status: str
    last_active_at: datetime


# ==================== WebSocket 实时通信 ====================
class ConnectionManager:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """connect。

        参数说明：
        :param self: 参数 self
        :param websocket: 参数 websocket
        :param user_id: 参数 user_id
        :return: 返回处理结果。
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        """disconnect。

        参数说明：
        :param self: 参数 self
        :param user_id: 参数 user_id
        :return: 返回处理结果。
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """send_personal_message。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param user_id: 参数 user_id
        :return: 返回处理结果。
        """
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast(self, message: dict):
        """broadcast。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket实时聊天连接"""
    await manager.connect(websocket, user_id)
    # 更新在线状态
    db = next(get_db())
    status = db.query(UserStatus).filter(UserStatus.user_id == user_id).first()
    if status:
        status.status = "online"
        status.last_active_at = datetime.utcnow()
    else:
        status = UserStatus(
            user_id=user_id,
            status="online",
            last_active_at=datetime.utcnow())
        db.add(status)
    db.commit()
    try:
        while True:
            data = await websocket.receive_json()
            # 处理接收到的消息
            if "action" in data:
                if data["action"] == "ping":
                    await websocket.send_json({"action": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # 更新离线状态
        status.status = "offline"
        status.last_active_at = datetime.utcnow()
        db.commit()


# ==================== REST API ====================
@router.get("/sessions")
async def get_chat_sessions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """获取当前用户的所有聊天会话"""
    sessions = (
        db.query(ChatSession) .filter(
            (ChatSession.user1_id == current_user.id) | (
                ChatSession.user2_id == current_user.id)) .order_by(
            ChatSession.updated_at.desc()) .all())

    result = []
    for session in sessions:
        # 获取对方用户信息
        partner_id = session.user2_id if session.user1_id == current_user.id else session.user1_id
        partner = db.query(User).filter(User.id == partner_id).first()
        partner_status = db.query(UserStatus).filter(
            UserStatus.user_id == partner_id).first()

        # 获取最后一条消息
        last_msg = None
        if session.last_message_id:
            last_msg = db.query(ChatMessage).filter(
                ChatMessage.id == session.last_message_id).first()

        result.append(
            {
                "id": session.id,
                "partner_id": partner_id,
                "partner_name": partner.name if partner else "未知用户",
                "partner_avatar": partner.avatar if partner else "",
                "partner_status": partner_status.status if partner_status else "offline",
                "last_message": last_msg.content if last_msg else "",
                "last_message_time": last_msg.created_at if last_msg else session.created_at,
                "unread_count": session.unread_count,
            })

    return result


@router.get("/messages/{partner_id}")
async def get_messages(
    partner_id: str,
    limit: int = 50,
    before_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取与指定用户的聊天消息"""
    query = (
        db.query(ChatMessage) .filter(
            ((ChatMessage.sender_id == current_user.id) & (
                ChatMessage.receiver_id == partner_id)) | (
                (ChatMessage.sender_id == partner_id) & (
                    ChatMessage.receiver_id == current_user.id))) .order_by(
                        ChatMessage.created_at.desc()))

    if before_id:
        before_msg = db.query(ChatMessage).filter(
            ChatMessage.id == before_id).first()
        if before_msg:
            query = query.filter(
                ChatMessage.created_at < before_msg.created_at)

    messages = query.limit(limit).all()
    # 标记消息为已读
    unread_messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.sender_id == partner_id,
            ChatMessage.is_read is False,
        )
        .all()
    )
    for msg in unread_messages:
        msg.is_read = True
    db.commit()
    # 更新会话未读计数
    session = (
        db.query(ChatSession) .filter(
            ((ChatSession.user1_id == current_user.id) & (
                ChatSession.user2_id == partner_id)) | (
                (ChatSession.user1_id == partner_id) & (
                    ChatSession.user2_id == current_user.id))) .first())
    if session:
        session.unread_count = 0
        db.commit()

    result = []
    for msg in reversed(messages):
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append(
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_name": sender.name if sender else "未知用户",
                "sender_avatar": sender.avatar if sender else "",
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "is_read": msg.is_read,
                "created_at": msg.created_at,
            }
        )

    return result


@router.post("/messages")
async def send_message(
        request: SendMessageRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """发送消息"""
    # 检查接收者是否存在
    receiver = db.query(User).filter(User.id == request.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="接收者不存在")

    # 创建消息
    message = ChatMessage(
        id=str(uuid.uuid4()),
        sender_id=current_user.id,
        receiver_id=request.receiver_id,
        content=request.content,
        message_type=request.message_type,
    )
    db.add(message)
    # 更新或创建会话
    session = (
        db.query(ChatSession) .filter(
            ((ChatSession.user1_id == current_user.id) & (
                ChatSession.user2_id == request.receiver_id)) | (
                (ChatSession.user1_id == request.receiver_id) & (
                    ChatSession.user2_id == current_user.id))) .first())

    if session:
        session.last_message_id = message.id
        session.unread_count += 1
        session.updated_at = datetime.utcnow()
    else:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user1_id=current_user.id,
            user2_id=request.receiver_id,
            last_message_id=message.id,
            unread_count=1,
        )
        db.add(session)

    db.commit()
    # 实时推送消息
    sender_info = {
        "id": current_user.id,
        "name": current_user.name,
        "avatar": current_user.avatar}

    await manager.send_personal_message(
        {
            "type": "new_message",
            "data": {
                "id": message.id,
                "sender_id": message.sender_id,
                "sender_name": current_user.name,
                "sender_avatar": current_user.avatar,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "message_type": message.message_type,
                "is_read": message.is_read,
                "created_at": message.created_at.isoformat(),
            },
        },
        request.receiver_id,
    )
    return success_response(
        data={
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_name": current_user.name,
            "sender_avatar": current_user.avatar,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "message_type": message.message_type,
            "is_read": message.is_read,
            "created_at": message.created_at,
        },
        message="发送成功",
    )


@router.get("/status/{user_id}")
async def get_user_status(user_id: str, db: Session = Depends(get_db)):
    """获取用户在线状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    status = db.query(UserStatus).filter(UserStatus.user_id == user_id).first()
    return success_response(data={
        "user_id": user.id,
        "user_name": user.name,
        "status": status.status if status else "offline",
        "last_active_at": status.last_active_at if status else datetime.utcnow(),
    })


@router.put("/status")
async def update_status(
        status: str = "online",
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """更新自己的在线状态"""
    valid_statuses = ["online", "offline", "busy", "away"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效状态，可选值: {valid_statuses}")

    user_status = db.query(UserStatus).filter(
        UserStatus.user_id == current_user.id).first()
    if user_status:
        user_status.status = status
        user_status.last_active_at = datetime.utcnow()
    else:
        user_status = UserStatus(
            user_id=current_user.id,
            status=status,
            last_active_at=datetime.utcnow())
        db.add(user_status)

    db.commit()
    return success_response(data={"status": status}, message="状态更新成功")


@router.get("/online-users")
async def get_online_users(db: Session = Depends(get_db)):
    """获取所有在线用户"""
    online_statuses = db.query(UserStatus).filter(
        UserStatus.status == "online").all()

    result = []
    for status in online_statuses:
        user = db.query(User).filter(User.id == status.user_id).first()
        if user:
            result.append(
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "status": status.status,
                    "last_active_at": status.last_active_at,
                }
            )

    return result
