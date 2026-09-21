# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""客户流失预警服务"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.tenant import Tenant, TenantPlan, TenantSubscription

_CHURN_CONTACTED_KEY = "churn_contacted_at"


def _aware(dt):
    """将可能 naive 的 datetime 规整为 UTC aware，避免与 now(timezone.utc) 相减报 TypeError。

    tenant.updated_at / expires_at / trial_ends_at 经 DateTime(timezone=True) 列落库后，
    部分记录为 naive（取决于驱动/时区配置），与 tz-aware 的 now 相减会崩。
    已在 P1-3 接线时发现并修复（同时修好既有 /churn/at-risk 接口）。
    """
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


class ChurnService:
    """分析客户流失风险，基于真实租户数据计算预警"""
    # ── 风险因子权重 ──
    WEIGHT_LAST_LOGIN = 0.35       # 最后登录距今时间
    WEIGHT_INQUIRY_STALE = 0.25    # 询盘未回复时长
    WEIGHT_EXPIRY = 0.20           # 套餐到期临近度
    WEIGHT_ACTIVITY_DROP = 0.12    # 活跃度下降
    WEIGHT_USAGE_FALL = 0.08       # 功能用量下降
    RISK_THRESHOLD_HIGH = 70
    RISK_THRESHOLD_MEDIUM = 40
    @staticmethod
    def get_at_risk_tenants(db: Session) -> list[dict[str, Any]]:
        """从数据库获取有流失风险的租户列表，并计算风险分数"""
        now = datetime.now(timezone.utc)
        tenants = db.query(Tenant).filter(
            Tenant.is_active == True,
            Tenant.status.in_(["active", "trial"]),
        ).all()
        results: list[dict[str, Any]] = []
        for t in tenants:
            score, reasons = ChurnService._calculate_risk_score(t, now)
            risk_level = ChurnService._risk_level(score)
            results.append({
                "id": t.id,
                "name": t.name,
                "risk_level": risk_level,
                "risk_score": round(score, 1),
                "reasons": reasons,
                "contact_name": t.contact_name,
                "contact_phone": t.contact_phone,
                "contact_email": t.contact_email,
                "status": t.status,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            })

        results.sort(key=lambda x: x["risk_score"], reverse=True)
        return results

    @staticmethod
    def calculate_risk_score(tenant_id: str, db: Session) -> dict[str, Any]:
        """单独计算指定租户的风险分数"""
        now = datetime.now(timezone.utc)
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"error": "Tenant not found", "risk_score": 0, "reasons": []}

        score, reasons = ChurnService._calculate_risk_score(tenant, now)
        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "risk_score": round(score, 1),
            "risk_level": ChurnService._risk_level(score),
            "reasons": reasons,
        }

    @staticmethod
    def _calculate_risk_score(tenant: Tenant, now: datetime) -> tuple[float, list[str]]:
        """核心风险计算引擎"""
        score = 0.0
        reasons: list[str] = []
        # 1. 最后活跃时间（用 updated_at 近似 login）
        if tenant.updated_at:
            days_inactive = (now - _aware(tenant.updated_at)).days
            if days_inactive >= 15:
                score += ChurnService.WEIGHT_LAST_LOGIN * 100
                reasons.append(f"{days_inactive}天未登录")
            elif days_inactive >= 7:
                score += ChurnService.WEIGHT_LAST_LOGIN * 60
                reasons.append(f"{days_inactive}天未登录")
            elif days_inactive >= 3:
                score += ChurnService.WEIGHT_LAST_LOGIN * 25
                reasons.append(f"{days_inactive}天未登录")

        # 2. 套餐到期临近度
        if tenant.expires_at:
            days_to_expiry = (_aware(tenant.expires_at) - now).days
            if days_to_expiry <= 0:
                score += ChurnService.WEIGHT_EXPIRY * 100
                reasons.append("套餐已到期")
            elif days_to_expiry <= 7:
                score += ChurnService.WEIGHT_EXPIRY * 80
                reasons.append(f"套餐{days_to_expiry}天后到期")
            elif days_to_expiry <= 30:
                score += ChurnService.WEIGHT_EXPIRY * 40
                reasons.append(f"套餐{days_to_expiry}天后到期")

        # 3. 试用到期判断
        if tenant.status == "trial" and tenant.trial_ends_at:
            trial_left = (_aware(tenant.trial_ends_at) - now).days
            if trial_left <= 3:
                score += ChurnService.WEIGHT_EXPIRY * 60
                reasons.append(f"试用期仅剩{trial_left}天")

        # 4. AI配额使用率（过低说明没在用）
        if hasattr(tenant, "ai_quota_used") and tenant.ai_quota_used is not None:
            plan = tenant.plan
            if plan and plan.max_ai_quota > 0:
                usage_rate = tenant.ai_quota_used / plan.max_ai_quota
                if usage_rate < 0.1:
                    score += ChurnService.WEIGHT_USAGE_FALL * 50
                    reasons.append("AI功能几乎未使用")

        return min(score, 100.0), reasons if reasons else ["运行正常，暂无明显风险"]

    @staticmethod
    def _risk_level(score: float) -> str:
        """_risk_level。

        参数说明：
        :param score: 参数 score
        :return: 返回处理结果。
        """
        if score >= ChurnService.RISK_THRESHOLD_HIGH:
            return "high"
        elif score >= ChurnService.RISK_THRESHOLD_MEDIUM:
            return "medium"
        return "low"

    @staticmethod
    def get_retention_tips(db: Session) -> list[dict[str, Any]]:
        """基于实际风险数据生成挽留建议"""
        at_risk = ChurnService.get_at_risk_tenants(db)
        tips: list[dict[str, Any]] = []
        tip_templates = {
            "15天未登录": ("电话回访，了解使用情况与痛点", "high"),
            "天未登录": ("发送关怀邮件，附平台新功能亮点", "medium"),
            "套餐已到期": ("立即电话联系，提供续费优惠方案", "high"),
            "天后到期": ("提醒续费，推荐年度套餐享优惠", "medium"),
            "试用期仅剩": ("引导转正式套餐，提供专属折扣", "high"),
            "AI功能几乎未使用": ("安排一对一功能培训或演示", "medium"),
        }
        for item in at_risk:
            if item["risk_level"] == "low":
                continue
            for reason in item["reasons"]:
                matched = False
                for keyword, (action, priority) in tip_templates.items():
                    if keyword in reason:
                        tips.append({
                            "tenant_id": item["id"],
                            "tenant_name": item["name"],
                            "risk_level": item["risk_level"],
                            "reason": reason,
                            "action": action,
                            "priority": priority,
                        })
                        matched = True
                        break
                if not matched:
                    tips.append({
                        "tenant_id": item["id"],
                        "tenant_name": item["name"],
                        "risk_level": item["risk_level"],
                        "reason": reason,
                        "action": "定期回访，保持客户关系",
                        "priority": "medium",
                    })

        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        tips.sort(key=lambda x: (x["tenant_id"], priority_order.get(x["priority"], 99)))
        return tips

    @staticmethod
    def _load_settings(tenant: Tenant) -> dict[str, Any]:
        """_load_settings。

        参数说明：
        :param tenant: 参数 tenant
        :return: 返回处理结果。
        """
        if not tenant.settings:
            return {}
        try:
            data = json.loads(tenant.settings)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _save_settings(tenant: Tenant, settings: dict[str, Any]) -> None:
        """_save_settings。

        参数说明：
        :param tenant: 参数 tenant
        :param settings: 参数 settings
        :return: 返回处理结果。
        """
        tenant.settings = json.dumps(settings, ensure_ascii=False)

    @staticmethod
    def get_contacted_list(db: Session) -> list[str]:
        """已联系租户 ID 列表（持久化在 tenant.settings）。"""
        ids: list[str] = []
        for t in db.query(Tenant.id, Tenant.settings).filter(Tenant.is_active.is_(True)).all():
            tid, raw = t[0], t[1]
            if not raw:
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get(_CHURN_CONTACTED_KEY):
                    ids.append(str(tid))
            except (json.JSONDecodeError, TypeError):
                continue
        return ids

    @staticmethod
    def mark_contacted(db: Session, tenant_id: str) -> dict[str, Any]:
        """标记租户为已联系"""
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"success": False, "message": "租户不存在"}
        settings = ChurnService._load_settings(tenant)
        now_iso = datetime.now(timezone.utc).isoformat()
        settings[_CHURN_CONTACTED_KEY] = now_iso
        ChurnService._save_settings(tenant, settings)
        tenant.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "tenant_id": tenant_id,
            "contacted": True,
            "contacted_at": now_iso,
            "message": f"租户 {tenant_id} 已标记为已联系",
        }

    @staticmethod
    def get_churn_trend(db: Session) -> list[dict[str, Any]]:
        """近12个月流失趋势"""
        now = datetime.now(timezone.utc)
        trend = []
        for i in range(12):
            month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            lost_count = db.query(Tenant).filter(
                Tenant.status == "cancelled",
                Tenant.updated_at >= month_start,
                Tenant.updated_at < (month_start.replace(day=28) + timedelta(days=5)).replace(day=1),
            ).count()
            trend.append({
                "month": month_start.strftime("%Y-%m"),
                "lost": lost_count,
            })
        return list(reversed(trend))
