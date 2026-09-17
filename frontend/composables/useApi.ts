/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, type Ref } from 'vue';
import { useRuntimeConfig, navigateTo, useCookie } from '#app';

interface ApiState<T> {
  data: Ref<T | null>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, unknown>;
  headers?: Record<string, string>;
  skipAuth?: boolean;
  immediate?: boolean;
}

/**
 * 内存级 token 缓存，避免频繁读取 cookie。
 * SSR 安全：服务端不共享全局 mutable 状态。
 */
let inMemoryToken: string | null = null;

function getAuthToken(): string | null {
  // SSR 环境下不读取客户端存储
  if (import.meta.server) return null;

  if (inMemoryToken) return inMemoryToken;

  const cookieToken = useCookie('admin_token').value;
  if (cookieToken) {
    inMemoryToken = cookieToken;
    return cookieToken;
  }

  // 一次性迁移：旧版 localStorage token → cookie
  try {
    const localStorageToken = localStorage.getItem('admin_token');
    if (localStorageToken) {
      inMemoryToken = localStorageToken;
      useCookie('admin_token').value = localStorageToken;
      localStorage.removeItem('admin_token');
      return localStorageToken;
    }
  } catch {
    // 无 localStorage 权限（如私有模式）
  }

  return null;
}

function setAuthToken(token: string | null): void {
  if (import.meta.server) return;

  inMemoryToken = token;
  const adminTokenCookie = useCookie('admin_token', {
    secure: import.meta.env.PROD,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7,
    path: '/',
  });

  if (token) {
    adminTokenCookie.value = token;
  } else {
    adminTokenCookie.value = null;
    // 清理所有可能的遗留存储
    try {
      localStorage.removeItem('admin_token');
    } catch { /* ignore */ }
  }
}

function stripApiPrefix(endpoint: string, apiBase: string): string {
  const prefix = '/api/v1';
  if (endpoint.startsWith(prefix)) {
    return endpoint.slice(prefix.length) || '/';
  }
  if (apiBase && apiBase !== prefix && endpoint.startsWith(apiBase)) {
    return endpoint.slice(apiBase.length) || '/';
  }
  return endpoint;
}

export function useApi() {
  const config = useRuntimeConfig();
  const baseURL = config.public.apiBase as string;

  async function request<T = unknown>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, params, headers = {}, skipAuth = false } = options;
    const path = endpoint.startsWith('http') ? endpoint : stripApiPrefix(endpoint, baseURL);
    const origin = import.meta.client ? window.location.origin : '';
    const url = endpoint.startsWith('http')
      ? new URL(endpoint)
      : new URL(`${baseURL}${path.startsWith('/') ? path : `/${path}`}`, origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      });
    }

    const allHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(import.meta.client ? { Origin: window.location.origin } : {}),
      ...headers,
    };

    if (!skipAuth) {
      const token = getAuthToken();
      if (token) {
        allHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const fetchOptions: RequestInit = {
      method,
      headers: allHeaders,
    };
    if (body && method !== 'GET') {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url.toString(), fetchOptions);
    const responseBody = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (response.status === 401 && !skipAuth) {
        if (import.meta.client) {
          setAuthToken(null);
          navigateTo('/admin/login');
        }
      }
      throw new Error(
        responseBody.message || responseBody.detail || `请求失败: ${response.status}`
      );
    }

    // 检查业务码
    if (responseBody.code !== undefined && responseBody.code !== 0) {
      if (responseBody.code === 401 && !skipAuth) {
        if (import.meta.client) {
          setAuthToken(null);
          navigateTo('/admin/login');
        }
      }
      throw new Error(responseBody.message || `请求失败: ${responseBody.code}`);
    }

    if (
      responseBody &&
      typeof responseBody === 'object' &&
      'code' in responseBody &&
      (responseBody as { code: number }).code === 0 &&
      'data' in responseBody &&
      (responseBody as { data: unknown }).data !== undefined
    ) {
      return (responseBody as { data: T }).data;
    }

    return responseBody as T;
  }

  function get<T = unknown>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}) {
    return request<T>(endpoint, { ...options, method: 'GET' });
  }

  function post<T = unknown>(
    endpoint: string,
    body?: unknown,
    options: Omit<RequestOptions, 'method' | 'body'> = {}
  ) {
    return request<T>(endpoint, { ...options, method: 'POST', body });
  }

  function put<T = unknown>(
    endpoint: string,
    body?: unknown,
    options: Omit<RequestOptions, 'method' | 'body'> = {}
  ) {
    return request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  function del<T = unknown>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}) {
    return request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  function useRequest<T = unknown>(
    endpoint: string,
    options: RequestOptions = {}
  ): ApiState<T> & { execute: () => Promise<void> } {
    const data: Ref<T | null> = ref(null);
    const loading = ref(false);
    const error = ref<string | null>(null);

    const execute = async () => {
      loading.value = true;
      error.value = null;
      try {
        data.value = await request<T>(endpoint, options);
      } catch (e: unknown) {
        error.value = e instanceof Error ? e.message : String(e);
      } finally {
        loading.value = false;
      }
    };

    if (options.immediate !== false) {
      execute();
    }

    return { data, loading, error, execute };
  }

  return { request, useRequest, setAuthToken, getAuthToken, get, post, put, delete: del };
}
