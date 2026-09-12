"""高级安全 API — FIX-13 国密算法 + FIX-14 零信任架构

- 国密 SM3/SM4 加密/哈希/HMAC
- 零信任访问决策
- 设备信任管理
- 风险评分
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response
from app.services.ubrain.gmssl_crypto_service import gmssl_crypto_service
from app.services.ubrain.zero_trust_service import (
    zero_trust_engine,
    DeviceContext,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""
ROUTE_TAGS = ["高级安全"]

router = APIRouter(prefix="/security-advanced", tags=["高级安全"])


# ═══════════════════════════════════════════════════════════
# FIX-13: 国密算法
# ═══════════════════════════════════════════════════════════

@router.post("/gmssl/encrypt")
def gmssl_encrypt(
    plaintext: str = Body(..., description="明文"),
    key_id: str = Body("default", description="密钥标识"),
    current_user=Depends(get_current_user),
):
    """SM4-CBC 加密。"""
    if not gmssl_crypto_service.is_configured():
        return success_response(data={"error": "国密服务未配置，请设置 GMSSL_MASTER_KEY 环境变量"})
    result = gmssl_crypto_service.encrypt_sm4(plaintext, key_id=key_id)
    return success_response(data={
        "ciphertext": result.ciphertext,
        "algorithm": result.algorithm,
        "success": result.success,
        "error": result.error,
    })


@router.post("/gmssl/decrypt")
def gmssl_decrypt(
    ciphertext: str = Body(..., description="密文"),
    key_id: str = Body("default", description="密钥标识"),
    current_user=Depends(get_current_user),
):
    """SM4-CBC 解密。"""
    if not gmssl_crypto_service.is_configured():
        return success_response(data={"error": "国密服务未配置"})
    result = gmssl_crypto_service.decrypt_sm4(ciphertext, key_id=key_id)
    return success_response(data={
        "plaintext": result.plaintext,
        "algorithm": result.algorithm,
        "success": result.success,
        "error": result.error,
    })


@router.post("/gmssl/hash")
def gmssl_hash(
    data: str = Body(..., description="待哈希数据"),
    current_user=Depends(get_current_user),
):
    """SM3 哈希。"""
    result = gmssl_crypto_service.hash_sm3(data)
    return success_response(data={
        "hash": result.hash_value,
        "algorithm": result.algorithm,
        "success": result.success,
    })


@router.post("/gmssl/hmac")
def gmssl_hmac(
    data: str = Body(..., description="待认证数据"),
    key_id: str = Body("default", description="密钥标识"),
    current_user=Depends(get_current_user),
):
    """HMAC-SM3 消息认证码。"""
    result = gmssl_crypto_service.hmac_sm3(data, key_id=key_id)
    return success_response(data={
        "mac": result.hash_value,
        "algorithm": result.algorithm,
        "success": result.success,
    })


@router.post("/gmssl/encrypt-record")
def gmssl_encrypt_record(
    record: dict[str, Any] = Body(..., description="待加密记录"),
    sensitive_fields: list[str] = Body(None, description="敏感字段列表"),
    current_user=Depends(get_current_user),
):
    """国密加密记录中的敏感字段。"""
    if not gmssl_crypto_service.is_configured():
        return success_response(data={"error": "国密服务未配置"})
    encrypted = gmssl_crypto_service.encrypt_record(record, sensitive_fields)
    return success_response(data={"encrypted": encrypted})


@router.get("/gmssl/status")
def gmssl_status(current_user=Depends(get_current_user)):
    """国密服务状态。"""
    return success_response(data={
        "configured": gmssl_crypto_service.is_configured(),
        "algorithms": ["SM3", "SM4-CBC", "HMAC-SM3"],
    })


# ═══════════════════════════════════════════════════════════
# FIX-14: 零信任架构
# ═══════════════════════════════════════════════════════════

@router.post("/zero-trust/decide")
def zero_trust_decide(
    user_id: str = Body(..., description="用户ID"),
    resource: str = Body(..., description="请求资源路径"),
    action: str = Body("read", description="操作类型"),
    device_id: str = Body(..., description="设备ID"),
    device_fingerprint: str = Body(..., description="设备指纹"),
    ip_address: str = Body(..., description="IP地址"),
    mfa_verified: bool = Body(False, description="是否已MFA验证"),
    session_age_minutes: int = Body(0, description="会话年龄（分钟）"),
    anomaly_score: float = Body(0.0, description="异常评分 0-1"),
    current_user=Depends(get_current_user),
):
    """零信任访问决策。"""
    device = DeviceContext(
        device_id=device_id,
        fingerprint=device_fingerprint,
        ip_address=ip_address,
        is_known_device=device_id in zero_trust_engine._known_devices,
    )
    from app.services.ubrain.zero_trust_service import AccessContext
    ctx = AccessContext(
        user_id=user_id,
        device=device,
        resource=resource,
        action=action,
        mfa_verified=mfa_verified,
        session_age_minutes=session_age_minutes,
        anomaly_score=anomaly_score,
    )
    decision = zero_trust_engine.make_decision(ctx)
    return success_response(data={
        "allowed": decision.allowed,
        "trust_level": decision.trust_level.value,
        "risk_level": decision.risk_level.value,
        "reason": decision.reason,
        "required_actions": decision.required_actions,
        "expires_at": decision.expires_at,
    })


@router.post("/zero-trust/device/register")
def register_device(
    user_id: str = Body(..., description="用户ID"),
    device_id: str = Body(..., description="设备ID"),
    fingerprint: str = Body(..., description="设备指纹"),
    current_user=Depends(get_current_user),
):
    """注册已知设备。"""
    device = DeviceContext(
        device_id=device_id,
        fingerprint=fingerprint,
        is_known_device=True,
    )
    zero_trust_engine.register_device(user_id, device)
    return success_response(data={"registered": True, "device_id": device_id})


@router.get("/zero-trust/devices/{user_id}")
def get_user_devices(
    user_id: str,
    current_user=Depends(get_current_user),
):
    """获取用户设备信任报告。"""
    report = zero_trust_engine.get_device_trust_report(user_id)
    return success_response(data=report)


@router.post("/zero-trust/ip/block")
def block_ip(
    ip: str = Body(..., description="要阻断的IP"),
    current_user=Depends(get_current_user),
):
    """阻断 IP。"""
    zero_trust_engine.block_ip(ip)
    return success_response(data={"blocked": ip})


@router.post("/zero-trust/ip/unblock")
def unblock_ip(
    ip: str = Body(..., description="要解除阻断的IP"),
    current_user=Depends(get_current_user),
):
    """解除 IP 阻断。"""
    zero_trust_engine.unblock_ip(ip)
    return success_response(data={"unblocked": ip})


@router.post("/zero-trust/risk/update")
def update_risk_score(
    user_id: str = Body(..., description="用户ID"),
    delta: float = Body(..., description="风险分变化量"),
    current_user=Depends(get_current_user),
):
    """更新用户风险评分。"""
    new_score = zero_trust_engine.update_risk_score(user_id, delta)
    return success_response(data={"user_id": user_id, "risk_score": new_score})


@router.get("/zero-trust/status")
def zero_trust_status(current_user=Depends(get_current_user)):
    """零信任引擎状态。"""
    return success_response(data={
        "known_devices": len(zero_trust_engine._known_devices),
        "blocked_ips": len(zero_trust_engine._blocked_ips),
        "tracked_users": len(zero_trust_engine._login_history),
        "risk_profiles": len(zero_trust_engine._risk_scores),
    })