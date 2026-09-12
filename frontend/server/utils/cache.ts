import type { H3Event } from 'h3'
import { setHeader, getHeader, getQuery } from 'h3'

interface CacheOptions {
  maxAge?: number
  staleMaxAge?: number
  cacheControl?: string
}

/**
 * In-memory API cache with ETag and Cache-Control header support.
 * For SSR with Nuxt 3 server routes.
 */
export function useAPICache() {
  const cacheStore = new Map<string, {
    data: any
    timestamp: number
    maxAge: number
  }>()

  function generateCacheKey(event: H3Event): string {
    const url = event.path || ''
    const query = getQuery(event)
    return `${url}:${JSON.stringify(query)}`
  }

  function get(event: H3Event): any | null {
    const key = generateCacheKey(event)
    const cached = cacheStore.get(key)

    if (!cached) return null

    const age = Date.now() - cached.timestamp
    if (age > cached.maxAge) {
      cacheStore.delete(key)
      return null
    }

    return {
      data: cached.data,
      age,
      cached: true,
      maxAge: cached.maxAge,
    }
  }

  function set(event: H3Event, data: any, options: CacheOptions = {}): void {
    const key = generateCacheKey(event)
    const maxAge = options.maxAge || 300

    cacheStore.set(key, {
      data,
      timestamp: Date.now(),
      maxAge: maxAge * 1000,
    })

    const staleMaxAge = options.staleMaxAge || maxAge * 2
    const cacheControl = options.cacheControl
      || `public, max-age=${maxAge}, s-maxage=${staleMaxAge}, stale-while-revalidate=${staleMaxAge}`

    setHeader(event, 'Cache-Control', cacheControl)
    setHeader(event, 'X-Cache-Status', 'HIT')
  }

  function invalidate(event: H3Event): void {
    const key = generateCacheKey(event)
    cacheStore.delete(key)
  }

  function invalidatePattern(pattern: string): void {
    for (const key of cacheStore.keys()) {
      if (key.includes(pattern)) {
        cacheStore.delete(key)
      }
    }
  }

  function clear(): void {
    cacheStore.clear()
  }

  function getStats() {
    let totalSize = 0
    const entries: Array<{ key: string; age: number; size: number }> = []

    for (const [key, value] of cacheStore.entries()) {
      const age = Date.now() - value.timestamp
      const size = JSON.stringify(value.data).length
      totalSize += size
      entries.push({ key, age, size })
    }

    return {
      count: cacheStore.size,
      totalSize,
      entries: entries.sort((a, b) => b.age - a.age).slice(0, 10),
    }
  }

  return { get, set, invalidate, invalidatePattern, clear, getStats }
}

export function cacheHeaders(event: H3Event, options: CacheOptions = {}) {
  const { maxAge = 300, staleMaxAge = 600, cacheControl } = options

  if (cacheControl) {
    setHeader(event, 'Cache-Control', cacheControl)
  } else {
    setHeader(
      event,
      'Cache-Control',
      `public, max-age=${maxAge}, s-maxage=${staleMaxAge}, stale-while-revalidate=${staleMaxAge}`
    )
  }

  setHeader(event, 'Vary', 'Accept-Encoding')
}

export function etagGenerator(data: any): string {
  const str = typeof data === 'string' ? data : JSON.stringify(data)
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return `W/"${Math.abs(hash).toString(36)}"`
}

export function validateETag(event: H3Event, data: any): boolean {
  const ifNoneMatch = getHeader(event, 'If-None-Match')
  if (!ifNoneMatch) return false

  const etag = etagGenerator(data)
  return ifNoneMatch === etag
}
