/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 销售模块类型定义
 */

// ==================== 客户相关 ====================

/** 客户状态 */
export type CustomerStatus = 'new' | 'contacted' | 'qualified' | 'converted';

/** 客户信息 */
export interface Customer {
  id: string;
  name: string;
  company: string;
  email: string;
  phone?: string;
  whatsappNumber?: string;
  website?: string;
  country: string;
  industry: string;
  score: number;
  status: CustomerStatus;
  lastContact: string;
  notes?: string;
  evidenceUrl?: string;
  emailEnrichment?: string;
  // 评分明细
  keywordScore?: number;
  countryScore?: number;
  industryScore?: number;
  contactScore?: number;
  sizeScore?: number;
  // 联系历史
  contactHistory?: ContactHistory[];
}

/** 联系历史 */
export interface ContactHistory {
  id: string;
  type: 'email' | 'call' | 'meeting' | 'website_visit';
  title: string;
  description?: string;
  timestamp: string;
}

/** 客户筛选条件 */
export interface CustomerFilters {
  keywords: string[];
  countries: string[];
  minScore: number;
  status?: CustomerStatus;
  industry?: string;
}

/** 搜索条件 */
export interface SearchCriteria {
  keywords: string[];
  countries: string[];
  industry?: string;
  maxResults: number;
  searchSource?: string;
  customerType?: string;
}

// ==================== 谈判相关 ====================

/** 谈判状态 */
export type NegotiationStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

/** 消息发送者 */
export type MessageSender = 'customer' | 'ai' | 'user';

/** 报价信息 */
export interface Quote {
  unitPrice: number;
  totalPrice: number;
  deliveryTime: string;
  validUntil: string;
}

/** 消息 */
export interface Message {
  id: string;
  sender: MessageSender;
  content: string;
  timestamp: string;
  quote?: Quote;
}

/** 谈判记录 */
export interface Negotiation {
  id: string;
  customerName: string;
  customerEmail: string;
  product: string;
  quantity: number;
  unit: string;
  destination: string;
  status: NegotiationStatus;
  round: number;
  unread: number;
  lastMessage: string;
  updatedAt: string;
  messages: Message[];
}

/** 报价表单 */
export interface QuoteForm {
  productName: string;
  quantity: number;
  baseCost: number;
  profitMargin: number;
  deliveryTime: string;
  paymentTerms: string;
}

/** 谈判设置 */
export interface NegotiationSettings {
  baseProfitMargin: number;
  maxRounds: number;
  autoReply: boolean;
  requireApproval: boolean;
  workingHours: any;
}

// ==================== 邮件相关 ====================

/** 邮件类型 */
export type EmailType = 'cold_outreach' | 'follow_up' | 'quote' | 'welcome' | 'marketing' | 'thanks';

/** 邮件状态 */
export type EmailStatus = 'draft' | 'scheduled' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'replied' | 'failed';

/** 邮件 */
export interface Email {
  id: string;
  recipientName: string;
  recipientEmail: string;
  subject: string;
  body?: string;
  type: EmailType;
  status: EmailStatus;
  sentAt?: string;
  openedAt?: string;
  clickedAt?: string;
  repliedAt?: string;
  openCount?: number;
  clickCount?: number;
}

/** 邮件活动状态 */
export type CampaignStatus = 'draft' | 'active' | 'paused' | 'completed';

/** 邮件活动 */
export interface EmailCampaign {
  id: string;
  name: string;
  total: number;
  sent: number;
  status: CampaignStatus;
  openRate: number;
  replyRate: number;
  createdAt: string;
}

/** 邮件模板 */
export interface EmailTemplate {
  id: string;
  name: string;
  description: string;
  language: string;
  type: EmailType;
  usageCount: number;
  isDefault: boolean;
  color: string;
  content?: string;
}

// ==================== 销售仪表板 ====================

/** 销售指标 */
export interface SalesMetrics {
  totalCustomers: number;
  customerGrowth: number;
  newCustomers: number;
  newCustomerGrowth: number;
  revenue: number;
  revenueGrowth: number;
  conversionRate: number;
  conversionGrowth: number;
  inquiries: number;
  inquiryGrowth: number;
  emailsSent: number;
  emailGrowth: number;
}

/** 漏斗阶段 */
export interface FunnelStage {
  name: string;
  count: number;
  percentage: number;
  rate: number;
  color: string;
}

/** 技能统计 */
export interface SkillStats {
  name: string;
  icon: string;
  usage: number;
  usageRate: number;
  effectiveness: number;
  color: string;
}

/** 地区统计 */
export interface RegionStats {
  name: string;
  flag: string;
  customers: number;
  percentage: number;
  revenue: number;
}
