/**
 * 根据 Host 解析租户 ID — 代理后端 /api/v1/domains/resolve
 */
import { defineEventHandler, getQuery, createError } from 'h3'

export default defineEventHandler(async (event) => {
  const host = getQuery(event).host as string | undefined
  if (!host?.trim()) {
    throw createError({ statusCode: 400, message: '缺少 host 参数' })
  }

  const config = useRuntimeConfig()
  const apiHost = (config.public.apiHost as string) || 'http://localhost:8000'
  const target = `${apiHost.replace(/\/$/, '')}/api/v1/domains/resolve?host=${encodeURIComponent(host.trim())}`

  try {
    return await $fetch(target)
  } catch (err: unknown) {
    const status = (err as { statusCode?: number })?.statusCode
    if (status === 404) {
      throw createError({ statusCode: 404, message: '域名未绑定租户' })
    }
    throw createError({ statusCode: 502, message: '租户解析服务暂不可用' })
  }
})
