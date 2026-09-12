/** 解析开发预览租户域：?__tenant=dev.local（兼容错误编码 ?__tenant%3Ddev.local） */

export function readTenantFromQueryRecord(query: Record<string, unknown>): string | null {
  const direct = query.__tenant
  if (typeof direct === 'string' && direct.trim()) {
    return direct.trim().toLowerCase()
  }
  if (Array.isArray(direct)) {
    const first = direct.find((v) => typeof v === 'string' && v.trim())
    if (typeof first === 'string') return first.trim().toLowerCase()
  }
  for (const key of Object.keys(query)) {
    if (key.startsWith('__tenant=')) {
      const domain = key.slice('__tenant='.length).trim()
      if (domain) return domain.toLowerCase()
    }
  }
  return null
}

export function readTenantFromSearch(search: string): string | null {
  const m = search.match(/[?&]__tenant(?:=|%3D)([^&]+)/i)
  if (!m?.[1]) return null
  try {
    return decodeURIComponent(m[1]).trim().toLowerCase()
  } catch {
    return m[1].trim().toLowerCase()
  }
}

export function resolveTenantPreviewDomain(
  query: Record<string, unknown>,
  search = '',
): string | null {
  return readTenantFromQueryRecord(query) || readTenantFromSearch(search) || null
}

/** 本地 / 生产租户站预览 URL（Admin「我的网站」、建站编辑器「预览网站」） */
export function resolveDevTenantPreviewHost(): string {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname?.trim()
    if (host && host !== 'localhost') return host
  }
  return '127.0.0.1'
}

/** 本地 / 生产租户站预览 URL（Admin 建站编辑器「预览网站」） */
export function buildTenantPreviewUrl(
  domain: string,
  opts?: { host?: string; lpro?: boolean },
): string {
  const raw = String(domain || '').replace(/^https?:\/\//, '').trim()
  if (!raw) return ''

  const tenantKey = raw.includes('/') ? raw.split('/')[0] : raw
  const isDev = Boolean(import.meta.env?.DEV)

  if (isDev) {
    const host = opts?.host || resolveDevTenantPreviewHost()
    const params = new URLSearchParams({ __tenant: tenantKey })
    if (opts?.lpro !== false) params.set('lpro', '1')
    return `http://${host}:3000/tenant?${params.toString()}`
  }

  if (tenantKey.includes('.') && !tenantKey.endsWith('.youding-saas.com')) {
    return `https://${tenantKey}`
  }
  const bare = tenantKey.replace(/\.youding-saas\.com$/i, '')
  const primary =
    (import.meta.env?.VITE_SAAS_PRIMARY_DOMAIN as string | undefined) || 'youding-saas.com'
  return `https://${bare}.${primary}`
}
