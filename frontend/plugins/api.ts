/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineNuxtPlugin, useCookie } from '#app'

/**
 * API 客户端插件
 * 将 $fetch 封装为 $api，自动拼装 /api 前缀
 */
export default defineNuxtPlugin(() => {
  const api = $fetch.create({
    baseURL: '/api',
    onRequest({ options }) {
      // 自动携带 admin token（从 cookie 读取，与 useApi 保持一致）
      if (import.meta.client) {
        const token = useCookie('admin_token').value
        if (token) {
          options.headers = {
            ...options.headers,
            Authorization: `Bearer ${token}`,
          }
        }
      }
    },
    onResponseError({ response }) {
      // 401 未授权时清除 cookie 中的 token
      if (response.status === 401 && import.meta.client) {
        const tokenCookie = useCookie('admin_token')
        tokenCookie.value = null
      }
    },
  })

  return {
    provide: {
      api,
    },
  }
})
