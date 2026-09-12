/**
 * 矩阵后端不再提供独立 JSON 登录：POST 一律 403；其余方法 302 到统一登录（OPTIONS 204 以利 CORS）。
 */
function getUnifiedLoginRedirect(req, res) {
  const base = (process.env.UNIFIED_ADMIN_LOGIN_URL || 'http://localhost:5173/login').replace(
    /\/$/,
    ''
  );
  const q = req.query && req.query.redirect;
  const back = typeof q === 'string' && q.trim() ? q.trim() : '';
  const target = back ? `${base}?redirect=${encodeURIComponent(back)}` : base;
  return res.redirect(302, target);
}

function postLoginForbidden(_req, res) {
  return res.status(403).json({ code: 403, message: 'Forbidden' });
}

function handleAuthLogin(req, res) {
  if (req.method === 'POST') {
    return postLoginForbidden(req, res);
  }
  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  return getUnifiedLoginRedirect(req, res);
}

module.exports = { getUnifiedLoginRedirect, postLoginForbidden, handleAuthLogin };
