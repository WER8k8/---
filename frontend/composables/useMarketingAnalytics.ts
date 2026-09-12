/**
 * SaaS 营销页（/platform）埋点 — 漏斗与 CTA 归因
 */
const SESSION_KEY = 'uj_marketing_session_id';
const LANDING_KEY = 'uj_marketing_landing';
const LAST_CLICK_KEY = 'uj_marketing_last_click';
const AB_KEY = 'uj_platform_ab_hero';

function newSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 24);
  }
  return `m${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

export type PlatformAbVariant = 'a' | 'b';

export function useMarketingAnalytics() {
  const route = useRoute();
  const config = useRuntimeConfig();
  const sessionId = useState<string>('marketingSessionId', () => '');

  function ensureSession(): string {
    if (!import.meta.client) return '';
    if (!sessionId.value) {
      const stored = sessionStorage.getItem(SESSION_KEY);
      sessionId.value = stored || newSessionId();
      sessionStorage.setItem(SESSION_KEY, sessionId.value);
    }
    if (!sessionStorage.getItem(LANDING_KEY)) {
      sessionStorage.setItem(LANDING_KEY, route.fullPath || '/platform');
    }
    return sessionId.value;
  }

  function heroAbVariant(): PlatformAbVariant {
    if (!import.meta.client) return 'a';
    let v = sessionStorage.getItem(AB_KEY) as PlatformAbVariant | null;
    if (v !== 'a' && v !== 'b') {
      v = Math.random() < 0.5 ? 'a' : 'b';
      sessionStorage.setItem(AB_KEY, v);
    }
    return v;
  }

  async function track(eventType: string, extra: Record<string, unknown> = {}) {
    if (!import.meta.client) return;
    const sid = ensureSession();
    const apiBase = (config.public.apiBase as string) || '/api/v1';
    const body: Record<string, unknown> = {
      event_type: eventType,
      session_id: sid,
      page_path: route.fullPath || '/platform',
      page_title: typeof document !== 'undefined' ? document.title : '',
      merchant_id: (config.public.merchantId as string) || 'default',
      content_ref: `platform:${heroAbVariant()}`,
      ...extra,
    };
    if (eventType.includes('click') || eventType === 'cta_click') {
      const label = String(extra.element_label || '');
      if (label) sessionStorage.setItem(LAST_CLICK_KEY, label);
    }
    try {
      await $fetch(`${apiBase}/analytics/event`, { method: 'POST', body });
    } catch {
      /* silent */
    }
  }

  function trackPageView() {
    return track('page_view', { element_label: `ab:${heroAbVariant()}` });
  }

  function trackCta(label: string, target?: string) {
    return track('cta_click', { element_label: label, element_id: target || label });
  }

  function trackSection(sectionId: string) {
    return track('section_view', { element_label: sectionId });
  }

  return {
    ensureSession,
    heroAbVariant,
    track,
    trackPageView,
    trackCta,
    trackSection,
  };
}
