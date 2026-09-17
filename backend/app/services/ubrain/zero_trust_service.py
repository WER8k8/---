# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""零信任安全架构服务 — FIX-14

核心原则：
1. 永不信任，始终验证（Never Trust, Always Verify）
2. 最小权限访问（Least Privilege Access）
3. 假设已 breached（Assume Breach）
4. 显式验证（Verify Explicitly）

实现层：
- 设备信任评估
- 持续身份验证
- 上下文感知访问控制
- 微分段策略
- 实时风险评分
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TrustLevel(str, Enum):
    FULL = "full"          # 完全信任
    PARTIAL = "partial"    # 部分信任（限制访问）
    UNTRUSTED = "untrusted"  # 不信任（拒绝/需 MFA）
    BLOCKED = "blocked"    # 已阻断


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DeviceContext:
    """设备上下文"""
    device_id: str
    fingerprint: str
    os: str = ""
    browser: str = ""
    ip_address: str = ""
    geo_location: str = ""
    is_known_device: bool = False
    last_seen: str = ""


@dataclass
class AccessContext:
    """访问上下文"""
    user_id: str
    device: DeviceContext
    resource: str
    action: str
    timestamp: str = ""
    mfa_verified: bool = False
    session_age_minutes: int = 0
    anomaly_score: float = 0.0


@dataclass
class TrustDecision:
    """信任决策"""
    allowed: bool
    trust_level: TrustLevel
    risk_level: RiskLevel
    reason: str
    required_actions: list[str] = field(default_factory=list)
    expires_at: str = ""


class ZeroTrustEngine:
    """零信任决策引擎。

    实时评估每次访问请求的信任等级，动态决定是否放行。
    """
    # 高风险国家/地区
    HIGH_RISK_REGIONS = {"XX"}  # 占位，实际配置从数据库/配置中心读取
    # 异常行为阈值
    ANOMALY_THRESHOLDS = {
        "rapid_login": 5,        # 5 分钟内超过 5 次登录
        "geo_jump": 3000,        # 两次登录距离超过 3000km
        "off_hours": True,       # 非工作时间访问
    }
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._known_devices: dict[str, dict] = {}   # device_id -> {user_id, fingerprint, last_seen}
        self._login_history: dict[str, list[dict]] = {}  # user_id -> [{ip, time, geo}]
        self._blocked_ips: set[str] = set()
        self._risk_scores: dict[str, float] = {}    # user_id -> 累积风险分

    def evaluate_device_trust(self, device: DeviceContext) -> TrustLevel:
        """评估设备信任等级。"""
        if device.ip_address in self._blocked_ips:
            return TrustLevel.BLOCKED

        known = self._known_devices.get(device.device_id)
        if known:
            # 已知设备，验证指纹
            if known.get("fingerprint") == device.fingerprint:
                return TrustLevel.FULL
            else:
                # 指纹变化（可能是浏览器更新或设备替换）
                return TrustLevel.PARTIAL

        # 新设备
        return TrustLevel.UNTRUSTED

    def evaluate_access_risk(self, ctx: AccessContext) -> RiskLevel:
        """评估访问风险等级。"""
        risk_score = 0.0
        reasons = []
        # 1. 设备信任
        device_trust = self.evaluate_device_trust(ctx.device)
        if device_trust == TrustLevel.BLOCKED:
            return RiskLevel.CRITICAL
        if device_trust == TrustLevel.UNTRUSTED:
            risk_score += 0.3
            reasons.append("new_device")
        if device_trust == TrustLevel.PARTIAL:
            risk_score += 0.15
            reasons.append("device_fingerprint_changed")

        # 2. 会话年龄
        if ctx.session_age_minutes > 480:  # 8 小时
            risk_score += 0.2
            reasons.append("long_session")

        # 3. MFA 状态
        if not ctx.mfa_verified:
            risk_score += 0.1
            reasons.append("no_mfa")

        # 4. 异常行为评分
        risk_score += min(0.3, ctx.anomaly_score)
        if ctx.anomaly_score > 0.5:
            reasons.append("high_anomaly_score")

        # 5. 历史风险累积
        user_risk = self._risk_scores.get(ctx.user_id, 0)
        risk_score += min(0.2, user_risk)
        # 判定等级
        if risk_score >= 0.7:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def make_decision(self, ctx: AccessContext) -> TrustDecision:
        """做出访问决策。"""
        risk = self.evaluate_access_risk(ctx)
        device_trust = self.evaluate_device_trust(ctx.device)
        required_actions: list[str] = []
        allowed = True
        reason = ""
        trust_level = TrustLevel.FULL
        if risk == RiskLevel.CRITICAL or device_trust == TrustLevel.BLOCKED:
            allowed = False
            trust_level = TrustLevel.BLOCKED
            reason = "Critical risk detected"
            required_actions = ["block", "alert_security_team"]

        elif risk == RiskLevel.HIGH:
            trust_level = TrustLevel.PARTIAL
            reason = "High risk access"
            required_actions = ["require_mfa", "step_up_auth", "log_audit"]
            # 敏感资源需要额外验证
            if self._is_sensitive_resource(ctx.resource):
                allowed = False
                required_actions.append("admin_approval")

        elif risk == RiskLevel.MEDIUM:
            trust_level = TrustLevel.PARTIAL
            reason = "Medium risk access"
            required_actions = ["require_mfa", "log_audit"]

        else:
            # LOW risk
            if device_trust == TrustLevel.UNTRUSTED:
                trust_level = TrustLevel.PARTIAL
                reason = "Low risk but new device"
                required_actions = ["device_registration", "log_audit"]
            else:
                trust_level = TrustLevel.FULL
                reason = "Normal access"
                required_actions = ["log_audit"]

        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        return TrustDecision(
            allowed=allowed,
            trust_level=trust_level,
            risk_level=risk,
            reason=reason,
            required_actions=required_actions,
            expires_at=expires_at,
        )

    def _is_sensitive_resource(self, resource: str) -> bool:
        """判断是否为敏感资源。"""
        sensitive_prefixes = [
            "/admin", "/super-admin", "/finance",
            "/api/v1/payment", "/api/v1/token-ledger",
            "/api/v1/email-queue/encrypt",
        ]
        return any(resource.startswith(p) for p in sensitive_prefixes)

    def register_device(self, user_id: str, device: DeviceContext) -> None:
        """注册已知设备。"""
        self._known_devices[device.device_id] = {
            "user_id": user_id,
            "fingerprint": device.fingerprint,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }

    def record_login(self, user_id: str, ip: str, geo: str = "") -> None:
        """记录登录历史。"""
        if user_id not in self._login_history:
            self._login_history[user_id] = []

        self._login_history[user_id].append({
            "ip": ip,
            "time": datetime.now(timezone.utc).isoformat(),
            "geo": geo,
        })
        # 保留最近 50 条
        self._login_history[user_id] = self._login_history[user_id][-50:]

    def block_ip(self, ip: str) -> None:
        """阻断 IP。"""
        self._blocked_ips.add(ip)

    def unblock_ip(self, ip: str) -> None:
        """解除 IP 阻断。"""
        self._blocked_ips.discard(ip)

    def update_risk_score(self, user_id: str, delta: float) -> float:
        """更新用户风险评分。"""
        current = self._risk_scores.get(user_id, 0)
        new_score = max(0, min(1.0, current + delta))
        self._risk_scores[user_id] = new_score
        return new_score

    def get_device_trust_report(self, user_id: str) -> dict[str, Any]:
        """获取用户设备信任报告。"""
        devices = [
            {"device_id": d_id, **info}
            for d_id, info in self._known_devices.items()
            if info.get("user_id") == user_id
        ]
        return {
            "user_id": user_id,
            "total_devices": len(devices),
            "devices": devices,
        }


class ZeroTrustMiddleware:
    """零信任中间件。

    在请求处理前执行零信任检查。
    """
    def __init__(self, engine: ZeroTrustEngine | None = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param engine: 参数 engine
        :return: 返回处理结果。
        """
        self.engine = engine or ZeroTrustEngine()

    async def check_request(
        self,
        user_id: str,
        resource: str,
        action: str,
        device_id: str,
        device_fingerprint: str,
        ip_address: str,
        mfa_verified: bool = False,
        session_age_minutes: int = 0,
    ) -> TrustDecision:
        """检查请求。"""
        device = DeviceContext(
            device_id=device_id,
            fingerprint=device_fingerprint,
            ip_address=ip_address,
            is_known_device=device_id in self.engine._known_devices,
        )
        ctx = AccessContext(
            user_id=user_id,
            device=device,
            resource=resource,
            action=action,
            timestamp=datetime.now(timezone.utc).isoformat(),
            mfa_verified=mfa_verified,
            session_age_minutes=session_age_minutes,
        )
        return self.engine.make_decision(ctx)


# 单例
zero_trust_engine = ZeroTrustEngine()
zero_trust_middleware = ZeroTrustMiddleware(zero_trust_engine)