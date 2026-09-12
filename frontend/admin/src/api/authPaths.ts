/** 认证相关路径（勿在页面模板中拼接展示，仅供代码引用） */
export function apiV1Base(): string {
  const b = (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE;
  return String(b ?? '/api/v1').replace(/\/$/, '');
}

/** 与后端 `AUTH_LOGIN_ROUTE` 对应：必须为 `/auth/...`，禁止 `..` 与非安全字符 */
export function normalizeAuthLoginPath(raw: string | undefined): string {
  const fallback = '/auth/login';
  if (typeof raw !== 'string') return fallback;
  const p0 = raw.trim();
  if (!p0) return fallback;
  const p = p0.startsWith('/') ? p0 : `/${p0}`;
  if (p.includes('..')) return fallback;
  if (!/^\/auth\/[A-Za-z0-9/_-]+$/.test(p)) return fallback;
  return p;
}

/** 登录提交 URL；通过 VITE_AUTH_LOGIN_PATH 与后端 `AUTH_LOGIN_ROUTE` 保持一致 */
export function authLoginUrl(): string {
  const p = (import.meta as unknown as { env?: { VITE_AUTH_LOGIN_PATH?: string } }).env
    ?.VITE_AUTH_LOGIN_PATH;
  const path = normalizeAuthLoginPath(p);
  return `${apiV1Base()}${path}`;
}
