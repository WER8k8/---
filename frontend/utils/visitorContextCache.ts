/** 租户站 visitor-context 客户端缓存 — 生产切换语言秒开、断网可用 */

import type { VisitorContext } from '../composables/useVisitorLocale';

const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

type CachedPayload = {
  ts: number;
  ctx: VisitorContext;
};

export function visitorContextCacheKey(domain: string, language?: string): string {
  const lang = (language || '').trim().toLowerCase().slice(0, 5);
  return lang ? `visitor_context:${domain}:${lang}` : `visitor_context:${domain}`;
}

function readRaw(key: string): VisitorContext | null {
  if (!import.meta.client) return null;
  try {
    const raw = sessionStorage.getItem(key) || localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CachedPayload | VisitorContext;
    if (parsed && typeof parsed === 'object' && 'ctx' in parsed && 'ts' in parsed) {
      const wrapped = parsed as CachedPayload;
      if (Date.now() - wrapped.ts > CACHE_TTL_MS) return null;
      return wrapped.ctx;
    }
    const legacy = parsed as VisitorContext;
    if (legacy?.country_code && legacy?.language) return legacy;
    return null;
  } catch {
    return null;
  }
}

export function readCachedVisitorContext(domain: string, language?: string): VisitorContext | null {
  if (!domain) return null;
  const candidates = [language].filter((v): v is string => Boolean(v && v.trim()));
  for (const lang of candidates) {
    const hit = readRaw(visitorContextCacheKey(domain, lang));
    if (hit) return hit;
  }
  return readRaw(visitorContextCacheKey(domain));
}

export function writeCachedVisitorContext(domain: string, ctx: VisitorContext): void {
  if (!import.meta.client || !domain) return;
  const lang = (ctx.language || '').trim().toLowerCase();
  if (!lang) return;
  const key = visitorContextCacheKey(domain, lang);
  const payload: CachedPayload = { ts: Date.now(), ctx };
  const serialized = JSON.stringify(payload);
  try {
    sessionStorage.setItem(key, serialized);
    localStorage.setItem(key, serialized);
  } catch {
    /* quota */
  }
}
