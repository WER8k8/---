# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI实时消息推送WebSocket"""

import json
import logging
import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import LogConfig
from app.core.security import get_current_user, optional_auth

logger = LogConfig.get_logger("ai_ws")

router = APIRouter()


# ==================== WebSocket连接管理器 ====================
class AIConnectionManager:
    """AI WebSocket连接管理器"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        # 存储格式: {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"AI WebSocket连接建立: user_id={user_id}")
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"AI WebSocket连接断开: user_id={user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """向指定用户发送消息"""
        if user_id in self.active_connections:
            message_json = json.dumps(message, ensure_ascii=False)
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"发送AI消息失败: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接的用户"""
        message_json = json.dumps(message, ensure_ascii=False)
        for user_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"广播AI消息失败: {e}")


# 全局连接管理器实例
ai_manager = AIConnectionManager()


# ==================== WebSocket端点 ====================
@router.websocket("/ws/{user_id}")
async def ai_websocket_endpoint(websocket: WebSocket, user_id: str):
    """AI实时消息推送WebSocket端点
    
    客户端可以连接此端点接收：
    - AI生成进度更新
    - AI任务完成通知
    - AI错误通知
    
    消息格式：
    ```json
    {
        "type": "progress|completed|error|info",
        "task_id": "任务ID",
        "task_type": "generate|optimize|analyze",
        "progress": 50,  // 进度百分比（0-100）
        "message": "消息内容",
        "result": {...},  // 完成时的结果数据
        "error": "错误信息",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    """
    await ai_manager.connect(websocket, user_id)
    try:
        # 发送欢迎消息
        await ai_manager.send_personal_message(
            {
                "type": "info",
                "message": "AI WebSocket连接已建立",
                "timestamp": logger.get_Current_time() if hasattr(logger, 'get_Current_time') else None,
            },
            user_id
        )
        # 监听客户端消息
        while True:
            data = await websocket.receive_json()
            # 处理客户端发送的消息
            if "action" in data:
                action = data["action"]
                if action == "ping":
                    # 心跳检测
                    await ai_manager.send_personal_message(
                        {"type": "pong", "timestamp": data.get("timestamp")},
                        user_id
                    )
                
                elif action == "subscribe_task":
                    # 订阅特定任务的更新
                    task_id = data.get("task_id")
                    if task_id:
                        # 这里可以将user_id和task_id关联，以便后续推送
                        # 简化实现：只是确认订阅
                        await ai_manager.send_personal_message(
                            {
                                "type": "info",
                                "message": f"已订阅任务 {task_id} 的更新",
                                "task_id": task_id,
                            },
                            user_id
                        )
                
                elif action == "unsubscribe_task":
                    # 取消订阅
                    task_id = data.get("task_id")
                    await ai_manager.send_personal_message(
                        {"type": "info", "message": f"已取消订阅任务 {task_id}"},
                        user_id
                    )
                
                else:
                    logger.warning(f"未知的AI WebSocket action: {action}")
                    await ai_manager.send_personal_message(
                        {"type": "error", "message": f"未知操作: {action}"},
                        user_id
                    )
            
    except WebSocketDisconnect:
        ai_manager.disconnect(user_id, websocket)
        logger.info(f"AI WebSocket断开: user_id={user_id}")
    
    except Exception as e:
        logger.error(f"AI WebSocket错误: {e}")
        ai_manager.disconnect(user_id, websocket)


# ==================== 辅助函数：推送AI任务更新 ====================
async def push_ai_task_progress(
    user_id: str,
    task_id: str,
    task_type: str,
    progress: int,
    message: str,
    metadata: Optional[Dict] = None
):
    """推送AI任务进度更新
    
    由AI服务调用，推送任务进度给指定用户。
    
    Args:
        user_id: 用户ID
        task_id: 任务ID
        task_type: 任务类型（generate/optimize/analyze）
        progress: 进度百分比（0-100）
        message: 进度消息
        metadata: 额外的元数据
    """
    msg = {
        "type": "progress",
        "task_id": task_id,
        "task_type": task_type,
        "progress": progress,
        "message": message,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    if metadata:
        msg["metadata"] = metadata
    
    
    await ai_manager.send_personal_message(msg, user_id)


async def push_ai_task_completed(
    user_id: str,
    task_id: str,
    task_type: str,
    result: Dict[str, Any]
):
    """推送AI任务完成通知"""
    msg = {
        "type": "completed",
        "task_id": task_id,
        "task_type": task_type,
        "result": result,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    await ai_manager.send_personal_message(msg, user_id)


async def push_ai_task_error(
    user_id: str,
    task_id: str,
    task_type: str,
    error: str
):
    """推送AI任务错误通知"""
    msg = {
        "type": "error",
        "task_id": task_id,
        "task_type": task_type,
        "error": error,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    await ai_manager.send_personal_message(msg, user_id)
