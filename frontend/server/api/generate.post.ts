/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * GEO Content Generation API
 * Proxies content generation requests to UJ backend with Redis caching.
 */
import { defineEventHandler, readBody } from 'h3'
import { redisGet, redisSet } from '../utils/redis'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const cacheKey = `geo_content:${body.keyword || 'default'}:${body.intent || 'mobile'}`

  // Try Redis cache first
  const cached = await redisGet(cacheKey)
  if (cached) {
    return JSON.parse(cached)
  }

  // Forward to backend
  const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000'
  const data = await $fetch(`${backendUrl}/api/generate`, {
    method: 'POST',
    body,
  })

  // Cache for 24 hours
  await redisSet(cacheKey, JSON.stringify(data), 86400)

  return data
})
