/** 统一 API 调用工具 + 认证令牌管理
 * 替代散落各处的 localStorage.getItem('admin_token') + 手动 fetch()
 */

import { getActivePinia } from 'pinia';
import { useAuthStore } from '@/stores/auth';
import { performSilentTokenRefresh } from '@/api/authRefresh';
import { readStoredAccessToken } from '@/utils/sessionAuth';
import { guardApiPayload } from '@/utils/noFakeDelivery';

/** API 基础路径前缀：默认 /api/v1，可用 VITE_API_BASE（构建静态注入）或
 * 运行期 window.__CONFIG__.API_BASE 覆盖，避免多环境部署时改码。 */
function resolveApiBase(): string {
  const fromEnv = (import.meta?.env?.VITE_API_BASE as string | undefined)?.trim();
  if (fromEnv) return fromEnv;
  const runtime =
    typeof window !== 'undefined'
      ? (window as { __CONFIG__?: { API_BASE?: string } }).__CONFIG__?.API_BASE
      : undefined;
  if (typeof runtime === 'string' && runtime.trim()) return runtime.trim();
  return '/api/v1';
}
const API_BASE = resolveApiBase().replace(/\/$/, '') || '/api/v1';

/**
 * FIX-CSRF: Cookie 认证模式下（token 哨兵 'cookie'）无 Bearer，后端 CSRF
 * double-submit 校验要求 X-CSRF-Token 头与 csrf_token cookie 一致。
 * 后端在安全方法（GET）响应里通过 X-CSRF-Token 响应头下发 token，这里
 * 统一捕获缓存，供 authHeaders 在 Cookie 模式下回放。
 */
const CSRF_STORE_KEY = 'csrf_echo_token';

function captureCsrfEchoToken(res: Response): void {
  try {
    const v = res.headers.get('X-CSRF-Token');
    if (v) sessionStorage.setItem(CSRF_STORE_KEY, v);
  } catch {
    /* sessionStorage 不可用时静默降级 */
  }
}

function readCsrfEchoToken(): string {
  try {
    return sessionStorage.getItem(CSRF_STORE_KEY) ?? '';
  } catch {
    return '';
  }
}

/** 获取认证令牌：优先 Pinia authStore，降级 readStoredAccessToken（sessionStorage > localStorage） */
export function getAuthToken(): string {
  try {
    const pinia = getActivePinia();
    if (pinia) {
      const t = useAuthStore(pinia).token;
      if (t) return t;
    }
  } catch {
    /* pinia 未挂载时降级 */
  }
  return readStoredAccessToken() ?? '';
}

/** 标准化认证请求头 */
export function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const token = getAuthToken();
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  // 哨兵值 'cookie' 表示 Cookie 认证模式：不发 Bearer，认证走 HttpOnly Cookie
  if (token && token !== 'cookie') h['Authorization'] = `Bearer ${token}`;
  // FIX-CSRF: Cookie 模式走 CSRF double-submit —— 回放 X-CSRF-Token 响应头缓存
  if (token === 'cookie') {
    const csrf = readCsrfEchoToken();
    if (csrf) h['X-CSRF-Token'] = csrf;
  }
  return { ...h, ...extra };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public endpoint: string,
    message?: string,
  ) {
    super(message || `API ${status}: ${endpoint}`);
  }
}

type QueryParams = Record<string, string | number | boolean | undefined | null>;

/** 开发态 API 超时（毫秒），避免后端挂掉时全站无限转圈 */
const API_FETCH_TIMEOUT_MS = 15_000;

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs = API_FETCH_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal, credentials: 'include' });
    captureCsrfEchoToken(res);
    return res;
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        0,
        url,
        timeoutMs > API_FETCH_TIMEOUT_MS
          ? `请求超时（已等待 ${Math.round(timeoutMs / 1000)} 秒）：后端仍在处理，请稍后点「刷新」重试`
          : '请求超时：后端可能未启动或响应过慢，请运行 scripts/start-dev-admin.ps1 后刷新',
      );
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchWithAuthRetry(
  url: string,
  init: RequestInit,
  retried = false,
  timeoutMs = API_FETCH_TIMEOUT_MS,
): Promise<Response> {
  const res = await fetchWithTimeout(url, init, timeoutMs);
  if (
    res.status !== 401 ||
    retried ||
    /\/auth\/(login|refresh)\b/.test(url)
  ) {
    return res;
  }
  const refreshed = await performSilentTokenRefresh();
  if (!refreshed) {
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      const pinia = getActivePinia();
      if (pinia) await useAuthStore(pinia).logout();
      else {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_refresh_token');
        localStorage.removeItem('admin_username');
      }
      const full = `${window.location.pathname}${window.location.search || ''}`;
      window.location.assign(`/login?redirect=${encodeURIComponent(full)}`);
    }
    return res;
  }
  const nextHeaders = {
    ...(init.headers as Record<string, string> | undefined),
    ...authHeaders(),
  };
  return fetchWithAuthRetry(url, { ...init, headers: nextHeaders }, true, timeoutMs);
}

/** fetch + 认证头 + 401 静默续期（与 axios 拦截器同源逻辑） */
export async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const headers = {
    ...authHeaders(),
    ...(init?.headers as Record<string, string> | undefined),
  };
  return fetchWithAuthRetry(input, { ...init, headers });
}

type ApiRequestOptions = {
  timeoutMs?: number
}

/** 统一 GET 请求 */
export async function apiGet<T = any>(
  path: string,
  params?: QueryParams,
  options?: ApiRequestOptions,
): Promise<T> {
  const u = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) u.searchParams.set(k, String(v));
    });
  }
  const res = await fetchWithAuthRetry(
    u.toString(),
    { headers: authHeaders() },
    false,
    options?.timeoutMs,
  );
  if (!res.ok) await throwApiError(res, `GET ${path}`);
  const body = await res.json();
  return unwrapApiBody<T>(body, `GET ${path}`);
}

/** 统一 POST 请求 */
export async function apiPost<T = any>(path: string, data?: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetchWithAuthRetry(`${API_BASE}${path}`, {
    method: 'POST',
    headers: authHeaders(),
    body: data ? JSON.stringify(data) : undefined,
    signal,
  });
  if (!res.ok) await throwApiError(res, `POST ${path}`);
  const body = await res.json();
  return unwrapApiBody<T>(body, `POST ${path}`);
}

/** 统一 PUT 请求 */
export async function apiPut<T = any>(path: string, data?: unknown): Promise<T> {
  const res = await fetchWithAuthRetry(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!res.ok) await throwApiError(res, `PUT ${path}`);
  const body = await res.json();
  return unwrapApiBody<T>(body, `PUT ${path}`);
}

/** 统一 PATCH 请求 */
export async function apiPatch<T = any>(path: string, data?: unknown): Promise<T> {
  const res = await fetchWithAuthRetry(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!res.ok) await throwApiError(res, `PATCH ${path}`);
  const body = await res.json();
  return unwrapApiBody<T>(body, `PATCH ${path}`);
}

/** 统一 DELETE 请求 */
export async function apiDelete(path: string): Promise<void> {
  const res = await fetchWithAuthRetry(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) await throwApiError(res, `DELETE ${path}`);
}

async function throwApiError(res: Response, endpoint: string): Promise<never> {
  let msg: string | undefined;
  try {
    const body = (await res.json()) as Record<string, unknown>;
    const detail = body.detail;
    if (typeof detail === 'string' && detail) {
      msg = detail;
    } else if (Array.isArray(detail)) {
      msg = detail
        .map((item) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object' && 'msg' in item) {
            return String((item as { msg?: unknown }).msg ?? item);
          }
          return String(item);
        })
        .join('; ');
    } else if (typeof body.message === 'string' && body.message) {
      msg = body.message;
    }
  } catch {
    /* 非 JSON 响应 */
  }
  throw new ApiError(res.status, endpoint, msg);
}

function unwrapApiBody<T>(body: Record<string, unknown>, endpoint: string): T {
  if (typeof body.code === 'number' && body.code !== 0) {
    const msg =
      typeof body.message === 'string' && body.message
        ? body.message
        : `请求失败 (${body.code})`;
    throw new ApiError(body.code, endpoint, msg);
  }
  if (body.code === 0 && body.data !== undefined) {
    return guardApiPayload(body.data as T, endpoint);
  }
  return guardApiPayload(body as T, endpoint);
}

/** ===== 带后端持久化的 localStorage 替代方案 ===== */

/** 从后端 OperationLog API 加载数据（替代 localStorage 的表数据） */
export { apiGet as loadFromApi, apiPost as saveToApi, apiPut as updateApi, apiDelete as deleteFromApi }

/** 通用后端持久化存储：优先 API，失败时降级 localStorage */
export async function persistentGet<T>(key: string, apiPath: string): Promise<T | null> {
  try {
    return await apiGet<T>(apiPath)
  } catch {
    // 生产路径禁止用 localStorage 缓存冒充实盘
    if (import.meta.env.PROD) return null
    try {
      const raw = localStorage.getItem(`cache:${key}`)
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  }
}

export async function persistentSet(key: string, apiPath: string, data: unknown): Promise<void> {
  // 先写 localStorage 缓存（快速响应）
  try { localStorage.setItem(`cache:${key}`, JSON.stringify(data)) } catch {}
  // 异步写后端
  try { await apiPost(apiPath, data) } catch {}
}

/** 业务操作日志写入（对应 /api/v1/super-admin/audit，复用现有 OperationLog） */
export async function logOperation(action: string, resourceType: string, detail?: string): Promise<void> {
  try {
    await apiPost('/super-admin/audit', { action, resource_type: resourceType, detail })
  } catch {}
}
