/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import type { SiteContentSnapshot, SiteSeoFields } from './types';

function i18nHomeOverlay(snapshot: SiteContentSnapshot, lang: string): Record<string, unknown> {
  const home = snapshot.pages?.home;
  if (!home || typeof home !== 'object') return {};
  const i18n = home.i18n;
  if (!i18n || typeof i18n !== 'object') return {};
  const block = (i18n as Record<string, unknown>)[lang];
  return block && typeof block === 'object' ? (block as Record<string, unknown>) : {};
}

function resolvePrimaryMarket(raw: string | undefined): SiteSeoFields['seoPrimaryMarket'] {
  if (raw === 'domestic') return 'domestic';
  if (raw === 'russia') return 'russia';
  return 'export';
}

/** 从 site_content 快照提取 SEO 表单字段（Google 英 + 百度中 + Yandex 俄） */
export function snapshotToSeo(snapshot: SiteContentSnapshot): SiteSeoFields {
  const home = (snapshot.pages?.home || {}) as Record<string, unknown>;
  const zh = i18nHomeOverlay(snapshot, 'zh');
  const ru = i18nHomeOverlay(snapshot, 'ru');
  const seoMeta = snapshot.seo;
  return {
    pageTitle: String(home.title || snapshot.brand?.name || ''),
    seoDescription: String(home.seoDescription || home.description || ''),
    seoKeywords: String(home.seoKeywords || ''),
    domesticPageTitle: String(zh.title || ''),
    domesticSeoDescription: String(zh.seoDescription || zh.description || ''),
    domesticSeoKeywords: String(zh.seoKeywords || ''),
    russianPageTitle: String(ru.title || ''),
    russianSeoDescription: String(ru.seoDescription || ru.description || ''),
    russianSeoKeywords: String(ru.seoKeywords || ''),
    allowIndex: home.robotsNoIndex !== true,
    seoPrimaryMarket: resolvePrimaryMarket(seoMeta?.primaryMarket),
  };
}

function applyI18nSeoBlock(
  i18n: Record<string, unknown>,
  lang: string,
  title: string,
  description: string,
  keywords: string,
): void {
  const block = { ...(i18n[lang] as Record<string, unknown> | undefined) };
  if (title.trim()) block.title = title.trim();
  if (description.trim()) block.seoDescription = description.trim();
  if (keywords.trim()) block.seoKeywords = keywords.trim();
  if (Object.keys(block).length) i18n[lang] = block;
}

/** SEO 表单写回 site_content（英文基字段 + zh/ru i18n + seo.primaryMarket） */
export function applySeoToSnapshot(snapshot: SiteContentSnapshot, seo: SiteSeoFields): SiteContentSnapshot {
  const home = { ...(snapshot.pages?.home || {}) } as Record<string, unknown>;
  home.title = seo.pageTitle;
  home.seoDescription = seo.seoDescription;
  home.seoKeywords = seo.seoKeywords;
  home.robotsNoIndex = !seo.allowIndex;

  const i18n = { ...(home.i18n as Record<string, unknown> | undefined) };
  applyI18nSeoBlock(
    i18n,
    'zh',
    seo.domesticPageTitle,
    seo.domesticSeoDescription,
    seo.domesticSeoKeywords,
  );
  applyI18nSeoBlock(
    i18n,
    'ru',
    seo.russianPageTitle,
    seo.russianSeoDescription,
    seo.russianSeoKeywords,
  );
  if (Object.keys(i18n).length) home.i18n = i18n;

  return {
    ...snapshot,
    seo: { primaryMarket: seo.seoPrimaryMarket },
    pages: {
      ...snapshot.pages,
      home,
    },
  };
}
