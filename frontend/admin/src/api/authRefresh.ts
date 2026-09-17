/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { getActivePinia } from 'pinia';
import { readStoredRefreshToken } from '@/utils/sessionAuth';

const baseURL = ((import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
  ?.VITE_API_BASE ?? '/api/v1') as string;

let refreshInFlight: Promise<boolean> | null = null;

function parseRefreshEnvelope(raw: unknown): {
  access_token: string;
  refresh_token?: string;
} | null {
  if (!raw || typeof raw !== 'object') return null;
  const o = raw as Record<string, unknown>;
  if (typeof o.code === 'number' && o.code !== 0) return null;
  const inner =
    o.code === 0 && o.data && typeof o.data === 'object' && !Array.isArray(o.data)
      ? (o.data as Record<string, unknown>)
      : o;
  const at = inner.access_token;
  const rt = inner.refresh_token;
  if (typeof at !== 'string' || at.length === 0) return null;
  // FIX-23: refresh_token 可能通过 HttpOnly Cookie 返回，响应体中不一定包含
  if (typeof rt === 'string' && rt.length > 0) {
    return { access_token: at, refresh_token: rt };
  }
  return { access_token: at };
}

const REFRESH_TIMEOUT_MS = 8000;

/**
 * 静默续期（fetch，不经 axios 拦截器）。并发请求共享同一 Promise，避免竞态。
 * FIX-23: 支持 HttpOnly Cookie 模式（storage 中无 refresh_token 时仍尝试请求）
 */
export function performSilentTokenRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  const p = (async (): Promise<boolean> => {
    const rt = readStoredRefreshToken();
    const url = `${String(baseURL).replace(/\/$/, '')}/auth/refresh`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REFRESH_TIMEOUT_MS);
    try {
      const body: Record<string, unknown> = {};
      if (rt) body.refresh_token = rt;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
        credentials: 'include',
      });
      const raw = await res.json().catch(() => null);
      const pair = parseRefreshEnvelope(raw);
      if (!pair) return false;
      // TODO: 添加 store 初始化校验，防止未初始化时调用
      const { useAuthStore } = await import('@/stores/auth');
      const pinia = getActivePinia();
      if (pinia) {
        // FIX-23: refresh_token 可能通过 HttpOnly Cookie 返回，不传则保持 undefined
        useAuthStore(pinia).applyTokenPair(pair.access_token, pair.refresh_token);
      } else {
        // 与 auth store 保持一致：优先 sessionStorage，回退 localStorage
        const store = typeof sessionStorage !== 'undefined' ? sessionStorage : localStorage;
        store.setItem('admin_token', pair.access_token);
        if (pair.refresh_token) {
          store.setItem('admin_refresh_token', pair.refresh_token);
        }
      }
      if (!pair.refresh_token && rt) {
        // 轮换后响应未携带新 refresh_token（Cookie 模式）：storage 里留着的旧 rt 已被
        // 后端 revoke，下次请求若再随 body 发送会 401 触发 hardLogout。清掉旧值，
        // 后续刷新仅依赖最新 Cookie。
        try { sessionStorage.removeItem('admin_refresh_token'); } catch {}
        try { localStorage.removeItem('admin_refresh_token'); } catch {}
      }
      return true;
    } catch {
      return false;
    } finally {
      clearTimeout(timer);
    }
  })();
  refreshInFlight = p;
  void p.finally(() => {
    if (refreshInFlight === p) refreshInFlight = null;
  });
  return p;
}
