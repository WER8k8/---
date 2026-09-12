/**
 * L-Pro 租户站 SEO：<title> / description / keywords + canonical + hreflang（en/zh/ru）
 * Google 英文 · 百度中文 · Yandex 俄语 — 各语言独立 URL（?language=）与独立 meta。
 */

import { computed, type ComputedRef, type Ref, unref, type MaybeRef } from 'vue';
import type { TenantLProNavKey } from './useTenantLProNav';
import {
  buildTenantLanguageUrl,
  preservedTenantPreviewQuery,
  resolveTenantSeoPrimaryMarket,
  resolveTenantSeoXDefaultLanguage,
  TENANT_SEO_HREFLANG_LOCALES,
  type TenantSeoPrimaryMarket,
} from '../utils/tenant-seo-url';

export interface TenantLProSeoHeadInput {
  activeKey: MaybeRef<TenantLProNavKey>;
  language: ComputedRef<string>;
  companyName: ComputedRef<string>;
  seoBaseTitle: ComputedRef<string>;
  localizedSeoDescription: ComputedRef<string>;
  localizedSeoKeywords: ComputedRef<string>;
  seoRobotsContent: ComputedRef<string>;
  siteContent: ComputedRef<Record<string, unknown> | null>;
  documentTitle?: string;
  documentDescription?: string;
  tSite: (key: string, vars?: Record<string, string>) => string;
}

export function useTenantLProSeoHead(input: TenantLProSeoHeadInput) {
  const route = useRoute();
  const config = useRuntimeConfig();
  const requestHeaders = import.meta.server
    ? useRequestHeaders(['host', 'x-forwarded-proto'])
    : null;

  const primaryMarket = computed<TenantSeoPrimaryMarket>(() =>
    resolveTenantSeoPrimaryMarket(input.siteContent.value),
  );

  const previewQuery = computed(() => preservedTenantPreviewQuery(route.query as Record<string, unknown>));

  const siteOrigin = computed(() => {
    if (import.meta.client && typeof window !== 'undefined') {
      return window.location.origin;
    }
    const host = requestHeaders?.host;
    if (host) {
      const proto = (requestHeaders?.['x-forwarded-proto'] as string) || 'https';
      return `${proto}://${host}`;
    }
    const fromConfig = (config.public.siteUrl as string) || '';
    return fromConfig.replace(/\/$/, '');
  });

  const seoPageTitle = computed(() => {
    const custom = input.documentTitle?.trim();
    if (custom) return `${custom} | ${input.companyName.value}`;

    const base = input.seoBaseTitle.value;
    const key = unref(input.activeKey);
    switch (key) {
      case 'products':
        return `${input.tSite('section_products_default')} | ${base}`;
      case 'about':
        return `${input.tSite('section_about', { name: input.companyName.value })} | ${base}`;
      case 'contact':
        return `${input.tSite('section_contact')} | ${base}`;
      case 'solutions':
        return `${input.tSite('section_solutions')} | ${base}`;
      case 'downloads':
        return `${input.tSite('nav_downloads')} | ${base}`;
      default:
        return base;
    }
  });

  const seoPageDescription = computed(() => {
    const custom = input.documentDescription?.trim();
    if (custom) return custom.slice(0, 160);
    const localized = input.localizedSeoDescription.value.trim();
    if (localized) return localized.slice(0, 160);
    return input.companyName.value;
  });

  const seoPageKeywords = computed(() => input.localizedSeoKeywords.value.trim());

  const canonicalUrl = computed(() =>
    buildTenantLanguageUrl(
      siteOrigin.value,
      route.path,
      input.language.value,
      previewQuery.value,
    ),
  );

  const hreflangLinks = computed(() => {
    const links: Array<{ rel: string; hreflang?: string; href: string }> = [];
    for (const { code, hreflang } of TENANT_SEO_HREFLANG_LOCALES) {
      links.push({
        rel: 'alternate',
        hreflang,
        href: buildTenantLanguageUrl(siteOrigin.value, route.path, code, previewQuery.value),
      });
    }
    const xDefaultLang = resolveTenantSeoXDefaultLanguage(primaryMarket.value);
    links.push({
      rel: 'alternate',
      hreflang: 'x-default',
      href: buildTenantLanguageUrl(siteOrigin.value, route.path, xDefaultLang, previewQuery.value),
    });
    return links;
  });

  useHead(() => ({
    title: seoPageTitle.value,
    htmlAttrs: {
      lang: input.language.value,
      dir: input.language.value === 'ar' ? 'rtl' : 'ltr',
    },
    meta: [
      { name: 'description', content: seoPageDescription.value },
      ...(seoPageKeywords.value ? [{ name: 'keywords', content: seoPageKeywords.value }] : []),
      { name: 'robots', content: input.seoRobotsContent.value },
      { property: 'og:title', content: seoPageTitle.value },
      { property: 'og:description', content: seoPageDescription.value },
      { property: 'og:url', content: canonicalUrl.value },
      { property: 'og:type', content: 'website' },
      { property: 'og:site_name', content: input.companyName.value },
      { property: 'og:image', content: `${siteOrigin.value}/images/og-default.jpg` },
      { property: 'og:locale', content: input.language.value === 'zh' ? 'zh_CN' : 'en_US' },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: seoPageTitle.value },
      { name: 'twitter:description', content: seoPageDescription.value },
    ],
    link: [
      { rel: 'canonical', href: canonicalUrl.value },
      ...hreflangLinks.value,
    ],
  }));

  return {
    seoPageTitle,
    seoPageDescription,
    canonicalUrl,
    siteOrigin,
  };
}
