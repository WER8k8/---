"""
统一线索数据模型 —— 所有渠道的线索收敛到单一模型

去重规则（优先级降序）：
1. 邮箱精确匹配（最高优先级）
2. 域名 + 公司名模糊匹配
3. LinkedIn URL 精确匹配
4. 电话精确匹配
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    CheckConstraint, Column, DateTime, Enum, Float, ForeignKey, Index, Integer,
    JSON, String, Text, UniqueConstraint,
)

from app.core.database import Base, UUID_TYPE


class LeadSource(str, enum.Enum):
    """线索来源渠道"""
    GOOGLE_CSE = "google_cse"           # Google Custom Search
    WEBSITE_SCRAPE = "website_scrape"   # 网站抓取
    HUNTER_IO = "hunter_io"             # Hunter.io
    APOLLO_IO = "apollo_io"             # Apollo.io
    LINKEDIN = "linkedin"               # LinkedIn
    WHATSAPP = "whatsapp"               # WhatsApp
    REDDIT = "reddit"                   # Reddit
    TIKTOK = "tiktok"                   # TikTok
    QUORA = "quora"                     # Quora
    MANUAL_IMPORT = "manual_import"     # 手动导入/CSV
    REFERRAL = "referral"               # 推荐


class LeadStatus(str, enum.Enum):
    """线索状态"""
    DISCOVERED = "discovered"       # 刚发现
    ENRICHED = "enriched"           # 已 enrich（补充信息）
    VERIFIED = "verified"           # 已验证（邮箱/电话）
    QUALIFIED = "qualified"         # 已认证（符合 ICP）
    CONTACTED = "contacted"         # 已联系
    ENGAGED = "engaged"             # 有互动（回复/点击）
    CONVERTED = "converted"         # 已转化（成交）
    ARCHIVED = "archived"           # 已归档
    INVALID = "invalid"             # 无效（退回/投诉）


class ProspectLead(Base):
    """统一线索模型 —— 所有渠道的单一真相来源"""
    __tablename__ = "prospect_leads"
    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ── 去重键 ──
    # 去重优先级 1：邮箱
    email = Column(String(255), nullable=True, index=True)
    email_domain = Column(String(255), nullable=True, index=True)
    # 去重优先级 2：LinkedIn
    linkedin_url = Column(String(500), nullable=True, index=True)
    linkedin_id = Column(String(64), nullable=True)
    # 去重优先级 3：电话
    phone = Column(String(50), nullable=True)
    # ── 公司信息 ──
    company_name = Column(String(255), nullable=True)
    company_name_normalized = Column(String(255), nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    website = Column(String(500), nullable=True)
    country = Column(String(8), nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    revenue_range = Column(String(50), nullable=True)
    # ── 联系人信息 ──
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    title = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True)
    # ── 来源与状态 ──
    source = Column(
        Enum(LeadSource, name="lead_source_enum"),
        nullable=False,
        default=LeadSource.GOOGLE_CSE,
    )
    source_detail = Column(JSON, default=dict)  # {search_keyword, page_url, scraped_at}
    status = Column(
        Enum(LeadStatus, name="lead_status_enum"),
        nullable=False,
        default=LeadStatus.DISCOVERED,
        index=True,
    )
    # ── 评分 ──
    fit_score = Column(Integer, nullable=False, default=50)  # 0-100 匹配度
    engagement_score = Column(Integer, nullable=False, default=0)  # 0-100 互动度
    overall_score = Column(Integer, nullable=False, default=0)  # 综合分
    # ── 4维评分子分（P1-4 新增）──
    score_match = Column(Integer, nullable=False, default=0)      # 匹配度（产品词+行业+国家）
    score_email = Column(Integer, nullable=False, default=0)      # 邮箱可信度
    score_evidence = Column(Integer, nullable=False, default=0)   # 证据完整度
    score_contact = Column(Integer, nullable=False, default=0)    # 联系人完整度
    # ── 证据链（P1-1 新增）──
    evidence_chain = Column(JSON, default=list)  # [{type, content, source_url, confidence, timestamp, details}]
    # ── 邮件追踪（P1-3 新增）──
    last_opened_at = Column(DateTime(timezone=True), nullable=True)
    open_count = Column(Integer, nullable=False, default=0)
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(Integer, nullable=False, default=0)
    last_replied_at = Column(DateTime(timezone=True), nullable=True)
    reply_count = Column(Integer, nullable=False, default=0)
    # ── 验证信息 ──
    email_verified = Column(String(20), nullable=True)  # valid / invalid / unknown / risky
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verified = Column(String(20), nullable=True)
    # ── 互动记录 ──
    contact_count = Column(Integer, nullable=False, default=0)
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    last_contacted_channel = Column(String(20), nullable=True)
    # ── 标签与备注 ──
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    # ── 归属 ──
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    assigned_to = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    created_by = Column(UUID_TYPE, ForeignKey("users.id"), nullable=True)
    # ── 元数据 ──
    merged_from = Column(JSON, default=list)  # 合并来源的线索 ID 列表
    is_duplicate = Column(String(64), nullable=True, index=True)  # 指向主线索 ID
    version = Column(Integer, nullable=False, default=1)
    lead_metadata = Column(JSON, default=dict)
    # ── 时间戳 ──
    created_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # ── 复合索引 ──
    __table_args__ = (
        # 邮箱 + 租户唯一（同一租户内邮箱不重复）
        UniqueConstraint("email", "tenant_id", name="uq_prospect_lead_email_tenant"),
        # LinkedIn + 租户唯一
        UniqueConstraint("linkedin_url", "tenant_id", name="uq_prospect_lead_linkedin_tenant"),
        # 域名 + 公司名 + 租户（辅助去重）
        Index("idx_prospect_lead_domain_company", "domain", "company_name_normalized"),
        # 状态 + 评分（查询常用组合）
        Index("idx_prospect_lead_status_score", "status", "overall_score"),
        # 租户 + 状态（列表查询）
        Index("idx_prospect_lead_tenant_status", "tenant_id", "status"),
        # 创建时间（排序）
        Index("idx_prospect_lead_created", "created_at"),
        # 评分范围约束
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_prospect_lead_overall_score"),
        CheckConstraint("score_match BETWEEN 0 AND 100", name="ck_prospect_lead_score_match"),
        CheckConstraint("score_email BETWEEN 0 AND 100", name="ck_prospect_lead_score_email"),
        CheckConstraint("score_evidence BETWEEN 0 AND 100", name="ck_prospect_lead_score_evidence"),
        CheckConstraint("score_contact BETWEEN 0 AND 100", name="ck_prospect_lead_score_contact"),
    )
    def compute_overall_score(self) -> int:
        """计算综合评分（4维加权）。"""
        # 如果有子分，用 4 维加权
        if any([self.score_match, self.score_email, self.score_evidence, self.score_contact]):
            score = int(
                self.score_match * 0.30 +
                self.score_email * 0.25 +
                self.score_evidence * 0.25 +
                self.score_contact * 0.20
            )
        else:
            # 兼容旧逻辑：fit_score 60% + engagement_score 40%
            score = int(self.fit_score * 0.6 + self.engagement_score * 0.4)

        # 邮箱验证加分
        if self.email_verified == "valid":
            score += 5
        elif self.email_verified == "invalid":
            score -= 10
        # 有电话加分
        if self.phone and self.phone_verified == "valid":
            score += 3
        # 追踪互动加分
        if self.open_count > 0:
            score += 2
        if self.reply_count > 0:
            score += 5
        return max(0, min(100, score))

    def compute_score_breakdown(self) -> dict:
        """返回 4 维评分明细，供前端雷达图使用。"""
        return {
            "match": self.score_match,
            "email": self.score_email,
            "evidence": self.score_evidence,
            "contact": self.score_contact,
            "overall": self.overall_score,
        }
