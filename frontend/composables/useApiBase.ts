/** SSR/浏览器统一的 API 根路径 */
export function useApiRoot() {
  const config = useRuntimeConfig()
  const apiHost = String(config.public.apiHost || 'http://localhost:8000').replace(/\/$/, '')
  const apiBase = String(config.public.apiBase || '/api/v1').replace(/\/$/, '')

  const root = computed(() => {
    if (import.meta.client) {
      return apiBase.startsWith('http') ? apiBase : apiBase
    }
    return `${apiHost}${apiBase.startsWith('/') ? apiBase : `/${apiBase}`}`
  })

  function apiUrl(path: string) {
    const p = path.startsWith('/') ? path : `/${path}`
    const base = root.value.replace(/\/$/, '')
    if (base.startsWith('http')) {
      return `${base}${p}`
    }
    return `${base}${p}`
  }

  return { apiUrl, apiHost, apiBase }
}
