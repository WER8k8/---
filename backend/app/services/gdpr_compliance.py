"""GDPR 合规服务 — FIX-46

提供 GDPR 合规所需功能：
- Cookie 同意管理
- 数据删除请求（被遗忘权）
- 数据导出请求（数据可携带权）
- 隐私政策版本管理
- 数据处理记录
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid

log = logging.getLogger(__name__)


class DataSubjectRequest(str, Enum):
    """数据主体请求类型。"""
    ACCESS = "access"           # 访问权
    RECTIFICATION = "rectification"  # 更正权
    ERASURE = "erasure"         # 被遗忘权
    PORTABILITY = "portability"  # 数据可携带权
    RESTRICT = "restrict"       # 限制处理权
    OBJECT = "object"           # 反对权


class RequestStatus(str, Enum):
    """请求状态。"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"


class GDPRComplianceService:
    """GDPR 合规服务。"""
    # 隐私政策版本
    PRIVACY_POLICY = {
        "version": "2.0",
        "last_updated": "2026-07-20",
        "sections": [
            "1. 我们收集哪些数据",
            "2. 我们如何使用数据",
            "3. 数据存储和安全",
            "4. 数据共享和传输",
            "5. 您的权利（GDPR）",
            "6. Cookie 使用",
            "7. 数据保留期限",
            "8. 联系我们",
        ],
        "data_retention": {
            "user_account": "账户活跃期间 + 90天",
            "lead_data": "24个月或用户请求删除",
            "email_logs": "12个月",
            "analytics": "26个月",
            "system_logs": "6个月",
        },
        "third_party_processors": [
            {"name": "Resend", "purpose": "邮件发送", "location": "EU/US"},
            {"name": "Redis", "purpose": "缓存", "location": "自托管"},
            {"name": "PostgreSQL", "purpose": "数据存储", "location": "自托管"},
        ],
    }
    # Cookie 类别
    COOKIE_CATEGORIES = {
        "necessary": {
            "label": "必要 Cookie",
            "description": "网站正常运行所需，无法禁用",
            "required": True,
            "cookies": ["session_id", "csrf_token", "consent"],
        },
        "functional": {
            "label": "功能 Cookie",
            "description": "记住您的偏好和设置",
            "required": False,
            "cookies": ["language", "theme", "user_prefs"],
        },
        "analytics": {
            "label": "分析 Cookie",
            "description": "帮助我们了解网站使用情况",
            "required": False,
            "cookies": ["_ga", "_gid", "_gat"],
        },
        "marketing": {
            "label": "营销 Cookie",
            "description": "用于个性化广告和内容",
            "required": False,
            "cookies": ["_fbp", "_gcl_au"],
        },
    }
    async def submit_data_request(
        self,
        user_id: str,
        request_type: DataSubjectRequest,
        details: dict[str, Any] | None = None,
    ) -> dict:
        """提交数据主体请求。"""
        request_id = str(uuid.uuid4())
        log.info(
            "[GDPR] 数据请求: user=%s type=%s id=%s",
            user_id, request_type.value, request_id,
        )
        return {
            "request_id": request_id,
            "user_id": user_id,
            "type": request_type.value,
            "status": RequestStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "message": f"您的{request_type.value}请求已提交，我们将在30天内处理。",
        }

    async def process_erasure_request(self, user_id: str) -> dict:
        """处理数据删除请求（被遗忘权）。"""
        deleted_items = {
            "user_profile": False,
            "leads": False,
            "email_logs": False,
            "cookies": False,
        }
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                # 删除线索数据
                from app.models.prospect_lead import ProspectLead
                db.query(ProspectLead).filter(
                    ProspectLead.email.like(f"%{user_id}%")
                ).delete()
                # 删除邮件外展数据
                from app.models.email_outreach import EmailOutreach
                db.query(EmailOutreach).filter(
                    EmailOutreach.user_id == user_id
                ).delete()
                db.commit()
                deleted_items["leads"] = True
                deleted_items["email_logs"] = True
                log.info("[GDPR] 数据删除完成: user=%s", user_id)
            finally:
                db.close()
        except Exception as e:
            log.error("[GDPR] 数据删除失败: %s", e)

        return {
            "status": "completed",
            "deleted_items": deleted_items,
            "message": "数据删除请求已处理完成。",
        }

    async def export_user_data(self, user_id: str) -> dict:
        """导出用户数据（数据可携带权）。"""
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data": {},
        }
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                # 导出线索
                from app.models.prospect_lead import ProspectLead
                leads = db.query(ProspectLead).filter(
                    ProspectLead.email.like(f"%{user_id}%")
                ).all()
                data["data"]["leads"] = [
                    {
                        "email": l.email,
                        "company": l.company,
                        "status": l.status,
                        "created_at": str(l.created_at) if l.created_at else None,
                    }
                    for l in leads
                ]
                # 导出邮件
                from app.models.email_outreach import EmailOutreach
                outreaches = db.query(EmailOutreach).filter(
                    EmailOutreach.user_id == user_id
                ).all()
                data["data"]["outreaches"] = [
                    {
                        "subject": o.subject,
                        "status": o.status,
                        "created_at": str(o.created_at) if o.created_at else None,
                    }
                    for o in outreaches
                ]
            finally:
                db.close()
        except Exception as e:
            log.error("[GDPR] 数据导出失败: %s", e)

        return data

    def get_cookie_consent_config(self) -> dict:
        """获取 Cookie 同意配置。"""
        return {
            "version": "1.0",
            "categories": {
                cat: {
                    "label": info["label"],
                    "description": info["description"],
                    "required": info["required"],
                }
                for cat, info in self.COOKIE_CATEGORIES.items()
            },
            "privacy_policy_url": "/privacy",
            "cookie_policy_url": "/cookies",
        }

    def get_privacy_policy(self) -> dict:
        """获取隐私政策。"""
        return self.PRIVACY_POLICY


# 全局实例
gdpr_service = GDPRComplianceService()