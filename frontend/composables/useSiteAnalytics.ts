/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 租户站流量埋点：会话 ID、页面浏览、点击归因（供询盘提交携带）。
 */
const SESSION_KEY = 'uj_site_session_id'
const LANDING_KEY = 'uj_landing_path'
const LAST_CLICK_KEY = 'uj_last_click_label'

function newSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, '').slice(0, 24)
  }
  return `s${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`
}

export function useSiteAnalytics() {
  const route = useRoute()
  const config = useRuntimeConfig()
  const { ensureTenantContext, effectiveTenantId, effectiveMerchantId } =
    useTenantSiteContext()

  const sessionId = useState<string>('siteSessionId', () => '')

  function ensureSession(): string {
    if (!import.meta.client) return ''
    if (!sessionId.value) {
      const stored = sessionStorage.getItem(SESSION_KEY)
      sessionId.value = stored || newSessionId()
      sessionStorage.setItem(SESSION_KEY, sessionId.value)
    }
    if (!sessionStorage.getItem(LANDING_KEY)) {
      sessionStorage.setItem(LANDING_KEY, route.fullPath || '/')
    }
    return sessionId.value
  }

  function getLandingPath(): string {
    if (!import.meta.client) return route.fullPath || '/'
    return sessionStorage.getItem(LANDING_KEY) || route.fullPath || '/'
  }

  function getLastClickLabel(): string {
    if (!import.meta.client) return ''
    return sessionStorage.getItem(LAST_CLICK_KEY) || ''
  }

  async function track(
    eventType: string,
    extra: Record<string, unknown> = {},
  ) {
    if (!import.meta.client) return
    await ensureTenantContext()
    const sid = ensureSession()
    const apiBase = (config.public.apiBase as string) || '/api/v1'
    const body: Record<string, unknown> = {
      event_type: eventType,
      session_id: sid,
      page_path: route.fullPath || '/',
      page_title: typeof document !== 'undefined' ? document.title : '',
      merchant_id: effectiveMerchantId(),
      tenant_id: effectiveTenantId(),
      agent_node_id: (config.public.agentNodeId as string) || '',
      product_id: route.params.id || '',
      content_ref: route.params.slug
        ? `slug:${route.params.slug}`
        : route.params.id
          ? `product:${route.params.id}`
          : route.path,
      ...extra,
    }
    if (eventType.includes('click') || eventType === 'form_open') {
      const label = String(extra.element_label || extra.element_id || '')
      if (label) sessionStorage.setItem(LAST_CLICK_KEY, label)
    }
    try {
      await $fetch(`${apiBase}/analytics/event`, { method: 'POST', body })
    } catch {
      /* silent */
    }
  }

  function trackPageView() {
    return track('page_view')
  }

  function trackClick(label: string, elementId?: string) {
    return track('link_click', {
      element_label: label,
      element_id: elementId || label,
    })
  }

  function attributionPayload() {
    return {
      session_id: ensureSession(),
      landing_path: getLandingPath(),
      last_click_label: getLastClickLabel(),
      tenant_id: effectiveTenantId() || undefined,
    }
  }

  return {
    ensureSession,
    track,
    trackPageView,
    trackClick,
    attributionPayload,
    getLandingPath,
    getLastClickLabel,
  }
}
