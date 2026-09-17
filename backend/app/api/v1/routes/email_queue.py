# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""邮件发送队列 + 数据飞轮 + 加密审计 + AI 安全 API — FIX-62 ~ FIX-65

FIX-62: 邮件发送队列（高吞吐 + 高送达率）
FIX-63: 数据飞轮（越用越聪明的获客系统）
FIX-64: 敏感字段加密审计
FIX-65: AI 安全（LLM 输入/输出安全）
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response
from app.services.ubrain.email_queue_service import (
    email_send_queue,
    data_flywheel_engine,
    field_encryption_service,
    ai_security_guard,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["邮件队列&安全"]

router = APIRouter(prefix="/email-queue", tags=["邮件队列&安全"])


# ═══════════════════════════════════════════════════════════
# FIX-62: 邮件发送队列
# ═══════════════════════════════════════════════════════════

@router.post("/enqueue")
async def enqueue_email(
    to_email: str = Body(..., description="收件人邮箱"),
    subject: str = Body(..., description="邮件主题"),
    body: str = Body(..., description="邮件正文"),
    to_name: str = Body("", description="收件人姓名"),
    priority: int = Body(0, ge=0, le=10, description="优先级 0-10"),
    campaign_id: str = Body("", description="营销活动ID"),
    scheduled_at: str = Body("", description="计划发送时间 ISO格式"),
    current_user=Depends(get_current_user),
):
    """单封邮件入队。"""
    item = await email_send_queue.enqueue(
        to_email=to_email,
        subject=subject,
        body=body,
        to_name=to_name,
        priority=priority,
        campaign_id=campaign_id,
        scheduled_at=scheduled_at,
    )
    return success_response(data=item.to_dict())


@router.post("/enqueue/batch")
async def enqueue_batch(
    recipients: list[dict] = Body(..., description="收件人列表 [{email, name, ...}]"),
    subject_template: str = Body(..., description="主题模板，支持 {变量名}"),
    body_template: str = Body(..., description="正文模板，支持 {变量名}"),
    campaign_id: str = Body("", description="营销活动ID"),
    priority: int = Body(0, ge=0, le=10, description="优先级"),
    current_user=Depends(get_current_user),
):
    """批量邮件入队。"""
    items = await email_send_queue.enqueue_batch(
        recipients=recipients,
        subject_template=subject_template,
        body_template=body_template,
        campaign_id=campaign_id,
        priority=priority,
    )
    return success_response(data={
        "enqueued": len(items),
        "items": [i.to_dict() for i in items],
    })


@router.post("/dequeue")
async def dequeue_and_send(
    batch_size: int = Body(50, ge=1, le=200, description="批量大小"),
    current_user=Depends(get_current_user),
):
    """出队并发送一批邮件。"""
    results = await email_send_queue.dequeue_batch(batch_size=batch_size)
    return success_response(data={
        "processed": len(results),
        "results": results,
    })


@router.get("/stats")
async def queue_stats(current_user=Depends(get_current_user)):
    """获取队列统计信息。"""
    stats = await email_send_queue.get_stats()
    return success_response(data=stats)


@router.post("/clear")
async def clear_completed(current_user=Depends(get_current_user)):
    """清理已完成（已发送/已失败）的队列项。"""
    removed = await email_send_queue.clear_completed()
    return success_response(data={"removed": removed})


@router.post("/domain-limits")
async def set_domain_limits(
    limits: dict[str, int] = Body(..., description="域名限速配置 {domain: hourly_limit}"),
    current_user=Depends(get_current_user),
):
    """设置域名速率限制。"""
    email_send_queue.set_domain_limits(limits)
    return success_response(data={"limits": email_send_queue._domain_limits})


@router.get("/domain-limits")
async def get_domain_limits(current_user=Depends(get_current_user)):
    """获取当前域名速率限制。"""
    return success_response(data={
        "limits": email_send_queue._domain_limits or email_send_queue.DEFAULT_DOMAIN_LIMITS,
        "rates": await email_send_queue.get_stats()["domain_rates"],
    })


# ═══════════════════════════════════════════════════════════
# FIX-63: 数据飞轮
# ═══════════════════════════════════════════════════════════

@router.post("/flywheel/learn")
def flywheel_learn(
    interaction_type: str = Body(..., description="交互类型: open/click/reply/bounce/unsubscribe"),
    email_data: dict[str, Any] = Body(..., description="邮件数据 {subject, body, template, time, day_of_week}"),
    lead_data: dict[str, Any] = Body(..., description="线索数据 {industry, role, country, company_size}"),
    current_user=Depends(get_current_user),
):
    """记录交互数据到飞轮（从交互中学习）。"""
    data_flywheel_engine.learn_from_interaction(
        interaction_type=interaction_type,
        email_data=email_data,
        lead_data=lead_data,
    )
    return success_response(data={
        "stage": data_flywheel_engine.get_stage(),
        "patterns_count": len(data_flywheel_engine._patterns),
    })


@router.get("/flywheel/insights")
def flywheel_insights(current_user=Depends(get_current_user)):
    """分析模式生成洞察。"""
    insights = data_flywheel_engine.analyze_patterns()
    return success_response(data={
        "stage": data_flywheel_engine.get_stage(),
        "insights": [i.to_dict() for i in insights],
    })


@router.get("/flywheel/suggestions")
def flywheel_suggestions(current_user=Depends(get_current_user)):
    """获取优化建议。"""
    suggestions = data_flywheel_engine.get_optimization_suggestions()
    return success_response(data={
        "stage": data_flywheel_engine.get_stage(),
        "suggestions": suggestions,
    })


@router.get("/flywheel/stage")
def flywheel_stage(current_user=Depends(get_current_user)):
    """获取飞轮当前阶段。"""
    return success_response(data={
        "stage": data_flywheel_engine.get_stage(),
        "patterns_count": len(data_flywheel_engine._patterns),
        "insights_count": len(data_flywheel_engine._insights),
    })


@router.post("/flywheel/reset")
def flywheel_reset(current_user=Depends(get_current_user)):
    """重置飞轮数据。"""
    data_flywheel_engine.reset()
    return success_response(data={"stage": data_flywheel_engine.get_stage()})


# ═══════════════════════════════════════════════════════════
# FIX-64: 敏感字段加密审计
# ═══════════════════════════════════════════════════════════

@router.post("/encrypt/encrypt")
def encrypt_field(
    plaintext: str = Body(..., description="明文"),
    current_user=Depends(get_current_user),
):
    """加密敏感字段。"""
    if not field_encryption_service.is_configured():
        return success_response(data={"error": "加密服务未配置，请设置 ENCRYPTION_SECRET_KEY 环境变量"})
    ciphertext = field_encryption_service.encrypt(plaintext)
    return success_response(data={"encrypted": ciphertext})


@router.post("/encrypt/decrypt")
def decrypt_field(
    ciphertext: str = Body(..., description="密文"),
    current_user=Depends(get_current_user),
):
    """解密敏感字段。"""
    if not field_encryption_service.is_configured():
        return success_response(data={"error": "加密服务未配置"})
    plaintext = field_encryption_service.decrypt(ciphertext)
    return success_response(data={"decrypted": plaintext})


@router.post("/encrypt/audit")
def audit_data(
    data: dict[str, Any] = Body(..., description="待审计数据"),
    current_user=Depends(get_current_user),
):
    """审计数据中的敏感字段。"""
    result = field_encryption_service.audit_data(data)
    return success_response(data=result)


@router.post("/encrypt/record")
def encrypt_record(
    record: dict[str, Any] = Body(..., description="待加密记录"),
    current_user=Depends(get_current_user),
):
    """加密记录中的所有敏感字段。"""
    if not field_encryption_service.is_configured():
        return success_response(data={"error": "加密服务未配置"})
    encrypted = field_encryption_service.encrypt_record(record)
    return success_response(data={"encrypted": encrypted})


@router.post("/encrypt/decrypt-record")
def decrypt_record(
    record: dict[str, Any] = Body(..., description="待解密记录"),
    current_user=Depends(get_current_user),
):
    """解密记录中的所有敏感字段。"""
    if not field_encryption_service.is_configured():
        return success_response(data={"error": "加密服务未配置"})
    decrypted = field_encryption_service.decrypt_record(record)
    return success_response(data={"decrypted": decrypted})


@router.get("/encrypt/status")
def encryption_status(current_user=Depends(get_current_user)):
    """获取加密服务状态。"""
    return success_response(data={
        "configured": field_encryption_service.is_configured(),
        "sensitive_fields": field_encryption_service.SENSITIVE_FIELDS,
    })


# ═══════════════════════════════════════════════════════════
# FIX-65: AI 安全
# ═══════════════════════════════════════════════════════════

@router.post("/ai-security/scan-input")
def scan_ai_input(
    text: str = Body(..., description="AI 输入文本"),
    current_user=Depends(get_current_user),
):
    """扫描 AI 输入文本（检测注入攻击、PII 泄露、越狱尝试）。"""
    result = ai_security_guard.scan_input(text)
    return success_response(data=result.to_dict())


@router.post("/ai-security/scan-output")
def scan_ai_output(
    text: str = Body(..., description="AI 输出文本"),
    current_user=Depends(get_current_user),
):
    """扫描 AI 输出文本（检测有害内容、幻觉标记、PII 泄露）。"""
    result = ai_security_guard.scan_output(text)
    return success_response(data=result.to_dict())


@router.post("/ai-security/audit-log")
def ai_audit_log(
    user_id: str = Body(..., description="用户ID"),
    model: str = Body(..., description="AI 模型名称"),
    input_text: str = Body(..., description="输入文本"),
    output_text: str = Body(..., description="输出文本"),
    current_user=Depends(get_current_user),
):
    """生成 AI 交互审计日志条目。"""
    input_scan = ai_security_guard.scan_input(input_text)
    output_scan = ai_security_guard.scan_output(output_text)
    log_entry = ai_security_guard.audit_log_entry(
        user_id=user_id,
        model=model,
        input_text=input_text,
        output_text=output_text,
        input_scan=input_scan,
        output_scan=output_scan,
    )
    return success_response(data=log_entry)


@router.post("/ai-security/sanitize")
def sanitize_text(
    text: str = Body(..., description="待净化文本"),
    current_user=Depends(get_current_user),
):
    """净化文本（移除 PII 等敏感信息）。"""
    sanitized = ai_security_guard._sanitize_text(text)
    return success_response(data={"original_length": len(text), "sanitized_length": len(sanitized), "sanitized": sanitized})