/** 租户独立站 · 可收录 URL（?language=）与 hreflang（en / zh / ru） */

export const TENANT_SEO_HREFLANG_LOCALES = [
  { code: 'en', hreflang: 'en' },
  { code: 'zh', hreflang: 'zh-CN' },
  { code: 'ru', hreflang: 'ru' },
] as const;

export type TenantSeoPrimaryMarket = 'export' | 'domestic' | 'russia';

/** 各市场默认站长平台（建站 SEO 面板展示用） */
export const TENANT_SEO_WEBMASTER_HINTS: Record<
  TenantSeoPrimaryMarket,
  { label: string; url: string; langParam: string }
> = {
  export: {
    label: 'Google Search Console',
    url: 'https://search.google.com/search-console',
    langParam: 'en',
  },
  domestic: {
    label: '百度站长平台',
    url: 'https://ziyuan.baidu.com/',
    langParam: 'zh',
  },
  russia: {
    label: 'Yandex Webmaster',
    url: 'https://webmaster.yandex.ru/',
    langParam: 'ru',
  },
};

const PRESERVED_QUERY_KEYS = ['__tenant', 'lpro'] as const;

export function preservedTenantPreviewQuery(
  query: Record<string, unknown> | undefined | null,
): Record<string, string> {
  const out: Record<string, string> = {};
  if (!query) return out;
  for (const key of PRESERVED_QUERY_KEYS) {
    const raw = query[key];
    if (typeof raw === 'string' && raw.trim()) out[key] = raw.trim();
  }
  return out;
}

export function buildTenantLanguagePath(
  path: string,
  language: string,
  extraQuery?: Record<string, string>,
): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  const params = new URLSearchParams();
  if (extraQuery) {
    for (const [k, v] of Object.entries(extraQuery)) {
      if (v) params.set(k, v);
    }
  }
  params.set('language', language.slice(0, 5));
  const qs = params.toString();
  return qs ? `${normalized}?${qs}` : normalized;
}

export function buildTenantLanguageUrl(
  origin: string,
  path: string,
  language: string,
  extraQuery?: Record<string, string>,
): string {
  const base = origin.replace(/\/$/, '');
  return `${base}${buildTenantLanguagePath(path, language, extraQuery)}`;
}

export function resolveTenantSeoPrimaryMarket(
  siteContent: Record<string, unknown> | null | undefined,
): TenantSeoPrimaryMarket {
  const seo = siteContent?.seo;
  if (!seo || typeof seo !== 'object') return 'export';
  const raw = (seo as { primaryMarket?: string }).primaryMarket;
  if (raw === 'domestic') return 'domestic';
  if (raw === 'russia') return 'russia';
  return 'export';
}

export function resolveTenantSeoXDefaultLanguage(market: TenantSeoPrimaryMarket): string {
  if (market === 'domestic') return 'zh';
  if (market === 'russia') return 'ru';
  return 'en';
}
