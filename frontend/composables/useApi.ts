import { ref, type Ref } from 'vue'
import { useRuntimeConfig, navigateTo } from '#app'

interface ApiState<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
}

interface RequestOptions {
  method?: string
  body?: any
  params?: Record<string, any>
  headers?: Record<string, string>
  skipAuth?: boolean
  immediate?: boolean
}

function getAuthToken(): string | null {
  if (import.meta.client) {
    return localStorage.getItem('admin_token')
  }
  return null
}

export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  async function request<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { method = 'GET', body, params, headers = {}, skipAuth = false } = options
    const origin = import.meta.client ? window.location.origin : ''
    const url = new URL(`${baseURL}${endpoint}`, origin)
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v))
      })
    }

    const allHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      'Origin': import.meta.client ? window.location.origin : 'http://localhost:3000',
      ...headers,
    }

    if (!skipAuth) {
      const token = getAuthToken()
      if (token) {
        allHeaders['Authorization'] = `Bearer ${token}`
      }
    }

    const fetchOptions: RequestInit = {
      method,
      headers: allHeaders,
    }
    if (body && method !== 'GET') {
      fetchOptions.body = JSON.stringify(body)
    }

    const response = await fetch(url.toString(), fetchOptions)
    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}))
      if (response.status === 401 && !skipAuth) {
        if (import.meta.client) {
          localStorage.removeItem('admin_token')
          navigateTo('/admin/login')
        }
      }
      throw new Error(errBody.detail || `请求失败: ${response.status}`)
    }
    return response.json()
  }

  function useRequest<T = any>(endpoint: string, options: RequestOptions = {}): ApiState<T> & { execute: () => Promise<void> } {
    const data: Ref<T | null> = ref(null)
    const loading = ref(false)
    const error = ref<string | null>(null)

    const execute = async () => {
      loading.value = true
      error.value = null
      try {
        data.value = await request<T>(endpoint, options)
      } catch (e: any) {
        error.value = e.message
      } finally {
        loading.value = false
      }
    }

    if (options.immediate !== false) {
      execute()
    }

    return { data, loading, error, execute }
  }

  return { request, useRequest }
}
