# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""告警引擎：检测 + 通知"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.core.config import settings
from app.models.ai_config import AIUsageLog
from app.models.alert import AlertEvent, AlertRule


def check_all_alerts(db: Session) -> List[AlertEvent]:
    """运行所有启用的告警规则，返回新产生的告警事件"""
    rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
    events = []
    for rule in rules:
        # 冷却检查
        if not _should_fire(rule, db):
            continue
        event = _evaluate_rule(rule, db)
        if event:
            db.add(event)
            db.flush()
            events.append(event)
            # 发送通知
            if rule.notify_feishu:
                _send_feishu_notification(event, rule)
    db.commit()
    return events


def _should_fire(rule: AlertRule, db: Session) -> bool:
    """检查是否在冷却期内"""
    since = datetime.now(timezone.utc) - timedelta(minutes=rule.cooldown_minutes)
    recent = db.query(AlertEvent).filter(
        AlertEvent.rule_id == rule.id,
        AlertEvent.created_at >= since,
        AlertEvent.status != "resolved",
    ).first()
    return recent is None


def _evaluate_rule(rule: AlertRule, db: Session) -> Optional[AlertEvent]:
    """评估单条规则"""
    value = _get_metric_value(rule.metric_key, rule.duration_minutes, db)
    if value is None:
        return None

    triggered = False
    if rule.operator == "gt" and value > rule.threshold:
        triggered = True
    elif rule.operator == "lt" and value < rule.threshold:
        triggered = True
    elif rule.operator == "eq" and abs(value - rule.threshold) < 0.001:
        triggered = True

    if not triggered:
        return None

    level = "warning"
    if value > rule.threshold * 3:
        level = "critical"
    elif value > rule.threshold * 1.5:
        level = "warning"

    return AlertEvent(
        rule_id=rule.id,
        rule_name=rule.name,
        category=rule.category,
        level=level,
        title=f"[{rule.category}] {rule.name}",
        message=f"指标 {rule.metric_key} = {value}，阈值 = {rule.threshold}",
        metric_value=value,
        threshold=rule.threshold,
        status="open",
        created_at=datetime.now(timezone.utc),
    )


def _get_metric_value(metric_key: str, window_minutes: int, db: Session) -> Optional[float]:
    """获取监控指标当前值"""
    since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    if metric_key == "ai_error_rate":
        total = db.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.created_at >= since
        ).scalar() or 0
        if total == 0:
            return 0
        errors = db.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.created_at >= since,
            AIUsageLog.success == False,
        ).scalar() or 0
        return round(errors / total * 100, 1)

    if metric_key == "ai_call_count":
        return db.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.created_at >= since
        ).scalar() or 0

    if metric_key == "cc_switch_status":
        from app.models.ai_config import CCSwitchConfig
        active = db.query(func.count(CCSwitchConfig.id)).filter(
            CCSwitchConfig.is_active == True
        ).scalar() or 0
        return float(active)

    if metric_key == "redis_memory_mb":
        if redis_client:
            try:
                info = redis_client.info()
                return round(info.get("used_memory", 0) / 1024 / 1024, 1)
            except Exception:
                return None
        return None

    return None


def _send_feishu_notification(event: AlertEvent, rule: AlertRule):
    """发送飞书通知"""
    webhook_url = rule.notify_webhook_url or settings.FEISHU_WEBHOOK_URL
    if not webhook_url:
        return

    color_map = {"info": "blue", "warning": "yellow", "critical": "red"}
    color = color_map.get(event.level, "yellow")
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"🚨 {event.title}"},
                "template": color,
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": event.message}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"级别: **{event.level.upper()}**\n时间: {event.created_at.strftime('%Y-%m-%d %H:%M')}"}},
                {"tag": "hr"},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "优丁建材 · 超级管理员告警中心"}]},
            ],
        },
    }
    try:
        with httpx.Client(timeout=10) as client:
            client.post(webhook_url, json=payload)
    except Exception:
        pass


def seed_default_alert_rules(db: Session):
    """初始化默认告警规则"""
    defaults = [
        ("AI 错误率过高", "ai_error", "ai_error_rate", "gt", 10, 10, 60),
        ("AI 调用量骤降", "ai_error", "ai_call_count", "lt", 5, 15, 30),
    ]
    for name, cat, key, op, threshold, dur, cooldown in defaults:
        exists = db.query(AlertRule).filter(AlertRule.name == name).first()
        if not exists:
            db.add(AlertRule(
                name=name,
                category=cat,
                metric_key=key,
                operator=op,
                threshold=threshold,
                duration_minutes=dur,
                cooldown_minutes=cooldown,
                enabled=True,
                notify_feishu=bool(settings.FEISHU_WEBHOOK_URL),
            ))
    db.commit()
