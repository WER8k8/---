"""获客数据模型统一（六段式） — FIX-37

统一线索数据模型，将分散的字段合并为六段式标准结构：
  1. 身份信息（Identity）      - 姓名、邮箱、电话、LinkedIn
  2. 公司信息（Company）       - 公司名、网站、行业、规模
  3. 职位信息（Position）      - 职位、部门、决策层级
  4. 来源信息（Source）        - 来源渠道、URL、采集时间
  5. 评分信息（Scoring）       - 评分、等级、各维度得分
  6. 状态信息（Status）        - 处理状态、外展状态、跟进记录

同时提供各模型之间的转换函数。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


# ============================================================
# 六段式统一模型
# ============================================================

class LeadStatus(str, Enum):
    """线索处理状态。"""
    NEW = "new"                 # 新线索
    VERIFIED = "verified"       # 已验证
    CONTACTED = "contacted"     # 已联系
    RESPONDED = "responded"     # 已回复
    INTERESTED = "interested"   # 有兴趣
    NEGOTIATING = "negotiating" # 洽谈中
    WON = "won"                 # 已成交
    LOST = "lost"               # 已流失
    UNSUBSCRIBED = "unsubscribed"  # 已退订
    INVALID = "invalid"         # 无效


class OutreachStatus(str, Enum):
    """外展状态。"""
    NONE = "none"               # 未外展
    DRAFT = "draft"             # 草稿
    QUEUED = "queued"           # 排队中
    SENDING = "sending"         # 发送中
    SENT = "sent"               # 已发送
    DELIVERED = "delivered"     # 已送达
    OPENED = "opened"           # 已打开
    CLICKED = "clicked"         # 已点击
    REPLIED = "replied"         # 已回复
    BOUNCED = "bounced"         # 退信
    COMPLAINED = "complained"   # 投诉
    FAILED = "failed"           # 失败


@dataclass
class IdentitySegment:
    """1. 身份信息段。"""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    phone: str = ""
    linkedin_url: str = ""
    twitter_url: str = ""
    avatar_url: str = ""
    @property
    def display_name(self) -> str:
        """display_name。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class CompanySegment:
    """2. 公司信息段。"""
    company_name: str = ""
    website: str = ""
    industry: str = ""
    industry_tags: list[str] = field(default_factory=list)
    company_size: str = ""       # small, medium, large
    company_linkedin: str = ""
    country: str = ""
    city: str = ""
    description: str = ""


@dataclass
class PositionSegment:
    """3. 职位信息段。"""
    title: str = ""
    department: str = ""
    seniority_level: str = ""    # c_level, vp, director, manager, staff
    decision_power: str = ""     # decision_maker, influencer, end_user
    is_decision_maker: bool = False


@dataclass
class SourceSegment:
    """4. 来源信息段。"""
    channel: str = "unknown"     # linkedin, website, referral, trade_show, etc.
    source_url: str = ""
    campaign: str = ""
    referrer: str = ""
    collected_at: Optional[datetime] = None
    imported_from: str = ""      # csv, api, manual


@dataclass
class ScoringSegment:
    """5. 评分信息段。"""
    score: float = 0.0
    grade: str = "cold"          # hot, warm, cool, cold
    email_quality_score: float = 0.0
    company_completeness_score: float = 0.0
    title_match_score: float = 0.0
    source_quality_score: float = 0.0
    activity_signals_score: float = 0.0
    geo_match_score: float = 0.0
    scored_at: Optional[datetime] = None


@dataclass
class StatusSegment:
    """6. 状态信息段。"""
    lead_status: LeadStatus = LeadStatus.NEW
    outreach_status: OutreachStatus = OutreachStatus.NONE
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    follow_up_count: int = 0
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    assigned_to: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class UnifiedLead:
    """六段式统一线索模型。"""
    id: str = ""
    tenant_id: str = ""
    # 六段数据
    identity: IdentitySegment = field(default_factory=IdentitySegment)
    company: CompanySegment = field(default_factory=CompanySegment)
    position: PositionSegment = field(default_factory=PositionSegment)
    source: SourceSegment = field(default_factory=SourceSegment)
    scoring: ScoringSegment = field(default_factory=ScoringSegment)
    status: StatusSegment = field(default_factory=StatusSegment)
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict:
        """转为字典，用于 JSON 序列化。"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "identity": asdict(self.identity),
            "company": asdict(self.company),
            "position": asdict(self.position),
            "source": asdict(self.source),
            "scoring": asdict(self.scoring),
            "status": {
                **asdict(self.status),
                "lead_status": self.status.lead_status.value,
                "outreach_status": self.status.outreach_status.value,
            },
            "metadata": self.metadata,
        }

    def to_csv_row(self) -> dict[str, str]:
        """转为 CSV 行。"""
        return {
            "id": self.id,
            "email": self.identity.email,
            "first_name": self.identity.first_name,
            "last_name": self.identity.last_name,
            "phone": self.identity.phone,
            "linkedin_url": self.identity.linkedin_url,
            "company": self.company.company_name,
            "website": self.company.website,
            "industry": self.company.industry,
            "company_size": self.company.company_size,
            "country": self.company.country,
            "city": self.company.city,
            "title": self.position.title,
            "department": self.position.department,
            "seniority": self.position.seniority_level,
            "is_decision_maker": str(self.position.is_decision_maker),
            "source_channel": self.source.channel,
            "source_url": self.source.source_url,
            "score": str(self.scoring.score),
            "grade": self.scoring.grade,
            "lead_status": self.status.lead_status.value,
            "outreach_status": self.status.outreach_status.value,
            "notes": self.status.notes,
            "tags": ";".join(self.status.tags),
            "created_at": str(self.status.created_at) if self.status.created_at else "",
        }

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> UnifiedLead:
        """从 CSV 行创建。"""
        return cls(
            id=row.get("id", ""),
            identity=IdentitySegment(
                email=row.get("email", ""),
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
                phone=row.get("phone", ""),
                linkedin_url=row.get("linkedin_url", ""),
            ),
            company=CompanySegment(
                company_name=row.get("company", ""),
                website=row.get("website", ""),
                industry=row.get("industry", ""),
                company_size=row.get("company_size", ""),
                country=row.get("country", ""),
                city=row.get("city", ""),
            ),
            position=PositionSegment(
                title=row.get("title", ""),
                department=row.get("department", ""),
                seniority_level=row.get("seniority", ""),
                is_decision_maker=row.get("is_decision_maker", "false").lower() == "true",
            ),
            source=SourceSegment(
                channel=row.get("source_channel", "csv_import"),
                source_url=row.get("source_url", ""),
            ),
            status=StatusSegment(
                notes=row.get("notes", ""),
                tags=row.get("tags", "").split(";") if row.get("tags") else [],
            ),
        )

    @classmethod
    def from_prospect_lead(cls, lead: Any) -> UnifiedLead:
        """从 ProspectLead 模型转换。"""
        return cls(
            id=str(lead.id) if hasattr(lead, "id") else "",
            identity=IdentitySegment(
                email=getattr(lead, "email", "") or "",
                first_name=getattr(lead, "first_name", "") or "",
                last_name=getattr(lead, "last_name", "") or "",
                phone=getattr(lead, "phone", "") or "",
                linkedin_url=getattr(lead, "linkedin_url", "") or "",
            ),
            company=CompanySegment(
                company_name=getattr(lead, "company", "") or "",
                website=getattr(lead, "website", "") or "",
                industry=getattr(lead, "industry", "") or "",
                country=getattr(lead, "country", "") or "",
            ),
            position=PositionSegment(
                title=getattr(lead, "title", "") or "",
            ),
            source=SourceSegment(
                channel=getattr(lead, "source", "unknown") or "unknown",
            ),
            scoring=ScoringSegment(
                score=float(getattr(lead, "score", 0) or 0),
            ),
            status=StatusSegment(
                lead_status=LeadStatus(getattr(lead, "status", "new") or "new"),
            ),
        )

    # CSV 列定义
    CSV_COLUMNS = [
        "email", "first_name", "last_name", "phone", "linkedin_url",
        "company", "website", "industry", "company_size", "country", "city",
        "title", "department", "seniority", "is_decision_maker",
        "source_channel", "source_url",
        "notes", "tags",
    ]
    # 必填列
    CSV_REQUIRED_COLUMNS = ["email"]