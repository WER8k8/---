/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 租户站统一 API 基址：优先 API_HOST，其次同源 /api/v1 代理。
 */
export function useApiV1Base(): string {
  const config = useRuntimeConfig()
  const apiHost = (config.public.apiHost as string) || ''
  if (apiHost.trim()) {
    return `${apiHost.replace(/\/$/, '')}/api/v1`
  }
  const apiBase = (config.public.apiBase as string) || '/api/v1'
  return apiBase.replace(/\/$/, '')
}

export function useApiV1Url(path: string): string {
  const base = useApiV1Base()
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}
