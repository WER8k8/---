# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""询盘入口聚合 — 统一说明 v1 / v2 / unified 路径。"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry


class InquiriesPortalService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def portal_meta(self) -> dict:
        """portal_meta。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        total = self.db.query(func.count(Inquiry.id)).scalar() or 0
        pending = (
            self.db.query(func.count(Inquiry.id))
            .filter(Inquiry.status == "pending")
            .scalar()
            or 0
        )
        return {
            "total_inquiries": int(total),
            "pending_count": int(pending),
            "canonical_list": "/api/v1/inquiries/unified",
            "apis": {
                "unified_list": {
                    "method": "GET",
                    "path": "/api/v1/inquiries/unified",
                    "description": "管理端主入口：统一询盘分页（推荐）",
                    "canonical": True,
                },
                "legacy_list": {
                    "method": "GET",
                    "path": "/api/v1/inquiries/",
                    "description": "兼容旧前端，行为同 unified",
                    "deprecated": True,
                    "use_instead": "/api/v1/inquiries/unified",
                },
                "v2": {
                    "method": "GET",
                    "path": "/api/v1/inquiries-v2/",
                    "description": "外贸 B2B 按 buyer/merchant 的 CRUD（非管理端列表）",
                    "scope": "b2b_crud_only",
                },
            },
            "migration_note": "新功能只对接 /inquiries/unified；/inquiries-v2 仅保留 B2B CRUD，勿新增第四条入口",
            "adr": "docs/adr/inquiries-api-canonical.md",
        }
