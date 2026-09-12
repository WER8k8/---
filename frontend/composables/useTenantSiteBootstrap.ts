/** 租户独立站 · 共享加载与 L-Pro 模式检测 */

import { computed } from 'vue';
import { useRoute, useRuntimeConfig, useState } from 'nuxt/app';
import { useApiRoot } from './useApiBase';
import { resolveTenantDomainFromRoute, useVisitorLocale } from './useVisitorLocale';
import {
  categorySlug,
  normalizeCatalogProducts,
  type TenantCatalogProduct,
} from '../utils/tenant-product-slug';

export interface TenantSiteBrand {
  site_title: string;
  logo_url: string;
  brand_colors: { primary: string; secondary: string; accent: string };
  product_categories: string[];
  company_name: string;
  slogan: string;
  about_summary: string;
  contact_phone: string;
  contact_email: string;
  footer_text: string;
  custom_css: string;
  site_content?: Record<string, unknown> | null;
}

export interface TenantSiteInfo {
  id: string;
  name: string;
  domain: string;
  status: string;
  plan_code: string | null;
  brand: TenantSiteBrand;
  is_online: boolean;
}

function siteContentOf(tenant: TenantSiteInfo | null): Record<string, unknown> | null {
  const sc = tenant?.brand?.site_content;
  return sc && typeof sc === 'object' ? sc : null;
}

export function isLProSiteContent(siteContent: Record<string, unknown> | null | undefined): boolean {
  if (!siteContent) return false;
  if (siteContent.templateTier === 'L-Pro') return true;
  const visual = siteContent.visualEditor as Record<string, unknown> | undefined;
  const tid = visual?.templateId || siteContent.templateId;
  return tid === 'premium-b2b-v1';
}

export function useTenantSiteBootstrap(apiBase = '/api/v1') {
  const tenant = useState<TenantSiteInfo | null>('youding-tenant-site', () => null);
  const loading = useState('youding-tenant-site-loading', () => true);
  const error = useState<string | null>('youding-tenant-site-error', () => null);
  const booted = useState('youding-tenant-site-booted', () => false);

  const route = useRoute();
  const config = useRuntimeConfig();
  const { apiUrl } = useApiRoot();
  const resolvedApiBase = () => apiBase || (config.public.apiBase as string) || '/api/v1';

  const domainRef = computed(() => tenant.value?.domain || resolveTenantDomainFromRoute() || '');

  const visitor = useVisitorLocale(() => domainRef.value, resolvedApiBase);
  const { loading: localeLoading, ...visitorRest } = visitor;

  const siteContent = computed(() => siteContentOf(tenant.value));
  const pages = computed(() => (siteContent.value?.pages as Record<string, Record<string, unknown>>) || {});
  const homePage = computed(() => pages.value.home || {});
  const productsPage = computed(() => pages.value.products || {});
  const aboutPage = computed(() => pages.value.about || {});
  const contactPage = computed(() => pages.value.contact || {});
  const downloadsPage = computed(() => pages.value.downloads || {});

  const lProMode = computed(() => {
    if (route.query.lpro === '1') return true;
    return isLProSiteContent(siteContent.value);
  });

  const catalogProducts = computed<TenantCatalogProduct[]>(() => {
    const fromItems = normalizeCatalogProducts(productsPage.value.productItems);
    if (fromItems.length) return fromItems;
    const names = productsPage.value.products;
    if (Array.isArray(names)) {
      return normalizeCatalogProducts(
        names.map((n: unknown) => ({ name: String(n), summary: tenant.value?.brand.company_name })),
      );
    }
    const legacy = tenant.value?.brand.product_categories || [];
    return normalizeCatalogProducts(
      legacy.map((n: string) => ({ name: n, summary: tenant.value?.brand.company_name })),
    );
  });

  const localizedCatalogProducts = computed<TenantCatalogProduct[]>(() => {
    const overlayItems = visitor.context.value?.site_content_localized?.products?.productItems;
    if (Array.isArray(overlayItems) && overlayItems.length) {
      return normalizeCatalogProducts(overlayItems);
    }
    return catalogProducts.value;
  });

  const categoryFilters = computed(() => {
    const fromHome = (homePage.value.categories as Array<{ name?: string }>) || [];
    const names = new Set<string>();
    for (const c of fromHome) {
      if (c?.name) names.add(String(c.name));
    }
    for (const p of catalogProducts.value) {
      if (p.category) names.add(p.category);
    }
    return [...names].map((name) => ({ name, slug: categorySlug(name) }));
  });

  async function ensureLoaded() {
    if (booted.value && tenant.value) return;
    loading.value = true;
    error.value = null;
    const sub = resolveTenantDomainFromRoute();
    if (!sub) {
      loading.value = false;
      error.value = visitor.tSite('tenant_not_found');
      return;
    }
    try {
      const localeTask = visitor.fetchVisitorContext(undefined, sub);
      const res = await fetch(apiUrl(`/tenants/domain/${encodeURIComponent(sub)}`));
      const body = await res.json();
      if (!res.ok || (body.code !== undefined && body.code !== 0)) {
        throw new Error(body.message || visitor.tSite('load_failed'));
      }
      tenant.value = (body.data || body) as TenantSiteInfo;
      await localeTask;
      booted.value = true;
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : visitor.tSite('load_failed');
    } finally {
      loading.value = false;
    }
  }

  return {
    tenant,
    loading,
    localeLoading,
    error,
    ensureLoaded,
    lProMode,
    siteContent,
    pages,
    homePage,
    productsPage,
    aboutPage,
    contactPage,
    downloadsPage,
    catalogProducts,
    localizedCatalogProducts,
    categoryFilters,
    ...visitorRest,
    apiBase: resolvedApiBase(),
  };
}
