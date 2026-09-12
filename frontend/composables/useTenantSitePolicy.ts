/** P1-05：租户独立站隐藏总站友链 */
import { SITE_CONFIG } from '~/config/site'

export function useTenantSitePolicy() {
  const config = useRuntimeConfig()
  const hideHubBacklink = useState('hideHubBacklink', () => false)

  async function load() {
    if (!import.meta.client) return
    const mainHost = new URL(
      (config.public.siteUrl as string) || SITE_CONFIG.url,
    ).hostname
    const current = window.location.hostname
    if (current === mainHost || current === 'localhost') {
      hideHubBacklink.value = false
      return
    }
    const apiBase = (config.public.apiBase as string) || '/api/v1'
    try {
      const res = await $fetch<{
        data?: { hide_hub_backlink?: boolean }
      }>(`${apiBase}/mobile/site-policy`, {
        params: { host: current, tenant_domain: current.split('.')[0] },
      })
      hideHubBacklink.value = Boolean(res?.data?.hide_hub_backlink)
    } catch {
      hideHubBacklink.value = true
    }
  }

  return { hideHubBacklink, load }
}
