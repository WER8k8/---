# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
from app.core.database import Base
from app.models.agent_tree import AgentNode
from app.models.admin import (AdminMenu, AdminPermission, AdminRole,
                              LoginLog, RolePermission)
from app.models.alert import AlertEvent, AlertRule
from app.models.ab_test import (ABTest, ABTestConversion, ABTestEvent,
                                ABTestVariant)
from app.models.media_factory import MediaRenderTask
from app.models.ai_config import (AIModelConfig, AIModelProvider, AIUsageLog, TenantAiProviderConfig,
                                   CCSwitchConfig)
from app.models.commission_settlement import AgentCommissionSettlement
from app.models.case_study import CaseImage, CaseStudy
from app.models.compliance import (AdvertisementLawKeyword, ComplianceRule,
                                   ComplianceScanResult, ComplianceViolation)
from app.models.content_master import ContentMaster
from app.models.email_outreach import EmailOutreach
from app.models.egress import BrowserProfile, EgressCostRecord, EgressEndpoint, EgressPoolReplenishJob
from app.models.evolution import (ApprovalRecord, CanaryRouteRecord,
                                  EvolutionTaskRecord, ExperienceEntry,
                                  SkillVersion, SOPVersion)
from app.models.deerflow_job import DeerflowJob
from app.models.n8n_workflow import N8nWorkflow
from app.models.finance_ledger import FinanceLedgerEntry
from app.models.content import (AIGenerationConfig, ContentPage,
                                ContentTemplate, ContentVersion,
                                GeneratedContent, InclusionStatus, Platform,
                                PlatformAccount, PlatformConfig, PublishLog,
                                PublishTask, RiskControlConfig,
                                SystemSetting)
from app.models.eeat import (ArticleAuthor, Author, AuthorCertification,
                             EEATScore, TrustSignal)
from app.models.feishu import FeishuBinding, FeishuMessageLog
from app.models.globalization import (GlossaryTerm, TranslationTask,
                                       TranslationRecord)
from app.models.growth_tools import GrowthAgentRun, GrowthKeywordEntry
from app.models.international import (InternationalCrawlLog,
                                       InternationalInquiry,
                                       InternationalTargetSite)
from app.models.inquiry import Inquiry
from app.models.domestic import DomesticInquiry
from app.models.social_interaction import SocialInteraction
from app.models.push_event import PushEvent
from app.models.tenant_wecom_push import TenantWecomPushConfig
from app.models.news import NewsArticle, NewsCategory
from app.models.notification import Notification
from app.models.product import Category, Product, ProductDocument
from app.models.tenant import Tenant, TenantInvoice, TenantPlan, TenantSubscription, UserTenant
from app.models.payment import PaymentChannel, PaymentOpsAudit, PaymentOrder, PaymentCompensationTask
from app.models.referral import ReferralCode, ReferralRecord
from app.models.region import (City, CombinatorialRule, District,
                               GeneratedKeyword, GroupKeyword, IndustryKeyword,
                               KeywordGroup, Province)
from app.models.schema_markup import SchemaMarkup, SchemaTemplate
from app.models.seo import (AiOptimizationLog, Keyword, KeywordRanking,
                            LlmsConfig, SiteAudit)
from app.models.user import OperationLog, User
from app.models.geo_sourcechain_models import (MaterialSpec, ContentChunk, SERPSnapshot,
                                 LeadInquiry, ReleaseGuard)
from app.models.geo_alert_db_models import (GEOAlertRule, GEOAlert, GEOAlertHistory)
from app.models.im_routing_and_specs import MerchantIMRouting, BuildingMaterialSpec
from app.models.merchant_profile import MerchantProfile
from app.models.quote import Quote
from app.models.quote import Quote, QuoteItem
from app.models.rfq import RFQ, RFQDocument, RFQItem, RFQRequirement
from app.models.opportunity import Opportunity, OpportunityStage
from app.models.company import Company, CompanyContact, CompanySignal, IntentEngineRun
from app.models.project import Project, ProjectSignal
from app.models.campaign import Campaign, CampaignEvent, CampaignRecipient, CampaignStep
from app.models.ai_visibility import AICitation, AIMention, AIQuery, AIQueryRun, CompetitorMention, VisibilityScore
from app.models.sales_task import SalesTask
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_category import ProductCategory
from app.models.product_image import ProductImage
from app.models.seo_metadata import SEOMetadata, SeoMetadata
from app.models.ai_recommendation import AIRecommendation
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.wangcai import WangcaiQaLog, WangcaiSession
from app.models.im_chat import IMMessage, IMSession, UserStatus
from app.models.system_config import SystemConfig
from app.models.review import Review
from app.models.shipping_timeline import ShippingTimeline, InquiryExtended
from app.models.ai_knowledge import AiChatSession, AiChatMessage, AiKnowledgeBase
from app.models.deerflow_job import DeerflowJob
from app.models.hermes_plugin import HermesPluginInstall
from app.models.ubrain_accio import BuyerProspectLead, UbrainTenantMemory
from app.models.ubrain_commercial_os import (
    UbrainActionAudit,
    UbrainFeedbackSnapshot,
    UbrainPipelineRun,
    UbrainResearchInsight,
)
from app.models.ubrain_decision import (
    UBrainDecisionRecord,
    UBrainExecutionRecord,
    UBrainFeedbackRecord,
)
from app.models.ssl_certificate import SSLCertificate
from app.models.site_analytics import SiteAnalyticsEvent
from app.models.platform_survival_ledger import PlatformSurvivalLedgerEntry
from app.models.content_feedback import ContentFeedbackCheck, IndustryPattern
from app.models.license import License, DeviceFingerprint, LicenseCode, LicenseOrder
from app.models.token_ledger import TokenLedgerEntry
from app.models.email_tracking_event import EmailTrackingEvent
from app.models.prospect_lead import ProspectLead
from app.models.registry import (
    DataSourceProvider,
    McpServer,
    McpTool,
    RegistryPlugin,
    RegistryPluginVersion,
    RegistrySkill,
    RegistrySkillVersion,
    TenantCapabilityToggle,
)
from app.models.trace import AgentScorecard, SkillPerformance, TaskTrace
from app.models.meter import MeterEvent
from app.models.ai_task import AiTask
from app.models.wallet import WalletAccount, WalletTransaction
from app.models.trade_fulfillment import (
    BusinessPayment,
    ContactEvent,
    ExperienceRecord,
    Invoice,
    KnowledgeBase,
    LogisticsShipment,
    Pipeline,
    PurchaseOrder,
    WhatsappMessage,
)

__all__ = [
    "Base", "AgentNode",
    "AdminRole",
    "AdminPermission",
    "RolePermission",
    "AdminMenu",
    "LoginLog",
    "AIModelProvider",
    "AIModelConfig",
    "AIUsageLog",
    "CCSwitchConfig",
    "AgentCommissionSettlement",
    "EmailOutreach",
    "TokenLedgerEntry",
    "WalletAccount",
    "WalletTransaction",
    "AlertRule",
    "AlertEvent",
    "User",
    "OperationLog",
    "Category",
    "Product",
    "ProductDocument",
    "ProspectLead",
    "ContentMaster",
    "EgressEndpoint",
    "EgressCostRecord",
    "EgressPoolReplenishJob",
    "BrowserProfile",
    "FinanceLedgerEntry",
    "ContentTemplate",
    "ContentVersion",
    "GeneratedContent",
    "Platform",
    "PlatformAccount",
    "PlatformConfig",
    "PublishTask",
    "PublishLog",
    "InclusionStatus",
    "SystemSetting",
    "AIGenerationConfig",
    "RiskControlConfig",
    "Keyword",
    "KeywordRanking",
    "SiteAudit",
    "AiOptimizationLog",
    "LlmsConfig",
    "GlossaryTerm",
    "TranslationTask",
    "TranslationRecord",
    "InternationalTargetSite",
    "InternationalInquiry",
    "InternationalCrawlLog",
    "Inquiry",
    "SocialInteraction",
    "CaseStudy",
    "CaseImage",
    "SchemaMarkup",
    "SchemaTemplate",
    "Author",
    "AuthorCertification",
    "ArticleAuthor",
    "EEATScore",
    "TrustSignal",
    "ComplianceRule",
    "ComplianceScanResult",
    "ComplianceViolation",
    "AdvertisementLawKeyword",
    "ABTest",
    "ABTestVariant",
    "ABTestEvent",
    "ABTestConversion",
    "FeishuBinding",
    "FeishuMessageLog",
    "Province",
    "City",
    "District",
    "IndustryKeyword",
    "KeywordGroup",
    "GroupKeyword",
    "CombinatorialRule",
    "GeneratedKeyword",
    "GrowthKeywordEntry",
    "GrowthAgentRun",
    "NewsArticle",
    "NewsCategory",
    "Notification",
    "PaymentOrder",
    "PaymentChannel",
    "PaymentOpsAudit",
    "TenantPlan",
    "Tenant",
    "TenantSubscription",
    "TenantInvoice",
    "UserTenant",
    "ReferralCode",
    "ReferralRecord",
    "MaterialSpec",
    "ContentChunk",
    "SERPSnapshot",
    "LeadInquiry",
    "ReleaseGuard",
    "GEOAlertRule",
    "GEOAlert",
    "GEOAlertHistory",
    "MerchantIMRouting",
    "BuildingMaterialSpec",
    "MerchantProfile",
    "Quote",
    "QuoteItem",
    "RFQ",
    "RFQItem",
    "RFQRequirement",
    "RFQDocument",
    "Opportunity",
    "OpportunityStage",
    "Company",
    "CompanyContact",
    "CompanySignal",
    "IntentEngineRun",
    "Project",
    "ProjectSignal",
    "Campaign",
    "CampaignStep",
    "CampaignRecipient",
    "CampaignEvent",
    "AIQuery",
    "AIQueryRun",
    "AIMention",
    "AICitation",
    "CompetitorMention",
    "VisibilityScore",
    "SalesTask",
    "Order",
    "OrderItem",
    "ProductCategory",
    "ProductImage",
    "SEOMetadata",
    "SeoMetadata",
    "AIRecommendation",
    "ChatSession",
    "ChatMessage",
    "WangcaiSession",
    "WangcaiQaLog",
    "IMMessage",
    "IMSession",
    "UserStatus",
    "SystemConfig",
    "Review",
    "ShippingTimeline",
    "InquiryExtended",
    "AiChatSession",
    "AiChatMessage",
    "AiKnowledgeBase",
    "SSLCertificate",
    "SiteAnalyticsEvent",
    "PlatformSurvivalLedgerEntry",
    "ContentFeedbackCheck",
    "IndustryPattern",
    "UBrainDecisionRecord",
    "UBrainExecutionRecord",
    "UBrainFeedbackRecord",
    "RegistrySkill",
    "RegistrySkillVersion",
    "McpServer",
    "McpTool",
    "RegistryPlugin",
    "RegistryPluginVersion",
    "DataSourceProvider",
    "TenantCapabilityToggle",
    "TaskTrace",
    "MeterEvent",
    "AiTask",
    "SkillPerformance",
    "AgentScorecard",
    "PurchaseOrder",
    "LogisticsShipment",
    "WhatsappMessage",
    "ExperienceRecord",
    "ContactEvent",
    "KnowledgeBase",
    "Invoice",
    "BusinessPayment",
    "Pipeline",
    "DomesticInquiry",
]
