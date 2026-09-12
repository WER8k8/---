import { resolveTenantPreviewDomain } from '../utils/tenant-preview-domain'

/**
 * 租户域名检测中间件
 *
 * 服务端 + 客户端:
 *   - 读取 Host，若非主站域名则写入 useState('tenantHost')
 *
 * 客户端额外逻辑:
 *   - 子域名 xxx.youding-saas.com 重定向到 /tenant
 *   - __tenant 查询参数模拟租户访问
 */

const MAIN_SITE_PATTERNS = [
  /^(www\.)?youding-saas\.com$/,
  /^(www\.)?youding\.com$/,
  /^(www\.)?youdingjiancai\.com$/,
  /^localhost$/,
  /^127\.0\.0\.1$/,
]

function normalizeHost(raw: string): string {
  return raw.split(':')[0].trim().toLowerCase()
}

function isMainSiteHost(host: string, saasPrimaryDomain: string): boolean {
  const escaped = saasPrimaryDomain.replace(/\./g, '\\.')
  const dynamic = new RegExp(`^(www\\.)?${escaped}$`)
  return MAIN_SITE_PATTERNS.some((p) => p.test(host)) || dynamic.test(host)
}

function resolveRequestHost(): string | null {
  if (import.meta.server) {
    const headers = useRequestHeaders(['host'])
    const raw = headers.host
    return raw ? normalizeHost(raw) : null
  }
  if (import.meta.client) {
    return normalizeHost(window.location.hostname)
  }
  return null
}

export default defineNuxtRouteMiddleware((to) => {
  const config = useRuntimeConfig()
  const saasPrimaryDomain = (config.public.saasPrimaryDomain as string) || 'youding-saas.com'
  const host = resolveRequestHost()

  const previewDomain = resolveTenantPreviewDomain(
    to.query as Record<string, unknown>,
    import.meta.client && typeof window !== 'undefined' ? window.location.search : '',
  )
  if (previewDomain && to.path.startsWith('/tenant') && to.query.__tenant !== previewDomain) {
    const query = Object.fromEntries(
      Object.entries(to.query).filter(([key]) => key !== '__tenant' && !key.startsWith('__tenant=')),
    )
    return navigateTo({
      path: to.path,
      query: { ...query, __tenant: previewDomain },
      replace: true,
    })
  }

  if (host && !isMainSiteHost(host, saasPrimaryDomain)) {
    const tenantHost = useState<string | null>('tenantHost', () => null)
    tenantHost.value = host
  }

  if (import.meta.client) {
    const saasMatch = host?.match(/^([a-z0-9][a-z0-9-]+)\.(youding-saas)\.com$/)
    const youdingMatch = host?.match(/^([a-z0-9][a-z0-9-]+)\.(youding)\.com$/)

    if (saasMatch || youdingMatch) {
      if (!to.path.startsWith('/tenant')) {
        return navigateTo({
          path: '/tenant',
          query: { ...to.query },
          replace: true,
        })
      }
    }

    if (previewDomain && !to.path.startsWith('/tenant')) {
      return navigateTo({
        path: '/tenant',
        query: { __tenant: previewDomain, ...to.query },
        replace: true,
      })
    }
  }
})
