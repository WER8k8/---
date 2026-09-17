# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DATA_SOURCE 插槽适配器：调用既有线索富化门面。"""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from app.orchestration.interfaces import DataSourceProvider, SlotArchetype
from app.services.ubrain.hunter_service import LeadEnrichmentService


class DataSourceEnrichAdapter(DataSourceProvider):
    """把异步富化服务封装为插槽契约，保留服务自身的真实结果。"""

    archetype = SlotArchetype.DATA_SOURCE

    def __init__(self, service: LeadEnrichmentService | None = None) -> None:
        self._service = service or LeadEnrichmentService()

    def enrich(self, tenant_id: str, subject: Mapping[str, Any]) -> Mapping[str, Any]:
        """调用 enrichment 服务；subject 可携带 email/domain 等真实字段。"""
        if not tenant_id.strip():
            raise ValueError("tenant_id 不能为空")
        if not isinstance(subject, Mapping):
            raise ValueError("subject 必须是映射")

        result = asyncio.run(
            self._service.enrich_lead(
                email=str(subject.get("email") or ""),
                first_name=str(subject.get("first_name") or ""),
                last_name=str(subject.get("last_name") or ""),
                domain=str(subject.get("domain") or ""),
                linkedin_url=str(subject.get("linkedin_url") or ""),
            )
        )
        return dict(result)


__all__ = ["DataSourceEnrichAdapter"]
