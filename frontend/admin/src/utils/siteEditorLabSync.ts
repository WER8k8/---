/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * site-editor-lab · Formily 草稿 ↔ 租户 site_content 双向映射
 * 对齐 L-Pro 发布门禁 + SITE-JTBD-01 四要素
 */
import { apiGet, getAuthToken } from '@/utils/api';
import type { SiteEditorDraft } from '@/api/admin-bff';

export type SiteEditorLabForm = SiteEditorDraft;

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

type StageRow = { stage?: string; title: string; description?: string };
type KnowledgeRow = { title: string; hook?: string };

function readStages(home: Record<string, unknown>): Partial<SiteEditorLabForm> {
  const raw = home.serviceStages;
  if (!Array.isArray(raw)) return {};
  const stages = raw.filter((s) => s && typeof s === 'object') as StageRow[];
  const out: Partial<SiteEditorLabForm> = {};
  const slots = [
    ['stage1Title', 'stage1Desc'],
    ['stage2Title', 'stage2Desc'],
    ['stage3Title', 'stage3Desc'],
    ['stage4Title', 'stage4Desc'],
  ] as const;
  slots.forEach(([titleKey, descKey], i) => {
    const row = stages[i];
    if (!row) return;
    out[titleKey] = String(row.title || '');
    out[descKey] = String(row.description || '');
  });
  return out;
}

function readKnowledge(home: Record<string, unknown>): Partial<SiteEditorLabForm> {
  const raw = home.knowledgeTopics;
  if (!Array.isArray(raw)) return {};
  const topics = raw.filter((k) => k && typeof k === 'object') as KnowledgeRow[];
  const out: Partial<SiteEditorLabForm> = {};
  const slots = [
    ['knowledge1Title', 'knowledge1Hook'],
    ['knowledge2Title', 'knowledge2Hook'],
    ['knowledge3Title', 'knowledge3Hook'],
  ] as const;
  slots.forEach(([titleKey, hookKey], i) => {
    const row = topics[i];
    if (!row) return;
    out[titleKey] = String(row.title || '');
    out[hookKey] = String(row.hook || '');
  });
  return out;
}

function writeStages(draft: SiteEditorLabForm): StageRow[] {
  const slots = [
    { title: draft.stage1Title, desc: draft.stage1Desc, stage: '01' },
    { title: draft.stage2Title, desc: draft.stage2Desc, stage: '02' },
    { title: draft.stage3Title, desc: draft.stage3Desc, stage: '03' },
    { title: draft.stage4Title, desc: draft.stage4Desc, stage: '04' },
  ];
  return slots
    .filter((s) => String(s.title || '').trim())
    .map((s) => ({
      stage: s.stage,
      title: String(s.title).trim(),
      description: String(s.desc || '').trim() || undefined,
    }));
}

function writeKnowledge(draft: SiteEditorLabForm): KnowledgeRow[] {
  const slots = [
    { title: draft.knowledge1Title, hook: draft.knowledge1Hook },
    { title: draft.knowledge2Title, hook: draft.knowledge2Hook },
    { title: draft.knowledge3Title, hook: draft.knowledge3Hook },
  ];
  return slots
    .filter((s) => String(s.title || '').trim())
    .map((s) => ({
      title: String(s.title).trim(),
      hook: String(s.hook || '').trim() || undefined,
    }));
}

export function draftFromSiteContent(siteContent: Record<string, unknown>): Partial<SiteEditorLabForm> {
  const brand = asRecord(siteContent.brand);
  const pages = asRecord(siteContent.pages);
  const home = asRecord(pages.home);
  const about = asRecord(pages.about);
  const contact = asRecord(pages.contact);

  return {
    title: String(home.title || brand.name || ''),
    hero: String(home.description || ''),
    brandName: String(brand.name || ''),
    aboutText: String(about.aboutText || ''),
    contactPhone: String(contact.phone || ''),
    contactEmail: String(contact.email || ''),
    ctaLabel: String(home.ctaPrimary || '立即询盘'),
    primaryPromise: String(home.primary_promise || brand.tagline || ''),
    inquiryHook: String(home.inquiryHook || ''),
    locale: String(siteContent.locale || 'zh-CN'),
    showCta: home.ctaPrimary !== false && home.showCta !== false,
    ...readStages(home),
    ...readKnowledge(home),
  };
}

export function mergeDraftIntoSiteContent(
  siteContent: Record<string, unknown>,
  draft: SiteEditorLabForm,
): Record<string, unknown> {
  const next = { ...siteContent };
  const brand = { ...asRecord(next.brand) };
  const pages = { ...asRecord(next.pages) };
  const home = { ...asRecord(pages.home) };
  const about = { ...asRecord(pages.about) };
  const contact = { ...asRecord(pages.contact) };

  if (draft.brandName?.trim()) {
    brand.name = draft.brandName.trim();
  }
  if (draft.title?.trim()) {
    home.title = draft.title.trim();
    if (!brand.name) brand.name = draft.title.trim();
  }
  if (draft.hero?.trim()) {
    home.description = draft.hero.trim();
  }
  if (draft.aboutText?.trim()) {
    about.aboutText = draft.aboutText.trim();
  }
  if (draft.contactPhone?.trim()) {
    contact.phone = draft.contactPhone.trim();
  }
  if (draft.contactEmail?.trim()) {
    contact.email = draft.contactEmail.trim();
  }
  if (draft.ctaLabel?.trim() && draft.showCta !== false) {
    home.ctaPrimary = draft.ctaLabel.trim();
  }
  if (draft.primaryPromise?.trim()) {
    home.primary_promise = draft.primaryPromise.trim();
    brand.tagline = draft.primaryPromise.trim();
  }
  if (draft.inquiryHook?.trim()) {
    home.inquiryHook = draft.inquiryHook.trim();
  }
  const stages = writeStages(draft);
  if (stages.length) home.serviceStages = stages;
  const knowledge = writeKnowledge(draft);
  if (knowledge.length) home.knowledgeTopics = knowledge;
  if (draft.locale?.trim()) {
    next.locale = draft.locale.trim();
  }

  next.templateId = next.templateId || 'premium-b2b-v1';
  next.templateTier = next.templateTier || 'L-Pro';
  next.brand = brand;
  next.pages = { ...pages, home, about, contact };

  return next;
}

function parseSettings(raw: unknown): Record<string, unknown> {
  if (!raw) return {};
  if (typeof raw === 'string') {
    try {
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
    } catch {
      return {};
    }
  }
  return typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
}

export async function loadTenantSiteContent(): Promise<Record<string, unknown>> {
  const res = await fetch('/api/v1/tenants/current', {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  });
  const body = await res.json();
  if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
    throw new Error(typeof body.message === 'string' ? body.message : '无法加载站点内容');
  }
  const data = body.data || body;
  const tenant = data.tenant || data;
  const settings = parseSettings(tenant.settings);
  const brand = asRecord(settings.brand);
  return asRecord(brand.site_content);
}

export async function saveTenantSiteContent(siteContent: Record<string, unknown>): Promise<void> {
  const res = await fetch('/api/v1/tenants/self', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify({
      settings: JSON.stringify({
        brand: { site_content: siteContent },
      }),
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.message === 'string' ? body.message : '保存官网失败');
  }
}

export async function refreshOnboardingPreviewUrl(): Promise<{ dev?: string; prod?: string }> {
  const status = await apiGet<{
    site_preview_dev_url?: string;
    site_preview_url?: string;
  }>('/tenants/self/onboarding-status');
  return {
    dev: status?.site_preview_dev_url,
    prod: status?.site_preview_url,
  };
}
