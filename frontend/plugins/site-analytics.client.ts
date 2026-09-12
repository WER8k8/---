/** 路由切换时自动上报 page_view */
export default defineNuxtPlugin(() => {
  const router = useRouter()
  const { trackPageView, ensureSession } = useSiteAnalytics()
  const { ensureTenantContext } = useTenantSiteContext()

  if (import.meta.client) {
    void ensureTenantContext()
    ensureSession()
    trackPageView()
    router.afterEach(() => {
      trackPageView()
    })
    const { track } = useSiteAnalytics()
    document.addEventListener(
      'click',
      (ev) => {
        const el = (ev.target as HTMLElement | null)?.closest?.('a[href^="tel:"]')
        if (!el) return
        const href = el.getAttribute('href') || 'phone'
        void track('phone_click', { element_label: href, element_id: href })
      },
      true,
    )
  }
})
