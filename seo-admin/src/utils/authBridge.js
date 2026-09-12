/**
 * 与主管理后台（frontend/admin）统一登录：共享 localStorage 中的 JWT。
 * 主后台写入 `admin_token`；本应用兼容旧键 `token`。
 */

const TOKEN_KEYS = ['admin_token', 'token'];

export function getSharedBearerToken() {
  for (const k of TOKEN_KEYS) {
    const t = localStorage.getItem(k);
    if (t && t.trim()) return t.trim();
  }
  return '';
}

export function persistSharedToken(token) {
  if (!token) return;
  const v = String(token).trim();
  localStorage.setItem('admin_token', v);
  localStorage.setItem('token', v);
}

export function clearSharedSession() {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
}

export function getMainAdminOrigin() {
  return String(import.meta.env.VITE_MAIN_ADMIN_ORIGIN || '').replace(/\/$/, '');
}

/** 主后台登录页路径，需与 frontend/admin 实际部署一致 */
export function getMainAdminLoginPath() {
  return String(import.meta.env.VITE_MAIN_ADMIN_LOGIN_PATH || '/login');
}

/**
 * 未登录时跳转到主管理后台登录；登录成功后可用 query.redirect 回到矩阵控制台。
 * @param {string} returnUrl 登录后回到的完整 URL（一般为当前矩阵页）
 */
export function redirectToMainAdminLogin(returnUrl) {
  const origin = getMainAdminOrigin();
  const loginPath = getMainAdminLoginPath();
  const redirect =
    returnUrl || `${window.location.origin}${window.location.pathname}${window.location.search}`;
  const q = `?redirect=${encodeURIComponent(redirect)}`;
  if (origin) {
    window.location.replace(`${origin}${loginPath}${q}`);
  } else {
    window.location.replace(`${loginPath}${q}`);
  }
}
