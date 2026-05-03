import { ref, type Ref } from 'vue'
import { useRuntimeConfig, navigateTo } from '#app'
import { useCookie } from '#app'

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

let inMemoryToken: string | null = null

function getAuthToken(): string | null {
  if (import.meta.client) {
    // 优先从内存获取，减少localStorage访问
    if (inMemoryToken) {
      return inMemoryToken
    }
    const cookieToken = useCookie('admin_token').value
    if (cookieToken) {
      inMemoryToken = cookieToken
      return cookieToken
    }
    // 兼容旧版本存储
    const localStorageToken = localStorage.getItem('admin_token')
    if (localStorageToken) {
      inMemoryToken = localStorageToken
      // 迁移到cookie
      useCookie('admin_token').value = localStorageToken
      localStorage.removeItem('admin_token')
      return localStorageToken
    }
  }
  return null
}

function setAuthToken(token: string | null): void {
  inMemoryToken = token
  if (import.meta.client) {
    const adminTokenCookie = useCookie('admin_token', {
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7天
      path: '/',
      httpOnly: false // Nuxt客户端无法设置httpOnly cookie
    })
    if (token) {
      adminTokenCookie.value = token
    } else {
      adminTokenCookie.value = null
    }
  }
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

    // 添加安全头防止XSS
    allHeaders['X-Content-Type-Options'] = 'nosniff'
    allHeaders['X-Frame-Options'] = 'DENY'

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

  return { request, useRequest, setAuthToken, getAuthToken }
}
