/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * UBrain 销售模块 API
 */

import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import type {
  Customer,
  CustomerFilters,
  SearchCriteria,
  Negotiation,
  QuoteForm,
  Email,
  EmailCampaign,
  EmailTemplate,
} from '@/types/sales';

// ==================== 客户开发 ====================

/**
 * 搜索客户
 */
export function searchCustomers(data: SearchCriteria) {
  return apiPost<{
    customers: Customer[];
    total_found: number;
  }>('/super-agent/sales/customer-finder', data);
}

/**
 * 获取客户详情
 */
export function getCustomerDetail(customerId: string) {
  return apiGet<Customer>(`/super-agent/sales/customer-finder/${customerId}`);
}

/**
 * 更新客户状态
 */
export function updateCustomerStatus(customerId: string, status: string) {
  return apiPut(`/super-agent/sales/customer-finder/${customerId}/status`, { status });
}

/**
 * 导出客户列表
 */
export function exportCustomers(customerIds: string[]) {
  return apiPost('/super-agent/sales/customer-finder/export', { customerIds });
}

// ==================== 自动谈单 ====================

/**
 * 处理询盘
 */
export function processInquiry(data: {
  customer_name: string;
  customer_email: string;
  products: Array<{ name: string; cost: number }>;
  quantity: number;
  destination: string;
  urgency?: string;
  previous_messages?: Array<{ role: string; content: string }>;
}) {
  return apiPost('/super-agent/sales/auto-negotiator', {
    action: 'process_inquiry',
    ...data,
  });
}

/**
 * 生成报价
 */
export function generateQuote(data: QuoteForm) {
  return apiPost('/super-agent/sales/auto-negotiator', {
    action: 'generate_quote',
    ...data,
  });
}

/**
 * 获取谈判列表
 */
export function getNegotiations(params?: {
  status?: string;
  limit?: number;
}) {
  return apiGet<{
    negotiations: Negotiation[];
    total: number;
  }>('/super-agent/sales/negotiations', params);
}

/**
 * 发送谈判消息
 */
export function sendNegotiationMessage(sessionId: string, message: string) {
  return apiPost(`/super-agent/sales/negotiations/${sessionId}/messages`, { message });
}

/**
 * 审批报价
 */
export function approveNegotiation(sessionId: string) {
  return apiPost(`/super-agent/sales/negotiations/${sessionId}/approve`);
}

// ==================== 开发信管理 ====================

/**
 * 生成开发信
 */
export function generateEmail(data: {
  customer_data: Record<string, any>;
  email_type: string;
  language: string;
}) {
  return apiPost<{
    email_id: string;
    subject: string;
    body: string;
  }>('/super-agent/sales/email-automation', {
    action: 'generate_email',
    ...data,
  });
}

/**
 * 创建邮件活动
 */
export function createCampaign(data: {
  campaign_name: string;
  customer_list: Array<Record<string, any>>;
  email_type: string;
  language: string;
}) {
  return apiPost<{
    campaign_id: string;
    name: string;
    total_emails: number;
  }>('/super-agent/sales/email-automation', {
    action: 'create_campaign',
    ...data,
  });
}

/**
 * 获取活动列表
 */
export function getCampaigns(params?: { limit?: number }) {
  return apiGet<{
    campaigns: EmailCampaign[];
    total: number;
  }>('/super-agent/sales/campaigns', params);
}

/**
 * 获取活动统计
 */
export function getCampaignStats(campaignId: string) {
  return apiGet(`/super-agent/sales/campaigns/${campaignId}/stats`);
}

/**
 * 暂停活动
 */
export function pauseCampaign(campaignId: string) {
  return apiPost(`/super-agent/sales/campaigns/${campaignId}/pause`);
}

/**
 * 继续活动
 */
export function resumeCampaign(campaignId: string) {
  return apiPost(`/super-agent/sales/campaigns/${campaignId}/resume`);
}

/**
 * 获取邮件列表
 */
export function getEmails(params?: {
  status?: string;
  type?: string;
  limit?: number;
  offset?: number;
}) {
  return apiGet<{
    emails: Email[];
    total: number;
  }>('/super-agent/sales/emails', params);
}

/**
 * 获取邮件详情
 */
export function getEmailDetail(emailId: string) {
  return apiGet<Email>(`/super-agent/sales/emails/${emailId}`);
}

/**
 * 重发邮件
 */
export function resendEmail(emailId: string) {
  return apiPost(`/super-agent/sales/emails/${emailId}/resend`);
}

/**
 * 获取邮件模板列表
 */
export function getEmailTemplates(params?: {
  type?: string;
  language?: string;
}) {
  return apiGet<EmailTemplate[]>('/super-agent/sales/templates', params);
}

/**
 * 创建邮件模板
 */
export function createEmailTemplate(data: Partial<EmailTemplate>) {
  return apiPost<EmailTemplate>('/super-agent/sales/templates', data);
}

/**
 * 更新邮件模板
 */
export function updateEmailTemplate(templateId: string, data: Partial<EmailTemplate>) {
  return apiPut<EmailTemplate>(`/super-agent/sales/templates/${templateId}`, data);
}

/**
 * 删除邮件模板
 */
export function deleteEmailTemplate(templateId: string) {
  return apiDelete(`/super-agent/sales/templates/${templateId}`);
}

// ==================== 销售仪表板 ====================

/**
 * 获取销售指标
 */
export function getSalesMetrics(params?: {
  start_date?: string;
  end_date?: string;
}) {
  return apiGet('/super-agent/sales/dashboard/metrics', params);
}

/**
 * 获取销售漏斗数据
 */
export function getSalesFunnel(params?: {
  start_date?: string;
  end_date?: string;
}) {
  return apiGet('/super-agent/sales/dashboard/funnel', params);
}

/**
 * 获取销售趋势
 */
export function getSalesTrend(params?: {
  type: 'revenue' | 'customers' | 'inquiries';
  start_date?: string;
  end_date?: string;
}) {
  return apiGet('/super-agent/sales/dashboard/trend', params);
}

/**
 * 获取地区分布
 */
export function getRegionDistribution() {
  return apiGet('/super-agent/sales/dashboard/regions');
}
