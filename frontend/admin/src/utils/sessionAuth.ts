/** 会话与 JWT 判定（与 stores/auth、api 拦截器共用，避免误退登录） */

import { decodeJwtPayload, isJwtExpired, jwtRoleFromPayload } from '@/utils/jwtPayload';

const LS_TOKEN = 'admin_token';
const LS_REFRESH = 'admin_refresh_token';

// ⚠️ 安全: 优先 sessionStorage（关闭浏览器即清除），回退 localStorage
const tokenStorage = typeof sessionStorage !== 'undefined' ? sessionStorage
  : typeof localStorage !== 'undefined' ? localStorage : null;

export function readStoredAccessToken(): string | null {
  if (!tokenStorage) return null;
  const t = tokenStorage.getItem(LS_TOKEN);
  return t && t.trim() ? t : null;
}

export function readStoredRefreshToken(): string | null {
  if (!tokenStorage) return null;
  const t = tokenStorage.getItem(LS_REFRESH);
  return t && t.trim() ? t : null;
}

function looksLikeJwt(token: string): boolean {
  return token.split('.').length >= 3;
}

export function hasValidAccessToken(token: string | null = readStoredAccessToken()): boolean {
  const t = token?.trim();
  if (!t) return false;
  if (!looksLikeJwt(t)) return false;
  const payload = decodeJwtPayload(t);
  if (!payload) return false;
  const exp = payload.exp;
  if (typeof exp !== 'number' || !Number.isFinite(exp)) return false;
  return !isJwtExpired(t);
}

/** 平台管理员：JWT role 为 admin / super_admin 时放行全部工作台能力 */
export function isPlatformAdminFromToken(token: string | null): boolean {
  if (!token) return false;
  const role = jwtRoleFromPayload(decodeJwtPayload(token));
  return role === 'admin' || role === 'super_admin';
}

export function canRestoreSession(): boolean {
  const t = readStoredRefreshToken();
  if (!t) return false;
  if (!looksLikeJwt(t)) return true;
  const payload = decodeJwtPayload(t);
  return payload ? !isJwtExpired(t) : false;
}
