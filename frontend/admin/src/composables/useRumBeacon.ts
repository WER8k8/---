/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 浏览器 RUM 信标 — Admin 壳上报 Core Web Vitals */
import { onMounted } from 'vue'
import { authHeaders } from '@/utils/api'

function sendBeacon(payload: Record<string, unknown>) {
  const body = JSON.stringify(payload)
  const url = '/api/v1/analytics/rum'
  void fetch(url, {
    method: 'POST',
    keepalive: true,
    headers: authHeaders(),
    body,
  }).catch(() => {})
}

export function useRumBeacon() {
  onMounted(() => {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return

    let lcp = 0
    let inp = 0
    let cls = 0

    try {
      const po = new PerformanceObserver((list) => {
        for (const e of list.getEntries()) {
          if (e.entryType === 'largest-contentful-paint') {
            lcp = Math.max(lcp, e.startTime)
          }
          if (e.entryType === 'layout-shift' && !(e as PerformanceEntry & { hadRecentInput?: boolean }).hadRecentInput) {
            cls += (e as PerformanceEntry & { value?: number }).value || 0
          }
          if (e.entryType === 'event' && (e as PerformanceEntry & { interactionId?: number }).interactionId) {
            const d = (e as PerformanceEntry & { duration?: number }).duration || 0
            inp = Math.max(inp, d)
          }
        }
      })
      po.observe({ type: 'largest-contentful-paint', buffered: true })
      po.observe({ type: 'layout-shift', buffered: true })
      po.observe({ type: 'event', buffered: true, durationThreshold: 16 } as PerformanceObserverInit)
    } catch {
      /* unsupported */
    }

    const flush = () => {
      if (lcp <= 0 && inp <= 0 && cls <= 0) return
      sendBeacon({
        lcp_ms: lcp ? Math.round(lcp) : undefined,
        inp_ms: inp ? Math.round(inp) : undefined,
        cls: cls ? Math.round(cls * 1000) / 1000 : undefined,
        page_path: window.location.pathname,
      })
    }

    window.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') flush()
    })
    setTimeout(flush, 8000)
  })
}
