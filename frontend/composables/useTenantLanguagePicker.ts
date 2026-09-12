/** L-Pro 租户站 · Tier1 核心语 + Tier2 扩展语 */

export interface TenantLanguageOption {
  code: string;
  name: string;
}

/** 与 backend im_locale_service.SUPPORTED_LANGUAGES 对齐 */
export const TIER1_LANGUAGES: TenantLanguageOption[] = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'ar', name: 'العربية' },
  { code: 'es', name: 'Español' },
  { code: 'pt', name: 'Português' },
  { code: 'ru', name: 'Русский' },
  { code: 'th', name: 'ไทย' },
  { code: 'vi', name: 'Tiếng Việt' },
  { code: 'id', name: 'Bahasa Indonesia' },
  { code: 'ms', name: 'Bahasa Melayu' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
];

/** Tier2：自动翻译外链（仅营销文案，规格以英文/源语言为准） */
export const TIER2_LANGUAGES: TenantLanguageOption[] = [
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'it', name: 'Italiano' },
  { code: 'nl', name: 'Nederlands' },
  { code: 'pl', name: 'Polski' },
  { code: 'tr', name: 'Türkçe' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'fa', name: 'فارسی' },
  { code: 'he', name: 'עברית' },
  { code: 'uk', name: 'Українська' },
  { code: 'fil', name: 'Filipino' },
];

export function tenantLanguageStorageKey(domain: string): string {
  return `youding-tenant-lang:${domain}`;
}

export function readStoredTenantLanguage(domain: string): string | null {
  if (!import.meta.client || !domain) return null;
  try {
    return localStorage.getItem(tenantLanguageStorageKey(domain)) || null;
  } catch {
    return null;
  }
}

export function writeStoredTenantLanguage(domain: string, code: string): void {
  if (!import.meta.client || !domain) return;
  try {
    localStorage.setItem(tenantLanguageStorageKey(domain), code);
  } catch {
    /* ignore */
  }
}

export function googleTranslatePageUrl(targetLang: string, pageUrl?: string): string {
  const url = encodeURIComponent(pageUrl || (typeof window !== 'undefined' ? window.location.href : ''));
  return `https://translate.google.com/translate?hl=${encodeURIComponent(targetLang)}&sl=auto&tl=${encodeURIComponent(targetLang)}&u=${url}`;
}
