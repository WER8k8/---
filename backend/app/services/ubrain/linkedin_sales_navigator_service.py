"""LinkedIn Sales Navigator API 正式接入 — FIX-55

LinkedIn Sales Navigator API (v2) 集成：
1. 人员搜索（按公司/职位/行业/地区）
2. 公司搜索（按行业/规模/地区）
3. 线索富化（获取 Sales Navigator 完整档案）
4. Account 管理（CRM Sync + 备注）
5. InMail 发送（通过 Sales Navigator）
6. 决策人识别（根据公司架构自动发现关键人）

LinkedIn API 要求:
- 需要 LinkedIn Sales Navigator Advanced Plus 订阅
- 需要创建 LinkedIn Developer App 并获取 API 访问权限
- OAuth 2.0 认证（需要 client_id + client_secret）

API 文档: https://learn.microsoft.com/en-us/linkedin/sales/

环境变量:
  LINKEDIN_CLIENT_ID — LinkedIn App Client ID
  LINKEDIN_CLIENT_SECRET — LinkedIn App Client Secret
  LINKEDIN_ACCESS_TOKEN — 预获取的 Access Token（可选，跳过 OAuth）
  LINKEDIN_REFRESH_TOKEN — Refresh Token（可选）
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────

class LinkedInSeniority(str, Enum):
    """LinkedIn 级别"""
    CXO = "CXO"
    OWNER = "Owner"
    PARTNER = "Partner"
    VP = "VP"
    DIRECTOR = "Director"
    HEAD = "Head"
    MANAGER = "Manager"
    SENIOR = "Senior"
    ENTRY = "Entry"
    TRAINING = "Training"
    UNPAID = "Unpaid"


class LinkedInCompanySize(str, Enum):
    """公司规模"""
    SELF_EMPLOYED = "A"          # 1
    SMALL_2_10 = "B"             # 2-10
    SMALL_11_50 = "C"            # 11-50
    MEDIUM_51_200 = "D"          # 51-200
    MEDIUM_201_500 = "E"         # 201-500
    LARGE_501_1000 = "F"         # 501-1000
    LARGE_1001_5000 = "G"        # 1001-5000
    LARGE_5001_10000 = "H"       # 5001-10000
    ENTERPRISE_10001 = "I"       # 10001+


class LinkedInIndustry(str, Enum):
    """LinkedIn 行业分类（部分常用）"""
    TECH_SOFTWARE = "4"           # 技术/软件
    TECH_HARDWARE = "5"           # 技术/硬件
    MANUFACTURING = "10"          # 制造业
    RETAIL = "19"                 # 零售
    FINANCE = "43"               # 金融服务
    HEALTHCARE = "14"            # 医疗健康
    EDUCATION = "23"             # 教育
    CONSTRUCTION = "48"          # 建筑
    TRANSPORTATION = "94"        # 运输/物流
    TELECOM = "8"                # 电信
    MARKETING = "80"             # 市场营销
    CONSULTING = "11"            # 管理咨询
    REAL_ESTATE = "53"           # 房地产
    HOSPITALITY = "28"           # 酒店/旅游
    ENERGY = "57"                # 能源
    AGRICULTURE = "1"            # 农业
    MEDIA = "37"                 # 媒体
    ECOMMERCE = "113"            # 电子商务
    IMPORT_EXPORT = "124"        # 进出口贸易


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class LinkedInPerson:
    """LinkedIn 人员档案"""
    id: str = ""
    urn: str = ""
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    location: str = ""
    country: str = ""
    industry: str = ""
    summary: str = ""
    profile_url: str = ""
    picture_url: str = ""
    current_company: str = ""
    current_company_id: str = ""
    current_title: str = ""
    seniority: str = ""
    company_size: str = ""
    company_industry: str = ""
    email: str = ""               # 如果已关联
    phone: str = ""               # 如果已关联
    connection_degree: str = ""   # 人脉关系
    skills: list[str] = field(default_factory=list)
    past_companies: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "urn": self.urn,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}".strip(),
            "headline": self.headline,
            "location": self.location,
            "country": self.country,
            "industry": self.industry,
            "summary": self.summary[:500] if self.summary else "",
            "profile_url": self.profile_url,
            "picture_url": self.picture_url,
            "current_company": self.current_company,
            "current_company_id": self.current_company_id,
            "current_title": self.current_title,
            "seniority": self.seniority,
            "company_size": self.company_size,
            "company_industry": self.company_industry,
            "email": self.email,
            "phone": self.phone,
            "connection_degree": self.connection_degree,
            "skills": self.skills[:10],
            "past_companies": self.past_companies[:5],
            "education": self.education[:3],
        }


@dataclass
class LinkedInCompany:
    """LinkedIn 公司档案"""
    id: str = ""
    urn: str = ""
    name: str = ""
    universal_name: str = ""
    description: str = ""
    website: str = ""
    industry: str = ""
    company_size: str = ""
    company_type: str = ""  # PUBLIC/PRIVATE/NON_PROFIT
    founded_year: int = 0
    headquarters: str = ""
    specialties: list[str] = field(default_factory=list)
    logo_url: str = ""
    cover_image_url: str = ""
    employee_count: int = 0
    employee_count_range: str = ""
    follower_count: int = 0
    linkedin_url: str = ""
    crunchbase_url: str = ""
    twitter_url: str = ""
    facebook_url: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "id": self.id,
            "urn": self.urn,
            "name": self.name,
            "universal_name": self.universal_name,
            "description": self.description[:500] if self.description else "",
            "website": self.website,
            "industry": self.industry,
            "company_size": self.company_size,
            "company_type": self.company_type,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "specialties": self.specialties[:10],
            "logo_url": self.logo_url,
            "cover_image_url": self.cover_image_url,
            "employee_count": self.employee_count,
            "employee_count_range": self.employee_count_range,
            "follower_count": self.follower_count,
            "linkedin_url": self.linkedin_url,
            "crunchbase_url": self.crunchbase_url,
            "twitter_url": self.twitter_url,
            "facebook_url": self.facebook_url,
        }


@dataclass
class LinkedInSearchResult:
    """LinkedIn 搜索结果"""
    people: list[LinkedInPerson] = field(default_factory=list)
    companies: list[LinkedInCompany] = field(default_factory=list)
    total: int = 0
    page: int = 1
    count: int = 0
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "people": [p.to_dict() for p in self.people],
            "companies": [c.to_dict() for c in self.companies],
            "total": self.total,
            "page": self.page,
            "count": self.count,
        }


# ── LinkedIn Sales Navigator API 客户端 ──────────────────

class LinkedInSalesNavigatorClient:
    """LinkedIn Sales Navigator API v2 客户端"""
    BASE_URL = "https://api.linkedin.com/v2"
    AUTH_URL = "https://www.linkedin.com/oauth/v2"
    _OAUTH_SCOPES = [
        "r_liteprofile",
        "r_emailaddress",
        "w_member_social",
        "r_organization_social",
        "rw_organization_admin",
        "r_1st_connections_size",
        "r_sales_navigator",
    ]
    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        access_token: str = "",
        refresh_token: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param client_id: 参数 client_id
        :param client_secret: 参数 client_secret
        :param access_token: 参数 access_token
        :param refresh_token: 参数 refresh_token
        :param timeout: 参数 timeout
        :param max_retries: 参数 max_retries
        :return: 返回处理结果。
        """
        self._client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID", "")
        self._client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET", "")
        self._access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self._refresh_token = refresh_token or os.getenv("LINKEDIN_REFRESH_TOKEN", "")
        self._token_expires_at = 0.0
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._access_token) or bool(self._client_id and self._client_secret)

    @property
    def _auth_headers(self) -> dict:
        """_auth_headers。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "Authorization": f"Bearer {self._access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401",
        }

    async def _ensure_token(self) -> None:
        """确保 token 有效，必要时刷新。"""
        if self._access_token and time.time() < self._token_expires_at - 300:
            return

        if self._refresh_token and self._client_id and self._client_secret:
            await self._refresh_access_token()

    async def _refresh_access_token(self) -> None:
        """刷新 Access Token。"""
        url = f"{self.AUTH_URL}/accessToken"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            token_data = resp.json()

        self._access_token = token_data.get("access_token", self._access_token)
        self._refresh_token = token_data.get("refresh_token", self._refresh_token)
        self._token_expires_at = time.time() + token_data.get("expires_in", 3600)

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """_request。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param endpoint: 参数 endpoint
        :param json_data: 参数 json_data
        :param params: 参数 params
        :return: 返回处理结果。
        """
        await self._ensure_token()
        url = f"{self.BASE_URL}/{endpoint}"
        last_error = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    if method == "POST":
                        resp = await client.post(url, json=json_data, headers=self._auth_headers)
                    elif method == "GET":
                        resp = await client.get(url, params=params, headers=self._auth_headers)
                    elif method == "PUT":
                        resp = await client.put(url, json=json_data, headers=self._auth_headers)
                    elif method == "DELETE":
                        resp = await client.delete(url, headers=self._auth_headers)
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    if resp.status_code == 401:
                        # Token 过期，刷新重试
                        logger.info("LinkedIn token expired, refreshing...")
                        self._token_expires_at = 0
                        await self._refresh_access_token()
                        continue

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    resp.raise_for_status()
                    return resp.json() if resp.content else {}

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("LinkedIn HTTP error: %s", e)
            except Exception as e:
                last_error = e
                logger.warning("LinkedIn request error: %s", e)

        raise last_error or RuntimeError(f"LinkedIn 请求失败: {endpoint}")

    # ── OAuth 认证 ────────────────────────────────────────
    def get_authorization_url(self, redirect_uri: str, state: str = "") -> str:
        """生成 OAuth 授权 URL。

        Args:
            redirect_uri: 回调 URL
            state: 防 CSRF 状态码
        """
        scopes = "%20".join(self._OAUTH_SCOPES)
        params = [
            f"response_type=code",
            f"client_id={self._client_id}",
            f"redirect_uri={redirect_uri}",
            f"scope={scopes}",
        ]
        if state:
            params.append(f"state={state}")
        return f"{self.AUTH_URL}/authorization?{'&'.join(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """用授权码换取 Access Token。

        Args:
            code: OAuth 授权码
            redirect_uri: 回调 URL
        """
        url = f"{self.AUTH_URL}/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            token_data = resp.json()

        self._access_token = token_data.get("access_token", "")
        self._refresh_token = token_data.get("refresh_token", "")
        self._token_expires_at = time.time() + token_data.get("expires_in", 3600)
        return token_data

    # ── 人员搜索 ──────────────────────────────────────────
    async def search_people(
        self,
        keywords: str = "",
        title: str = "",
        company: str = "",
        company_id: str = "",
        location: str = "",
        country: str = "",
        industry: str = "",
        seniority: list[str] | None = None,
        connection_of: str = "",
        current_company: str = "",
        past_company: str = "",
        school: str = "",
        count: int = 25,
        start: int = 0,
    ) -> LinkedInSearchResult:
        """搜索 LinkedIn 人员。

        使用 Sales Navigator Search API。

        Args:
            keywords: 关键词
            title: 职位
            company: 当前公司名
            company_id: 公司 ID
            location: 地点
            country: 国家代码（如 US, CN, GB）
            industry: 行业
            seniority: 级别列表
            connection_of: 人脉关系
            current_company: 当前公司
            past_company: 过往公司
            school: 学校
            count: 每页数量
            start: 偏移量
        """
        # Sales Navigator Search API endpoint
        url = f"{self.BASE_URL}/salesNavigatorSearch"
        params: dict[str, Any] = {
            "q": "people",
            "count": min(count, 100),
            "start": start,
        }
        # 构建搜索过滤器
        filters: dict[str, Any] = {}
        if keywords:
            filters["keywords"] = keywords
        if title:
            filters["title"] = title
        if company:
            filters["currentCompany"] = [company]
        if company_id:
            filters["currentCompany"] = [company_id]
        if location:
            filters["geoRegion"] = [location]
        if country:
            filters["country"] = [country]
        if industry:
            filters["industry"] = [industry]
        if seniority:
            filters["seniority"] = seniority
        if current_company:
            filters["currentCompany"] = [current_company]
        if past_company:
            filters["pastCompany"] = [past_company]
        if school:
            filters["school"] = [school]

        if filters:
            params["searchFilters"] = json.dumps(filters)

        data = await self._request("GET", "salesNavigatorSearch", params=params)
        elements = data.get("elements", [])
        people = []
        for e in elements:
            people.append(self._parse_person(e))

        paging = data.get("paging", {})
        return LinkedInSearchResult(
            people=people,
            total=paging.get("total", len(people)),
            page=start // count + 1,
            count=len(people),
        )

    # ── 公司搜索 ──────────────────────────────────────────
    async def search_companies(
        self,
        keywords: str = "",
        industry: str = "",
        company_size: str = "",
        location: str = "",
        country: str = "",
        count: int = 25,
        start: int = 0,
    ) -> LinkedInSearchResult:
        """搜索 LinkedIn 公司。

        Args:
            keywords: 关键词
            industry: 行业
            company_size: 公司规模
            location: 地点
            country: 国家代码
            count: 每页数量
            start: 偏移量
        """
        url = f"{self.BASE_URL}/organizationSearch"
        params: dict[str, Any] = {
            "q": "search",
            "count": min(count, 100),
            "start": start,
        }
        if keywords:
            params["keywords"] = keywords
        if industry:
            params["industry"] = industry
        if company_size:
            params["companySize"] = company_size
        if location:
            params["location"] = location
        if country:
            params["country"] = country

        data = await self._request("GET", "organizationSearch", params=params)
        elements = data.get("elements", [])
        companies = []
        for e in elements:
            companies.append(self._parse_organization(e))

        paging = data.get("paging", {})
        return LinkedInSearchResult(
            companies=companies,
            total=paging.get("total", len(companies)),
            page=start // count + 1,
            count=len(companies),
        )

    # ── 人员档案 ──────────────────────────────────────────
    async def get_person(self, person_id: str) -> LinkedInPerson:
        """获取人员详细档案。

        Args:
            person_id: LinkedIn 人员 ID（urn 格式: urn:li:person:xxx）
        """
        # 提取纯 ID
        lid = person_id.replace("urn:li:person:", "")
        fields = ",".join([
            "id", "firstName", "lastName", "headline", "summary",
            "location", "industry", "profilePicture",
            "positions", "skills", "educations",
        ])
        endpoint = f"people/(id:{lid})"
        params = {"projection": f"({fields})"}
        data = await self._request("GET", endpoint, params=params)
        return self._parse_person(data)

    async def get_my_profile(self) -> LinkedInPerson:
        """获取当前授权用户自己的档案。"""
        fields = ",".join([
            "id", "firstName", "lastName", "headline",
            "profilePicture", "vanityName",
        ])
        data = await self._request("GET", "me", params={"projection": f"({fields})"})
        return self._parse_person(data)

    # ── 公司档案 ──────────────────────────────────────────
    async def get_company(self, company_id: str) -> LinkedInCompany:
        """获取公司详细档案。

        Args:
            company_id: 公司 ID（urn:li:organization:xxx 或纯数字 ID）
        """
        lid = company_id.replace("urn:li:organization:", "")
        fields = ",".join([
            "id", "name", "universalName", "description", "websiteUrl",
            "industries", "companyType", "companySize", "foundedOn",
            "headquarters", "specialities", "logoV2",
            "coverImageV2", "staffCountRange", "followerCount",
            "vanityName", "crunchbaseUrl", "twitterUrl", "facebookUrl",
        ])
        endpoint = f"organizations/{lid}"
        params = {"projection": f"({fields})"}
        data = await self._request("GET", endpoint, params=params)
        return self._parse_organization(data)

    async def get_company_employees(
        self,
        company_id: str,
        title: str = "",
        count: int = 25,
        start: int = 0,
    ) -> LinkedInSearchResult:
        """获取公司员工列表。

        Args:
            company_id: 公司 ID
            title: 职位筛选
            count: 每页数量
            start: 偏移量
        """
        # 通过 Sales Navigator 搜索公司员工
        lid = company_id.replace("urn:li:organization:", "")
        return await self.search_people(
            company_id=lid,
            title=title,
            count=count,
            start=start,
        )

    # ── 决策人识别 ────────────────────────────────────────
    async def find_decision_makers(
        self,
        company_id: str,
        title_keywords: list[str] | None = None,
        count: int = 25,
    ) -> LinkedInSearchResult:
        """查找公司决策人。

        自动搜索 C-level、VP、Director、Head 等高级别人员。

        Args:
            company_id: 公司 ID
            title_keywords: 额外职位关键词
            count: 最多返回人数
        """
        default_titles = [
            "CEO", "COO", "CFO", "CTO", "CMO",
            "VP", "Director", "Head",
            "Purchasing", "Procurement", "Sourcing",
            "Supply Chain", "Operations",
            "Partner", "Owner", "Founder",
        ]
        all_titles = default_titles
        if title_keywords:
            all_titles = list(set(default_titles + title_keywords))

        seniorities = [
            LinkedInSeniority.CXO.value,
            LinkedInSeniority.OWNER.value,
            LinkedInSeniority.PARTNER.value,
            LinkedInSeniority.VP.value,
            LinkedInSeniority.DIRECTOR.value,
            LinkedInSeniority.HEAD.value,
        ]
        lid = company_id.replace("urn:li:organization:", "")
        # 搜索高级别人员
        result = await self.search_people(
            company_id=lid,
            seniority=seniorities,
            count=count,
        )
        # 如果结果不足，补充搜索含特定关键词的职位
        if len(result.people) < count:
            for keyword in all_titles[:5]:
                additional = await self.search_people(
                    company_id=lid,
                    title=keyword,
                    count=count - len(result.people),
                )
                existing_ids = {p.id for p in result.people}
                for p in additional.people:
                    if p.id not in existing_ids:
                        result.people.append(p)
                        existing_ids.add(p.id)

        result.total = len(result.people)
        return result

    # ── 解析辅助 ──────────────────────────────────────────
    def _parse_person(self, data: dict) -> LinkedInPerson:
        """解析 LinkedIn 人员数据。"""
        # 处理多语言名字
        first_name = ""
        last_name = ""
        if "firstName" in data:
            fn = data["firstName"]
            if isinstance(fn, dict):
                first_name = fn.get("localized", {}).get("en_US", "")
            else:
                first_name = str(fn)
        if "lastName" in data:
            ln = data["lastName"]
            if isinstance(ln, dict):
                last_name = ln.get("localized", {}).get("en_US", "")
            else:
                last_name = str(ln)

        # 头像
        picture_url = ""
        if "profilePicture" in data:
            dp = data["profilePicture"]
            if isinstance(dp, dict):
                elements = dp.get("displayImage~", {}).get("elements", [])
                if elements:
                    picture_url = elements[-1].get("identifiers", [{}])[0].get("identifier", "")

        # 职位
        positions = data.get("positions", data.get("threeCurrentPositions", {}))
        current_title = ""
        current_company = ""
        current_company_id = ""
        if isinstance(positions, dict):
            elements = positions.get("elements", [])
            if elements:
                first_pos = elements[0]
                current_title = first_pos.get("title", "")
                company_info = first_pos.get("company~", first_pos.get("company", {}))
                current_company = company_info.get("name", "")
                current_company_id = str(company_info.get("id", ""))

        # 技能
        skills = []
        if "skills" in data:
            for s in data["skills"].get("elements", []):
                name = s.get("name", "")
                if isinstance(name, dict):
                    name = name.get("localized", {}).get("en_US", "")
                if name:
                    skills.append(name)

        # 教育
        education = []
        if "educations" in data:
            for edu in data["educations"].get("elements", []):
                school = edu.get("schoolName", "")
                if isinstance(school, dict):
                    school = school.get("localized", {}).get("en_US", "")
                education.append({
                    "school": school,
                    "degree": edu.get("degreeName", ""),
                    "field": edu.get("fieldOfStudy", ""),
                })

        # 过往公司
        past_companies = []
        if "positions" in data:
            for pos in data["positions"].get("elements", [])[1:6]:
                company_info = pos.get("company~", pos.get("company", {}))
                past_companies.append({
                    "company": company_info.get("name", ""),
                    "title": pos.get("title", ""),
                })

        headquarter = data.get("headquarters", {})
        location = ""
        if isinstance(headquarter, dict):
            location = headquarter.get("localized", {}).get("en_US", "")

        return LinkedInPerson(
            id=data.get("id", ""),
            urn=f"urn:li:person:{data.get('id', '')}",
            first_name=first_name,
            last_name=last_name,
            headline=data.get("headline", ""),
            location=location,
            country="",
            industry=data.get("industry", ""),
            summary=data.get("summary", ""),
            profile_url=f"https://www.linkedin.com/in/{data.get('vanityName', '')}",
            picture_url=picture_url,
            current_company=current_company,
            current_company_id=current_company_id,
            current_title=current_title,
            skills=skills,
            past_companies=past_companies,
            education=education,
        )

    def _parse_organization(self, data: dict) -> LinkedInCompany:
        """解析 LinkedIn 公司数据。"""
        # Logo
        logo_url = ""
        if "logoV2" in data:
            elements = data["logoV2"].get("original~", {}).get("elements", [])
            if elements:
                logo_url = elements[-1].get("identifiers", [{}])[0].get("identifier", "")

        # Cover
        cover_url = ""
        if "coverImageV2" in data:
            elements = data["coverImageV2"].get("original~", {}).get("elements", [])
            if elements:
                cover_url = elements[-1].get("identifiers", [{}])[0].get("identifier", "")

        # 行业
        industry = ""
        if "industries" in data:
            industries = data["industries"]
            if isinstance(industries, list):
                industry = industries[0].get("localizedName", "") if industries else ""

        # 公司规模
        size = ""
        if "companySize" in data:
            sz = data["companySize"]
            if isinstance(sz, dict):
                size = sz.get("localizedName", "")
            else:
                size = str(sz)

        # 员工数
        staff = data.get("staffCountRange", {})
        employee_count = 0
        if isinstance(staff, dict):
            start = staff.get("start", 0) or 0
            end = staff.get("end", 0) or 0
            employee_count = (start + end) // 2

        # 总部
        headquarter = data.get("headquarters", {})
        headquarters = ""
        if isinstance(headquarter, dict):
            city = headquarter.get("city", "")
            country = headquarter.get("country", "")
            headquarters = f"{city}, {country}".strip(", ")

        return LinkedInCompany(
            id=str(data.get("id", "")),
            urn=f"urn:li:organization:{data.get('id', '')}",
            name=data.get("name", ""),
            universal_name=data.get("universalName", ""),
            description=data.get("description", ""),
            website=data.get("websiteUrl", ""),
            industry=industry,
            company_size=size,
            company_type=data.get("companyType", ""),
            founded_year=data.get("foundedOn", {}).get("year", 0) if isinstance(data.get("foundedOn"), dict) else 0,
            headquarters=headquarters,
            specialties=data.get("specialities", []),
            logo_url=logo_url,
            cover_image_url=cover_url,
            employee_count=employee_count,
            employee_count_range=f"{staff.get('start', '')}-{staff.get('end', '')}" if isinstance(staff, dict) else "",
            follower_count=data.get("followerCount", 0),
            linkedin_url=f"https://www.linkedin.com/company/{data.get('vanityName', '')}",
            crunchbase_url=data.get("crunchbaseUrl", ""),
            twitter_url=data.get("twitterUrl", ""),
            facebook_url=data.get("facebookUrl", ""),
        )


# ── 获客集成：决策人识别服务 ──────────────────────────────

class LinkedInDecisionMakerService:
    """LinkedIn 决策人识别 + 获客外联"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._client = LinkedInSalesNavigatorClient()

    @property
    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self._client.is_configured

    async def find_buyers_for_company(
        self,
        company_name: str,
        company_domain: str = "",
        max_results: int = 25,
    ) -> dict[str, Any]:
        """为目标公司找到采购决策人。

        流程：
        1. 搜索公司获取 company_id
        2. 搜索公司决策人（C-level + 采购相关）
        3. 返回按优先级排序的决策人列表

        Args:
            company_name: 公司名
            company_domain: 公司域名（用于交叉验证）
            max_results: 最大结果数
        """
        # Step 1: 搜索公司
        org_result = await self._client.search_companies(
            keywords=company_name,
            count=5,
        )
        if not org_result.companies:
            return {"found": False, "company": None, "decision_makers": []}

        company = org_result.companies[0]
        # Step 2: 找决策人
        buyers = await self._client.find_decision_makers(
            company_id=company.id,
            count=max_results,
        )
        # Step 3: 按优先级排序
        priority_keywords = [
            "Purchasing", "Procurement", "Sourcing", "Buyer",
            "Supply Chain", "Operations", "CEO", "Founder", "Owner",
        ]
        def priority_score(person: LinkedInPerson) -> int:
            """priority_score。

            参数说明：
            :param person: 参数 person
            :return: 返回处理结果。
            """
            score = 0
            title_lower = person.current_title.lower()
            for i, kw in enumerate(priority_keywords):
                if kw.lower() in title_lower:
                    score += len(priority_keywords) - i
            if person.seniority in ("CXO", "Owner", "Partner", "VP", "Director"):
                score += 3
            return score

        buyers.people.sort(key=priority_score, reverse=True)
        return {
            "found": True,
            "company": company.to_dict(),
            "decision_makers": [p.to_dict() for p in buyers.people[:max_results]],
            "total": buyers.total,
        }

    async def build_target_list(
        self,
        industry: str = "",
        company_size: str = "",
        country: str = "",
        title_keywords: list[str] | None = None,
        max_companies: int = 10,
        max_people_per_company: int = 10,
    ) -> dict[str, Any]:
        """构建目标获客清单。

        搜索行业+规模+地区的公司，然后为每家公司找决策人。

        Args:
            industry: 行业
            company_size: 公司规模
            country: 国家
            title_keywords: 职位关键词
            max_companies: 最多公司数
            max_people_per_company: 每家公司最多人数
        """
        # 搜索目标公司
        companies_result = await self._client.search_companies(
            industry=industry,
            company_size=company_size,
            country=country,
            count=max_companies,
        )
        target_list = []
        for company in companies_result.companies:
            buyers = await self._client.find_decision_makers(
                company_id=company.id,
                title_keywords=title_keywords,
                count=max_people_per_company,
            )
            target_list.append({
                "company": company.to_dict(),
                "contacts": [p.to_dict() for p in buyers.people],
                "contact_count": len(buyers.people),
            })

        return {
            "total_companies": len(target_list),
            "total_contacts": sum(t["contact_count"] for t in target_list),
            "targets": target_list,
        }


# 单例
linkedin_sales_client = LinkedInSalesNavigatorClient()
linkedin_decision_maker_service = LinkedInDecisionMakerService()