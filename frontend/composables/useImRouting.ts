/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** P1-01：统一 IM 路由（/im-routing/channels 与 /mobile/im-routing 同源） */

export type ImChannel = {
  channel_type: string
  account_id: string
  prefilled_text?: string
  im_link?: string
  display_text?: string
}

export function useImRouting() {
  const config = useRuntimeConfig()
  const route = useRoute()
  const { locale } = useI18n()

  const merchantId = computed(() => {
    const fromQuery = route.query.merchant_id
    if (fromQuery) return String(fromQuery)
    const pub = config.public.merchantId as string | undefined
    return pub || 'default'
  })

  const countryCode = computed(() => {
    const q = route.query.country as string | undefined
    if (q) return q.toUpperCase().slice(0, 2)
    if (import.meta.client) {
      const stored = localStorage.getItem('buyer_country')
      if (stored) return stored.toUpperCase().slice(0, 2)
    }
    return 'US'
  })

  async function fetchChannels(): Promise<ImChannel[]> {
    const apiBase = (config.public.apiBase as string) || '/api/v1'
    const params = {
      merchant_id: merchantId.value,
      country_code: countryCode.value,
      language: locale.value,
    }
    try {
      const res = await $fetch<{ data?: { channels?: ImChannel[] } }>(
        `${apiBase}/mobile/im-routing`,
        { params },
      )
      const data = res?.data ?? (res as { channels?: ImChannel[] })
      const list = data?.channels || []
      if (list.length) return list
    } catch {
      /* fallback */
    }
    try {
      const res = await $fetch<{ data?: { channels?: ImChannel[] } }>(
        `${apiBase}/im-routing/channels`,
        {
          params: {
            merchant_id: Number(mid) || 1,
            country_code: countryCode.value,
            language: locale.value,
          },
        },
      )
      return res?.data?.channels || []
    } catch {
      // P1-01：API 不可用时勿注入假渠道，StickyImBar 保持隐藏
      return []
    }
  }

  return { merchantId, countryCode, fetchChannels }
}
