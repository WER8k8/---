/** 与 backend site_content_locale_service._merge_i18n_block 对齐 */

export function mergeSiteI18nBlock(
  page: Record<string, unknown> | null | undefined,
  language: string,
): Record<string, unknown> {
  if (!page || typeof page !== 'object') return {};
  const out = { ...page };
  const i18n = page.i18n as Record<string, Record<string, unknown>> | undefined;
  if (!i18n || typeof i18n !== 'object') return out;

  let overlay = i18n[language];
  if (!overlay || typeof overlay !== 'object') {
    overlay = language !== 'en' ? i18n.en : undefined;
  }
  if (!overlay || typeof overlay !== 'object') return out;

  for (const [key, value] of Object.entries(overlay)) {
    if (key === 'i18n') continue;
    if (value === null || value === undefined) continue;
    if (typeof value === 'string' && !value.trim()) continue;
    if (Array.isArray(value) && value.length === 0) continue;
    if (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0) continue;
    out[key] = value;
  }
  return out;
}

export function localizedSiteString(
  siteContent: Record<string, unknown> | null | undefined,
  overlaySlice: Record<string, unknown> | undefined,
  blockKey: 'brand' | 'home' | 'about' | 'products',
  field: string,
  language: string,
  fallbacks: string[] = [],
): string {
  const fromOverlay = overlaySlice?.[field];
  if (typeof fromOverlay === 'string' && fromOverlay.trim()) return fromOverlay.trim();

  const root = siteContent && typeof siteContent === 'object' ? siteContent : {};
  let block: Record<string, unknown> | undefined;
  if (blockKey === 'brand') {
    block = root.brand as Record<string, unknown> | undefined;
  } else {
    const pages = root.pages as Record<string, unknown> | undefined;
    block = pages?.[blockKey] as Record<string, unknown> | undefined;
  }

  const merged = mergeSiteI18nBlock(block, language);
  const primary = merged[field];
  if (typeof primary === 'string' && primary.trim()) return primary.trim();

  if (language !== 'en') {
    const enMerged = mergeSiteI18nBlock(block, 'en');
    const enVal = enMerged[field];
    if (typeof enVal === 'string' && enVal.trim()) return enVal.trim();
  }

  for (const fb of fallbacks) {
    if (fb?.trim()) return fb.trim();
  }
  return '';
}
