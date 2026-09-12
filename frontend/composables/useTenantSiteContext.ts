/**
 * 按当前 Host 从后端解析 tenant_id，供埋点与询盘归因（优先于静态 env）。
 */
export function useTenantSiteContext() {
  const config = useRuntimeConfig()
  const resolvedTenantId = useState<string | null>('resolvedTenantId', () => null)
  const resolvedMerchantId = useState<string | null>('resolvedMerchantId', () => null)
  const loading = useState('tenantContextLoading', () => false)

  async function ensureTenantContext() {
    if (!import.meta.client) return
    const envTid = (config.public.tenantId as string) || ''
    if (envTid) {
      resolvedTenantId.value = envTid
      resolvedMerchantId.value =
        (config.public.merchantId as string) || envTid
      return
    }
    if (resolvedTenantId.value || loading.value) return
    loading.value = true
    const apiBase = (config.public.apiBase as string) || '/api/v1'
    const host = window.location.host
    const merchantId = (config.public.merchantId as string) || ''
    try {
      const res = await $fetch<{
        data?: { tenant_id?: string; merchant_id?: string }
      }>(`${apiBase}/analytics/site-context`, {
        params: { host, merchant_id: merchantId || undefined },
      })
      const data = res?.data ?? (res as { tenant_id?: string })
      if (data?.tenant_id) {
        resolvedTenantId.value = data.tenant_id
        resolvedMerchantId.value = data.merchant_id || data.tenant_id
      }
    } catch {
      /* 无租户上下文时保持空，由 env 兜底 */
    } finally {
      loading.value = false
    }
  }

  function effectiveTenantId(): string {
    return (
      resolvedTenantId.value ||
      (config.public.tenantId as string) ||
      ''
    )
  }

  function effectiveMerchantId(): string {
    return (
      resolvedMerchantId.value ||
      (config.public.merchantId as string) ||
      effectiveTenantId() ||
      ''
    )
  }

  return {
    ensureTenantContext,
    effectiveTenantId,
    effectiveMerchantId,
    resolvedTenantId,
  }
}
