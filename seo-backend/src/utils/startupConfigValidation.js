/**
 * 进程启动前环境变量自检（生产环境强制项更严）。
 * 校验失败抛出 Error，由 app.js 捕获后 process.exit(1)。
 */

const logger = require('./logger');

function isProduction() {
  return String(process.env.NODE_ENV || '').toLowerCase() === 'production';
}

function parseHttpUrl(raw) {
  const s = String(raw || '').trim();
  if (!s) return null;
  try {
    const u = new URL(s);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return null;
    return u;
  } catch {
    return null;
  }
}

function validateSeoMatrixDbEnvOrThrow() {
  const host = (process.env.SEO_MATRIX_DB_HOST || '').trim();
  const name = (process.env.SEO_MATRIX_DB_NAME || '').trim();
  const user = process.env.SEO_MATRIX_DB_USER;
  const userStr = user === undefined ? '' : String(user).trim();
  const hasPassword = process.env.SEO_MATRIX_DB_PASSWORD !== undefined;

  const any = !!(host || name || userStr || hasPassword);
  if (!any) {
    return;
  }

  const missing = [];
  if (!host) missing.push('SEO_MATRIX_DB_HOST');
  if (!name) missing.push('SEO_MATRIX_DB_NAME');
  if (!userStr) missing.push('SEO_MATRIX_DB_USER');

  if (missing.length) {
    throw new Error(
      `[配置错误] 已检测到矩阵 MySQL 相关环境变量不完整，缺少: ${missing.join(
        ', '
      )}。请要么补全 SEO_MATRIX_DB_HOST / SEO_MATRIX_DB_NAME / SEO_MATRIX_DB_USER（及可选 SEO_MATRIX_DB_PASSWORD、SEO_MATRIX_DB_PORT），要么删除所有 SEO_MATRIX_DB_* 以禁用矩阵第二连接。`
    );
  }
}

function validateUnifiedLoginUrlOrThrow() {
  const raw = (process.env.UNIFIED_ADMIN_LOGIN_URL || '').trim();
  if (!isProduction()) {
    if (raw) {
      const u = parseHttpUrl(raw);
      if (!u) {
        throw new Error(
          '[配置错误] UNIFIED_ADMIN_LOGIN_URL 必须是合法的 http(s) 绝对 URL，例如 https://admin.example.com/login'
        );
      }
    }
    return;
  }

  if (!raw) {
    throw new Error(
      '[配置错误] 生产环境必须设置 UNIFIED_ADMIN_LOGIN_URL（统一管理员登录页完整 URL），用于 GET /api/v1/auth/login 的 302 跳转。'
    );
  }
  const u = parseHttpUrl(raw);
  if (!u) {
    throw new Error(
      '[配置错误] UNIFIED_ADMIN_LOGIN_URL 必须是合法的 http(s) 绝对 URL，例如 https://admin.example.com/login'
    );
  }
  if (u.protocol === 'http:' && !['localhost', '127.0.0.1'].includes(u.hostname)) {
    logger.warn(
      '[安全提示] 生产环境 UNIFIED_ADMIN_LOGIN_URL 使用了 http 非本机域名，存在明文传输风险，建议使用 https。'
    );
  }
}

function validateJwtSecretPresenceOrThrow() {
  const node = (process.env.JWT_SECRET || '').trim();
  if (!node) {
    throw new Error(
      '[配置错误] 必须设置 JWT_SECRET（矩阵本机 refresh / 历史 Node Token 签名密钥），且长度建议不少于 32 字符。'
    );
  }
  if (node.length < 16) {
    throw new Error(
      '[配置错误] JWT_SECRET 长度过短（<16），不满足最低安全要求，请更换为足够长的随机串。'
    );
  }

  if (isProduction()) {
    const main = (process.env.MAIN_ADMIN_JWT_SECRET || '').trim();
    if (!main) {
      throw new Error(
        '[配置错误] 生产环境必须设置 MAIN_ADMIN_JWT_SECRET，且其值须与 Python 主后端 JWT_SECRET_KEY 完全一致，用于校验统一登录签发的 Bearer Token（须与 JWT_SECRET 不同）。'
      );
    }
    if (main.length < 16) {
      throw new Error(
        '[配置错误] MAIN_ADMIN_JWT_SECRET 长度过短（<16），请更换为与主站一致的强随机密钥。'
      );
    }
  }
}

/**
 * 启动前完整自检（在连接数据库之前调用）。
 */
function validateStartupConfigOrThrow() {
  validateJwtSecretPresenceOrThrow();
  validateSeoMatrixDbEnvOrThrow();
  validateUnifiedLoginUrlOrThrow();
}

module.exports = {
  validateStartupConfigOrThrow,
  isProduction,
};
