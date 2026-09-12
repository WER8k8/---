"""
Hunter.io / Apollo.io 付费 API 集成 — FIX-53

提供：
1. 域名搜索（按域名查找公司邮箱）
2. 邮箱验证（批量验证邮箱有效性）
3. 邮箱查找（按姓名+域名查找邮箱）
4. 公司/域名富化（获取公司信息）
5. Apollo.io 兼容 API（人员搜索 + 序列）
6. 速率限制 + 缓存 + 降级

Hunter.io API 文档: https://hunter.io/api-documentation/v2
Apollo.io API 文档: https://apolloio.github.io/apollo-api-docs/

环境变量:
  HUNTER_API_KEY — Hunter.io API Key
  APOLLO_API_KEY — Apollo.io API Key
  HUNTER_CACHE_TTL — 缓存 TTL（秒，默认 86400）
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class EmailConfidence(str, Enum):
    """邮箱置信度"""
    EXCELLENT = "excellent"   # 90%+
    HIGH = "high"             # 80-90%
    MODERATE = "moderate"     # 60-80%
    LOW = "low"               # <60%
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    """邮箱验证状态"""
    VALID = "valid"
    INVALID = "invalid"
    ACCEPT_ALL = "accept_all"   # catch-all 域名
    UNKNOWN = "unknown"
    DISPOSABLE = "disposable"
    ROLE = "role"               # 角色邮箱（info@, admin@ 等）
    WEBMAIL = "webmail"         # 免费邮箱（gmail.com 等）


class ApolloPersonSeniority(str, Enum):
    """Apollo 人员级别"""
    OWNER = "owner"
    CXO = "cxo"
    VP = "vp"
    DIRECTOR = "director"
    MANAGER = "manager"
    SENIOR = "senior"
    ENTRY = "entry"
    INTERN = "intern"


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class HunterEmail:
    """Hunter 邮箱结果"""
    email: str
    first_name: str = ""
    last_name: str = ""
    position: str = ""
    confidence: EmailConfidence = EmailConfidence.UNKNOWN
    department: str = ""
    linkedin: str = ""
    phone: str = ""
    twitter: str = ""
    sources: list[dict] = field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}".strip(),
            "position": self.position,
            "confidence": self.confidence.value,
            "department": self.department,
            "linkedin": self.linkedin,
            "phone": self.phone,
            "twitter": self.twitter,
            "sources": self.sources,
            "verification_status": self.verification_status.value,
        }


@dataclass
class HunterDomainResult:
    """Hunter 域名搜索结果"""
    domain: str
    organization: str = ""
    logo: str = ""
    emails: list[HunterEmail] = field(default_factory=list)
    webmail: bool = False
    pattern: str = ""
    total_results: int = 0
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "domain": self.domain,
            "organization": self.organization,
            "logo": self.logo,
            "emails": [e.to_dict() for e in self.emails],
            "webmail": self.webmail,
            "pattern": self.pattern,
            "total_results": self.total_results,
        }


@dataclass
class ApolloPerson:
    """Apollo 人员搜索结果"""
    id: str = ""
    first_name: str = ""
    last_name: str = ""
    name: str = ""
    title: str = ""
    seniority: str = ""
    email: str = ""
    email_status: str = ""
    linkedin_url: str = ""
    company_name: str = ""
    company_id: str = ""
    company_website: str = ""
    company_linkedin: str = ""
    phone: str = ""
    departments: list[str] = field(default_factory=list)
    photo_url: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": self.name or f"{self.first_name} {self.last_name}".strip(),
            "title": self.title,
            "seniority": self.seniority,
            "email": self.email,
            "email_status": self.email_status,
            "linkedin_url": self.linkedin_url,
            "company_name": self.company_name,
            "company_id": self.company_id,
            "company_website": self.company_website,
            "company_linkedin": self.company_linkedin,
            "phone": self.phone,
            "departments": self.departments,
            "photo_url": self.photo_url,
        }


# ── 缓存 ──────────────────────────────────────────────────

class EmailCache:
    """简单的内存缓存层"""
    def __init__(self, ttl: int = 86400):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param ttl: 参数 ttl
        :return: 返回处理结果。
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def _key(self, *args: Any) -> str:
        """_key。

        参数说明：
        :param self: 参数 self
        :param *args: 参数 *args
        :return: 返回处理结果。
        """
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, *args: Any) -> Optional[Any]:
        """get。

        参数说明：
        :param self: 参数 self
        :param *args: 参数 *args
        :return: 返回处理结果。
        """
        key = self._key(*args)
        if key in self._cache:
            val, expiry = self._cache[key]
            if time.time() < expiry:
                return val
            del self._cache[key]
        return None

    def set(self, value: Any, *args: Any) -> None:
        """set。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param *args: 参数 *args
        :return: 返回处理结果。
        """
        key = self._key(*args)
        self._cache[key] = (value, time.time() + self._ttl)

    def clear(self) -> None:
        """clear。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._cache.clear()


# ── Hunter.io API 客户端 ──────────────────────────────────

class HunterClient:
    """Hunter.io API v2 客户端"""
    BASE_URL = "https://api.hunter.io/v2"
    def __init__(
        self,
        api_key: str = "",
        cache_ttl: int = 86400,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param api_key: 参数 api_key
        :param cache_ttl: 参数 cache_ttl
        :param timeout: 参数 timeout
        :param max_retries: 参数 max_retries
        :return: 返回处理结果。
        """
        self._api_key = api_key or self._env_key()
        self._cache = EmailCache(ttl=cache_ttl)
        self._timeout = timeout
        self._max_retries = max_retries
        self._rate_limit_remaining = 50
        self._rate_limit_reset = 0.0

    @staticmethod
    def _env_key() -> str:
        """_env_key。
        :return: 返回处理结果。
        """
        import os
        return os.getenv("HUNTER_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._api_key)

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        cache_key: tuple | None = None,
    ) -> dict[str, Any]:
        """发送 API 请求（带缓存、重试、速率限制）。"""
        # 缓存检查
        if cache_key:
            cached = self._cache.get(*cache_key)
            if cached is not None:
                logger.debug("Hunter cache hit: %s", endpoint)
                return cached

        # 速率限制等待
        if self._rate_limit_remaining <= 1 and time.time() < self._rate_limit_reset:
            wait = self._rate_limit_reset - time.time() + 0.5
            logger.info("Hunter rate limit: waiting %.1fs", wait)
            await asyncio.sleep(wait)

        url = f"{self.BASE_URL}/{endpoint}"
        query = {"api_key": self._api_key}
        if params:
            query.update(params)

        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.get(url, params=query)
                    self._update_rate_limit(resp.headers)
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        logger.warning("Hunter 429: retry after %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code >= 500:
                        logger.warning("Hunter 5xx attempt %d/%d", attempt + 1, self._max_retries)
                        await asyncio.sleep(2 ** attempt)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    # 缓存
                    if cache_key:
                        self._cache.set(data, *cache_key)

                    return data

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 401:
                    raise ValueError("Hunter API key 无效（401）") from e
                if e.response.status_code == 402:
                    raise ValueError("Hunter 账户配额已用完（402）") from e
                logger.warning("Hunter HTTP error: %s", e)
            except httpx.TimeoutException:
                last_error = TimeoutError(f"Hunter 请求超时: {endpoint}")
                logger.warning("Hunter timeout: %s", endpoint)
            except Exception as e:
                last_error = e
                logger.warning("Hunter request error: %s", e)

        raise last_error or RuntimeError(f"Hunter 请求失败: {endpoint}")

    def _update_rate_limit(self, headers: httpx.Headers) -> None:
        """_update_rate_limit。

        参数说明：
        :param self: 参数 self
        :param headers: 参数 headers
        :return: 返回处理结果。
        """
        try:
            remaining = headers.get("X-RateLimit-Remaining")
            reset_at = headers.get("X-RateLimit-Reset")
            if remaining:
                self._rate_limit_remaining = int(remaining)
            if reset_at:
                self._rate_limit_reset = int(reset_at)
        except (ValueError, TypeError):
            pass

    async def domain_search(
        self,
        domain: str,
        limit: int = 50,
        offset: int = 0,
        department: str = "",
        seniority: str = "",
    ) -> HunterDomainResult:
        """按域名搜索邮箱。

        Args:
            domain: 公司域名（如 example.com）
            limit: 每页数量（最大 100）
            offset: 偏移量
            department: 部门筛选（executive/engineering/finance/HR/marketing/sales/IT）
            seniority: 级别筛选（junior/senior/executive）
        """
        params = {"domain": domain, "limit": min(limit, 100), "offset": offset}
        if department:
            params["department"] = department
        if seniority:
            params["seniority"] = seniority

        data = await self._request(
            "domain-search",
            params,
            cache_key=("domain_search", domain, limit, offset, department, seniority),
        )
        result_data = data.get("data", {})
        emails = []
        for e in result_data.get("emails", []):
            emails.append(HunterEmail(
                email=e.get("value", ""),
                first_name=e.get("first_name", ""),
                last_name=e.get("last_name", ""),
                position=e.get("position", ""),
                confidence=EmailConfidence(e.get("confidence", 0)),
                department=e.get("department", ""),
                linkedin=e.get("linkedin", ""),
                phone=e.get("phone_number", ""),
                twitter=e.get("twitter", ""),
                sources=[s for s in e.get("sources", [])],
                verification_status=VerificationStatus(
                    e.get("verification", {}).get("status", "unknown")
                ),
            ))

        return HunterDomainResult(
            domain=result_data.get("domain", domain),
            organization=result_data.get("organization", ""),
            logo=result_data.get("logo", ""),
            emails=emails,
            webmail=bool(result_data.get("webmail", False)),
            pattern=result_data.get("pattern", ""),
            total_results=result_data.get("total_results", len(emails)),
        )

    async def email_verifier(self, email: str) -> HunterEmail:
        """验证单个邮箱地址。

        Args:
            email: 邮箱地址
        """
        data = await self._request(
            "email-verifier",
            {"email": email},
            cache_key=("email_verifier", email),
        )
        result = data.get("data", {})
        return HunterEmail(
            email=result.get("email", email),
            first_name=result.get("first_name", ""),
            last_name=result.get("last_name", ""),
            position=result.get("position", ""),
            confidence=EmailConfidence(result.get("score", 0)),
            department=result.get("department", ""),
            verification_status=VerificationStatus(
                result.get("status", "unknown")
            ),
        )

    async def email_finder(
        self,
        domain: str,
        first_name: str,
        last_name: str,
    ) -> HunterEmail:
        """按姓名+域名查找邮箱。

        Args:
            domain: 公司域名
            first_name: 名
            last_name: 姓
        """
        data = await self._request(
            "email-finder",
            {
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
            },
            cache_key=("email_finder", domain, first_name, last_name),
        )
        result = data.get("data", {})
        return HunterEmail(
            email=result.get("email", ""),
            first_name=result.get("first_name", first_name),
            last_name=result.get("last_name", last_name),
            position=result.get("position", ""),
            confidence=EmailConfidence(result.get("score", 0)),
            department=result.get("department", ""),
            linkedin=result.get("linkedin", ""),
            phone=result.get("phone_number", ""),
            twitter=result.get("twitter", ""),
            sources=[s for s in result.get("sources", [])],
        )

    async def batch_verify(self, emails: list[str]) -> list[HunterEmail]:
        """批量验证邮箱（并发）。

        Args:
            emails: 邮箱列表
        """
        tasks = [self.email_verifier(e) for e in emails]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        verified = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("Batch verify failed for %s: %s", emails[i], r)
                verified.append(HunterEmail(
                    email=emails[i],
                    verification_status=VerificationStatus.UNKNOWN,
                ))
            else:
                verified.append(r)
        return verified

    async def account_info(self) -> dict[str, Any]:
        """获取账户信息（配额、用量等）。"""
        data = await self._request("account")
        account = data.get("data", {})
        return {
            "email": account.get("email", ""),
            "plan_name": account.get("plan_name", ""),
            "plan_level": account.get("plan_level", 0),
            "reset_date": account.get("reset_date", ""),
            "calls": {
                "used": account.get("calls", {}).get("used", 0),
                "available": account.get("calls", {}).get("available", 0),
            },
        }

    async def combine_search(
        self,
        domain: str,
        seniority: str = "",
        department: str = "",
        max_results: int = 100,
    ) -> HunterDomainResult:
        """组合搜索：分页获取全部结果。

        Args:
            domain: 公司域名
            seniority: 级别筛选
            department: 部门筛选
            max_results: 最大结果数
        """
        all_emails: list[HunterEmail] = []
        offset = 0
        result = None
        while offset < max_results:
            result = await self.domain_search(
                domain=domain,
                limit=min(50, max_results - offset),
                offset=offset,
                seniority=seniority,
                department=department,
            )
            all_emails.extend(result.emails)
            if len(result.emails) < 50 or len(all_emails) >= max_results:
                break
            offset += 50

        if result:
            result.emails = all_emails
            result.total_results = len(all_emails)
        return result or HunterDomainResult(domain=domain)


# ── Apollo.io API 客户端 ─────────────────────────────────

class ApolloClient:
    """Apollo.io API 客户端"""
    BASE_URL = "https://api.apollo.io/api/v1"
    def __init__(
        self,
        api_key: str = "",
        cache_ttl: int = 86400,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param api_key: 参数 api_key
        :param cache_ttl: 参数 cache_ttl
        :param timeout: 参数 timeout
        :param max_retries: 参数 max_retries
        :return: 返回处理结果。
        """
        self._api_key = api_key or self._env_key()
        self._cache = EmailCache(ttl=cache_ttl)
        self._timeout = timeout
        self._max_retries = max_retries

    @staticmethod
    def _env_key() -> str:
        """_env_key。
        :return: 返回处理结果。
        """
        import os
        return os.getenv("APOLLO_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._api_key)

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
        cache_key: tuple | None = None,
    ) -> dict[str, Any]:
        """_request。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param endpoint: 参数 endpoint
        :param json_data: 参数 json_data
        :param params: 参数 params
        :param cache_key: 参数 cache_key
        :return: 返回处理结果。
        """
        if cache_key:
            cached = self._cache.get(*cache_key)
            if cached is not None:
                return cached

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self._api_key,
        }
        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    if method == "POST":
                        resp = await client.post(url, json=json_data, headers=headers)
                    else:
                        resp = await client.get(url, params=params, headers=headers)

                    if resp.status_code == 429:
                        await asyncio.sleep(5)
                        continue
                    if resp.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    if cache_key:
                        self._cache.set(data, *cache_key)

                    return data
            except Exception as e:
                last_error = e
                logger.warning("Apollo request error: %s", e)

        raise last_error or RuntimeError(f"Apollo 请求失败: {endpoint}")

    async def search_people(
        self,
        q_organization_name: str = "",
        q_keywords: str = "",
        organization_ids: list[str] | None = None,
        titles: list[str] | None = None,
        seniorities: list[str] | None = None,
        page: int = 1,
        per_page: int = 25,
        q_linkedin_url: str = "",
    ) -> dict[str, Any]:
        """搜索人员。

        Args:
            q_organization_name: 公司名关键词
            q_keywords: 关键词
            organization_ids: 公司 ID 列表
            titles: 职位关键词列表
            seniorities: 级别列表（owner/cxo/vp/director/manager等）
            page: 页码
            per_page: 每页数量
            q_linkedin_url: LinkedIn URL
        """
        json_data: dict[str, Any] = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        if q_organization_name:
            json_data["q_organization_name"] = q_organization_name
        if q_keywords:
            json_data["q_keywords"] = q_keywords
        if organization_ids:
            json_data["organization_ids"] = organization_ids
        if titles:
            json_data["titles"] = titles
        if seniorities:
            json_data["person_seniorities"] = seniorities
        if q_linkedin_url:
            json_data["q_linkedin_url"] = q_linkedin_url

        data = await self._request(
            "POST",
            "people/search",
            json_data=json_data,
            cache_key=(
                "apollo_people_search",
                q_organization_name,
                q_keywords,
                ",".join(organization_ids or []),
                ",".join(titles or []),
                ",".join(seniorities or []),
                page,
                per_page,
            ),
        )
        people = []
        for p in data.get("people", []):
            people.append(ApolloPerson(
                id=p.get("id", ""),
                first_name=p.get("first_name", ""),
                last_name=p.get("last_name", ""),
                name=p.get("name", ""),
                title=p.get("title", ""),
                seniority=p.get("seniority", ""),
                email=p.get("email", ""),
                email_status=p.get("email_status", ""),
                linkedin_url=p.get("linkedin_url", ""),
                company_name=p.get("organization", {}).get("name", ""),
                company_id=p.get("organization_id", ""),
                company_website=p.get("organization", {}).get("website_url", ""),
                company_linkedin=p.get("organization", {}).get("linkedin_url", ""),
                phone="",
                departments=p.get("departments", []),
                photo_url=p.get("photo_url", ""),
            ).to_dict())

        return {
            "people": people,
            "total": data.get("pagination", {}).get("total_entries", 0),
            "page": page,
            "per_page": per_page,
            "total_pages": data.get("pagination", {}).get("total_pages", 0),
        }

    async def people_enrich(
        self,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        domain: str = "",
        linkedin_url: str = "",
    ) -> dict[str, Any]:
        """富化人员信息。

        Args:
            first_name: 名
            last_name: 姓
            email: 邮箱
            domain: 域名
            linkedin_url: LinkedIn URL
        """
        json_data: dict[str, Any] = {}
        if first_name:
            json_data["first_name"] = first_name
        if last_name:
            json_data["last_name"] = last_name
        if email:
            json_data["email"] = email
        if domain:
            json_data["domain"] = domain
        if linkedin_url:
            json_data["linkedin_url"] = linkedin_url

        data = await self._request(
            "POST",
            "people/match",
            json_data=json_data,
            cache_key=(
                "apollo_people_enrich",
                first_name,
                last_name,
                email,
                domain,
                linkedin_url,
            ),
        )
        p = data.get("person", {})
        if not p:
            return {"found": False, "person": None}

        return {
            "found": True,
            "person": ApolloPerson(
                id=p.get("id", ""),
                first_name=p.get("first_name", ""),
                last_name=p.get("last_name", ""),
                name=p.get("name", ""),
                title=p.get("title", ""),
                seniority=p.get("seniority", ""),
                email=p.get("email", ""),
                email_status=p.get("email_status", ""),
                linkedin_url=p.get("linkedin_url", ""),
                company_name=p.get("organization", {}).get("name", ""),
                company_id=p.get("organization_id", ""),
                company_website=p.get("organization", {}).get("website_url", ""),
                company_linkedin=p.get("organization", {}).get("linkedin_url", ""),
                phone="",
                departments=p.get("departments", []),
                photo_url=p.get("photo_url", ""),
            ).to_dict(),
        }

    async def organization_search(
        self,
        q_name: str = "",
        q_keywords: str = "",
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        """搜索公司/组织。

        Args:
            q_name: 公司名
            q_keywords: 关键词
            page: 页码
            per_page: 每页数量
        """
        json_data: dict[str, Any] = {
            "page": page,
            "per_page": min(per_page, 100),
        }
        if q_name:
            json_data["q_name"] = q_name
        if q_keywords:
            json_data["q_keywords"] = q_keywords

        data = await self._request(
            "POST",
            "organizations/search",
            json_data=json_data,
            cache_key=("apollo_org_search", q_name, q_keywords, page, per_page),
        )
        orgs = []
        for o in data.get("organizations", []):
            orgs.append({
                "id": o.get("id", ""),
                "name": o.get("name", ""),
                "website_url": o.get("website_url", ""),
                "linkedin_url": o.get("linkedin_url", ""),
                "primary_domain": o.get("primary_domain", ""),
                "num_employees": o.get("num_employees", 0),
                "industry": o.get("industry", ""),
                "revenue": o.get("revenue", ""),
                "city": o.get("city", ""),
                "state": o.get("state", ""),
                "country": o.get("country", ""),
                "logo_url": o.get("logo_url", ""),
            })

        return {
            "organizations": orgs,
            "total": data.get("pagination", {}).get("total_entries", 0),
            "page": page,
            "per_page": per_page,
            "total_pages": data.get("pagination", {}).get("total_pages", 0),
        }


# ── 统一门面服务 ──────────────────────────────────────────

class LeadEnrichmentService:
    """线索富化统一门面。

    自动选择最佳数据源：
    1. Apollo.io（优先：人员搜索 + 富化）
    2. Hunter.io（次选：邮箱查找 + 验证）
    3. 零成本引擎（降级：格式校验 + DNS MX）
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._hunter = HunterClient()
        self._apollo = ApolloClient()

    @property
    def available_sources(self) -> list[str]:
        """available_sources。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        sources = []
        if self._apollo.is_configured:
            sources.append("apollo")
        if self._hunter.is_configured:
            sources.append("hunter")
        return sources

    async def find_emails_by_domain(
        self,
        domain: str,
        title_keywords: list[str] | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """按域名查找邮箱（自动选择数据源）。

        Args:
            domain: 公司域名
            title_keywords: 职位关键词
            max_results: 最大结果数
        """
        results = {"emails": [], "source": "", "error": ""}
        # 优先 Apollo
        if self._apollo.is_configured:
            try:
                apollo_result = await self._apollo.search_people(
                    q_organization_name=domain.replace(".com", "").replace("www.", ""),
                    titles=title_keywords,
                    per_page=min(max_results, 100),
                )
                for p in apollo_result.get("people", []):
                    if p.get("email"):
                        results["emails"].append({
                            "email": p["email"],
                            "first_name": p.get("first_name", ""),
                            "last_name": p.get("last_name", ""),
                            "position": p.get("title", ""),
                            "company": p.get("company_name", ""),
                            "linkedin": p.get("linkedin_url", ""),
                            "confidence": p.get("email_status", "unknown"),
                            "source": "apollo",
                        })
                results["source"] = "apollo"
                if results["emails"]:
                    return results
            except Exception as e:
                logger.warning("Apollo search failed: %s", e)
                results["error"] = str(e)

        # 降级 Hunter
        if self._hunter.is_configured:
            try:
                hunter_result = await self._hunter.combine_search(
                    domain=domain,
                    max_results=max_results,
                )
                for e in hunter_result.emails:
                    results["emails"].append({
                        "email": e.email,
                        "first_name": e.first_name,
                        "last_name": e.last_name,
                        "position": e.position,
                        "company": hunter_result.organization,
                        "linkedin": e.linkedin,
                        "confidence": e.confidence.value,
                        "source": "hunter",
                    })
                results["source"] = "hunter"
                if results["emails"]:
                    return results
            except Exception as e:
                logger.warning("Hunter search failed: %s", e)
                results["error"] = results.get("error", "") or str(e)

        return results

    async def verify_email(self, email: str) -> dict[str, Any]:
        """验证邮箱地址。"""
        if self._hunter.is_configured:
            try:
                result = await self._hunter.email_verifier(email)
                return {
                    "email": result.email,
                    "status": result.verification_status.value,
                    "confidence": result.confidence.value,
                    "source": "hunter",
                }
            except Exception as e:
                logger.warning("Hunter verify failed: %s", e)

        # 降级到零成本验证
        try:
            from app.services.ubrain.email_verification_service import (
                verify_email as zero_cost_verify,
            )
            zero_result = await zero_cost_verify(email)
            return {
                "email": email,
                "status": zero_result.get("status", "unknown"),
                "confidence": "unknown",
                "source": "zero_cost",
            }
        except Exception:
            return {"email": email, "status": "unknown", "confidence": "unknown", "source": "none"}

    async def enrich_lead(
        self,
        email: str = "",
        first_name: str = "",
        last_name: str = "",
        domain: str = "",
        linkedin_url: str = "",
    ) -> dict[str, Any]:
        """富化线索信息。"""
        if self._apollo.is_configured:
            try:
                result = await self._apollo.people_enrich(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    domain=domain,
                    linkedin_url=linkedin_url,
                )
                if result.get("found"):
                    return result
            except Exception as e:
                logger.warning("Apollo enrich failed: %s", e)

        # 降级到 Hunter
        if self._hunter.is_configured and email and domain:
            try:
                result = await self._hunter.email_verifier(email)
                return {
                    "found": True,
                    "person": {
                        "email": result.email,
                        "first_name": result.first_name,
                        "last_name": result.last_name,
                        "position": result.position,
                        "confidence": result.confidence.value,
                        "source": "hunter",
                    },
                }
            except Exception as e:
                logger.warning("Hunter enrich failed: %s", e)

        return {"found": False, "person": None}

    async def account_status(self) -> dict[str, Any]:
        """获取所有数据源账户状态。"""
        status = {"sources": {}}
        if self._hunter.is_configured:
            try:
                status["sources"]["hunter"] = await self._hunter.account_info()
            except Exception as e:
                status["sources"]["hunter"] = {"error": str(e)}

        if self._apollo.is_configured:
            status["sources"]["apollo"] = {"status": "configured"}

        return status


# 单例
lead_enrichment_service = LeadEnrichmentService()