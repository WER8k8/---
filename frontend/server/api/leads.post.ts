/**
 * Submit a new lead/inquiry - proxied from backend.
 */
import { defineEventHandler, readBody } from 'h3'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000'

  return await $fetch(`${backendUrl}/api/leads`, {
    method: 'POST',
    body,
  })
})
