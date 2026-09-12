import { defineEventHandler, getQuery, createError, setHeader, getHeader } from 'h3'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const apiHost = String(config.public.apiHost || 'http://127.0.0.1:8001').replace(/\/$/, '')
  const q = getQuery(event)
  const tenant = String(q.__tenant || q.tenant || getHeader(event, 'x-tenant-domain') || '').trim()
  if (!tenant) {
    throw createError({
      statusCode: 400,
      message: '缺少租户域名：请使用 ?__tenant=your.domain',
    })
  }
  const lang = String(q.language || 'en')
  try {
    const text = await $fetch<string>(
      `${apiHost}/api/v1/public/tenants/${encodeURIComponent(tenant)}/llms.txt?language=${encodeURIComponent(lang)}`,
      { responseType: 'text' },
    )
    setHeader(event, 'Content-Type', 'text/plain; charset=utf-8')
    setHeader(event, 'Cache-Control', 'public, max-age=300')
    setHeader(event, 'X-YouDing-Tenant', tenant)
    return text
  } catch {
    throw createError({ statusCode: 502, message: '租户 llms.txt 暂不可用' })
  }
})
