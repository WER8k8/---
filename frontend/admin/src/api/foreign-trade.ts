/**
 * 外贸标杆能力 API — OSINT / ICP / PI / 询盘 / 发布人审 / 专家团队
 */

import { apiGet, apiPost, apiPut, authHeaders, getAuthToken } from '@/utils/api';

export type AgentEnvelope<T = Record<string, unknown>> = {
  skill_id?: string;
  status?: string;
  summary?: string;
  data?: T;
  next_actions?: string[];
  human_review_required?: boolean;
};

export type B2bExpert = {
  id: string;
  name: string;
  name_en?: string;
  emoji?: string;
  tagline?: string;
  skills?: string[];
  must_show?: string[];
  out_of_scope?: string[];
};

export type PreflightResult = {
  ok?: boolean;
  blocked?: boolean;
  checklist_required?: string[];
  checklist_missing?: string[];
  content_risks?: Array<{ code: string; message: string }>;
  message?: string;
};

const API_BASE = '/api/v1';

export function osintCheck(target: string) {
  return apiPost<AgentEnvelope>('/foreign-trade/osint/check', { target });
}

export function websiteIcpProfile(websiteUrl: string, tenantId?: string) {
  return apiPost<AgentEnvelope>('/foreign-trade/website/icp-profile', {
    website_url: websiteUrl,
    tenant_id: tenantId,
    max_pages: 5,
  });
}

export function proformaInvoice(payload: Record<string, unknown>) {
  return apiPost<AgentEnvelope>('/foreign-trade/documents/proforma-invoice', payload);
}

export function inquiryOsint(inquiryId: string) {
  return apiPost<AgentEnvelope>(`/foreign-trade/inquiries/${encodeURIComponent(inquiryId)}/osint`, {});
}

export function inquiryMeddpicc(inquiryId: string) {
  return apiGet<Record<string, unknown>>(`/foreign-trade/inquiries/${encodeURIComponent(inquiryId)}/meddpicc`);
}

export function inquiryProforma(inquiryId: string) {
  return apiPost<AgentEnvelope>(
    `/foreign-trade/inquiries/${encodeURIComponent(inquiryId)}/proforma-invoice`,
    {},
  );
}

export function publishPreflight(contentMasterId: string, checklist: Record<string, boolean>) {
  return apiPost<PreflightResult>('/foreign-trade/publish/preflight', {
    content_master_id: contentMasterId,
    checklist,
    force: false,
  });
}

export function fetchB2bExperts() {
  return apiGet<{
    experts: B2bExpert[];
    platform_note?: string;
    catalog_version?: string;
    total?: number;
  }>('/foreign-trade/ecosystem/experts');
}

export function downloadMarkdown(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  triggerDownload(filename, blob);
}

export async function exportProformaFile(
  payload: Record<string, unknown>,
  fmt: 'docx' | 'html' | 'markdown' | 'pdf' = 'docx',
) {
  const token = getAuthToken();
  const res = await fetch(
    `${API_BASE}/foreign-trade/documents/proforma-invoice/export?fmt=${fmt}`,
    {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { message?: string }).message || `导出失败 HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const ext = fmt === 'docx' ? 'docx' : fmt === 'html' ? 'html' : fmt === 'pdf' ? 'pdf' : 'md';
  const cd = res.headers.get('Content-Disposition') || '';
  const match = cd.match(/filename="([^"]+)"/);
  triggerDownload(match?.[1] || `PI.${ext}`, blob);
}

export function saveContentMasterPreflight(masterId: string, checklist: Record<string, boolean>) {
  return apiPut<{ preflight_checklist?: Record<string, boolean> }>(
    `/content-masters/${encodeURIComponent(masterId)}`,
    { preflight_checklist: checklist },
  );
}

function triggerDownload(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export type SidecarHealth = {
  configured?: boolean;
  healthy?: boolean | null;
  url?: string | null;
  detail?: string | null;
  compliance?: string;
};

export function foreignTradeSidecarsStatus() {
  return apiGet<Record<string, SidecarHealth>>('/foreign-trade/integrations/sidecars/status');
}

export function linkedinDecisionMakers(payload: {
  company: string;
  domain?: string;
  industry?: string;
  purpose: string;
  tenant_consent: boolean;
  compliance_acknowledged: boolean;
  max_results?: number;
}) {
  return apiPost<Record<string, unknown>>('/foreign-trade/integrations/linkedin/decision-makers', payload);
}

export function customsBuyerBrief(params: {
  product: string;
  hs_code?: string;
  country_code?: string;
  include_sidecar?: boolean;
}) {
  const q = new URLSearchParams({ product: params.product });
  if (params.hs_code) q.set('hs_code', params.hs_code);
  if (params.country_code) q.set('country_code', params.country_code);
  if (params.include_sidecar) q.set('include_sidecar', 'true');
  return apiGet<Record<string, unknown>>(`/foreign-trade/trade-intel/customs-buyer-brief?${q}`);
}

export function customsBuyerResearch(payload: {
  product: string;
  hs_code?: string;
  country_code?: string;
  purpose: string;
  tenant_consent: boolean;
  compliance_acknowledged: boolean;
  max_results?: number;
}) {
  return apiPost<Record<string, unknown>>('/foreign-trade/integrations/customs/buyer-research', payload);
}

export async function exportInquiryProformaFile(
  inquiryId: string,
  fmt: 'docx' | 'html' | 'pdf' = 'docx',
) {
  const env = await inquiryProforma(inquiryId);
  const doc = (env.data || {}) as Record<string, unknown>;
  await exportProformaFile(
    {
      seller: doc.seller || { name: 'Seller', address: '', email: '' },
      buyer: doc.buyer || {
        name: 'Buyer',
        company: 'Buyer Co',
        email: '',
        code: inquiryId.slice(0, 8).toUpperCase(),
      },
      lines: doc.lines || [{ description: 'Product', quantity: 100, unit_price: 0 }],
      currency: doc.currency || 'USD',
      payment_terms: doc.payment_terms || '30% deposit, 70% before shipment',
      delivery_terms: doc.delivery_terms || 'FOB',
    },
    fmt,
  );
}
