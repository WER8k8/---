# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""线索富化服务 — 从多源获取线索详细信息。

数据源：
  - Hunter.io：邮箱验证
  - LinkedIn（通过 RapidAPI 或类似代理）：公司信息

铁律：
  - 无 API key 时返回原始数据 + enrichment_status="skipped"，绝不假成功
  - 不硬编码任何密钥，全部从环境变量读取
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


def _hunter_key() -> str:
    return os.environ.get("HUNTER_IO_API_KEY", "").strip()


def _linkedin_key() -> str:
    return os.environ.get("LINKEDIN_API_KEY", "").strip()


class LeadEnrichmentService:
    """线索富化：从多源获取线索详细信息。"""

    async def _verify_email(self, email: str) -> dict[str, Any]:
        """调用 Hunter.io 验证邮箱。"""
        key = _hunter_key()
        if not key:
            return {"status": "skipped", "reason": "HUNTER_IO_API_KEY 未配置"}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/email-verifier",
                    params={"email": email, "api_key": key},
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                return {
                    "status": "verified",
                    "result": data.get("result", "unknown"),
                    "score": data.get("score"),
                    "regexp": data.get("regexp", False),
                    "gibberish": data.get("gibberish", False),
                    "disposable": data.get("disposable", False),
                    "webmail": data.get("webmail", False),
                }
        except Exception as exc:
            logger.warning("Hunter.io 验证失败: %s", exc)
            return {"status": "error", "reason": str(exc)}

    async def _get_company_info(self, domain: str) -> dict[str, Any]:
        """通过 LinkedIn API 获取公司信息。"""
        key = _linkedin_key()
        if not key:
            return {"status": "skipped", "reason": "LINKEDIN_API_KEY 未配置"}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    "https://linkedin-company-information.p.rapidapi.com/company/search",
                    params={"domain": domain},
                    headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": "linkedin-company-information.p.rapidapi.com"},
                )
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else data.get("items", [])
                if not items:
                    return {"status": "not_found"}
                first = items[0]
                return {
                    "status": "found",
                    "name": first.get("name"),
                    "industry": first.get("industry"),
                    "size": first.get("staffCountRange"),
                    "description": (first.get("description") or "")[:500],
                    "website": first.get("website"),
                    "headquarters": first.get("headquarters"),
                }
        except Exception as exc:
            logger.warning("LinkedIn 查询失败: %s", exc)
            return {"status": "error", "reason": str(exc)}

    async def enrich(self, lead: dict) -> dict:
        """富化单条线索。

        lead 必填: email
        lead 可选: company_domain, company_name
        无 API key 时返回原始数据 + enrichment_status="skipped"。
        """
        email = (lead.get("email") or "").strip()
        if not email:
            return {**lead, "enrichment_status": "failed", "enrichment_error": "email 为空"}

        has_hunter = bool(_hunter_key())
        has_linkedin = bool(_linkedin_key())

        if not has_hunter and not has_linkedin:
            return {**lead, "enrichment_status": "skipped", "enrichment_error": "无任何数据源 API key"}

        result = dict(lead)
        sources_used = []

        if has_hunter:
            email_result = await self._verify_email(email)
            result["email_verification"] = email_result
            if email_result.get("status") == "verified":
                sources_used.append("hunter_io")

        if has_linkedin:
            domain = (lead.get("company_domain") or "").strip()
            if not domain and "@" in email:
                domain = email.split("@", 1)[1]
            if domain:
                company_result = await self._get_company_info(domain)
                result["company_info"] = company_result
                if company_result.get("status") == "found":
                    sources_used.append("linkedin")

        result["enrichment_status"] = "enriched" if sources_used else "partial"
        result["enrichment_sources"] = sources_used
        return result

    async def enrich_batch(self, leads: list[dict]) -> list[dict]:
        """批量富化。"""
        return [await self.enrich(lead) for lead in leads]
