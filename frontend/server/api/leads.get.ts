/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * Leads list API - proxied from backend.
 */
import { defineEventHandler, getQuery } from 'h3'

export default defineEventHandler(async (event) => {
  const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000'
  const query = getQuery(event)
  const limit = Number(query.limit || 50)

  return await $fetch(`${backendUrl}/api/leads`, {
    query: { limit },
  })
})
