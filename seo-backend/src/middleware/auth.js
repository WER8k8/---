const jwt = require('jsonwebtoken');
const { models } = require('../config/database');
const AdminUser = models.AdminUser;
const logger = require('../utils/logger');

/**
 * 1) 本服务签发的 JWT：payload.id
 * 2) 主管理后台（Python）统一登录签发：payload.sub + mid → 映射 admin_users.id
 */
async function resolveUserFromBearerToken(token) {
  const nodeSecret = process.env.JWT_SECRET;
  const mainSecret = process.env.MAIN_ADMIN_JWT_SECRET;

  if (!nodeSecret) {
    return null;
  }

  let user = null;

  try {
    const decoded = jwt.verify(token, nodeSecret);
    if (decoded && decoded.id != null) {
      user = await AdminUser.findByPk(decoded.id);
    }
  } catch (e) {
    // try Python-issued token below
  }

  if (!user && mainSecret && mainSecret !== nodeSecret) {
    try {
      const py = jwt.verify(token, mainSecret, { algorithms: ['HS256'] });
      const mid = py.mid != null ? Number(py.mid) : NaN;
      if (Number.isInteger(mid) && mid > 0) {
        user = await AdminUser.findByPk(mid);
      }
    } catch (e) {
      // fall through
    }
  }

  return user;
}

const authMiddleware = async (req, res, next) => {
  try {
    if (!process.env.JWT_SECRET) {
      logger.error('JWT_SECRET 未配置');
      return res.status(500).json({ code: 500, message: '服务器认证配置错误' });
    }

    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ code: 401, message: '未提供认证令牌' });
    }

    const token = authHeader.split(' ')[1];
    const user = await resolveUserFromBearerToken(token);

    if (!user) {
      return res.status(401).json({ code: 401, message: '用户不存在' });
    }

    if (user.status !== 1) {
      return res.status(403).json({ code: 403, message: '账号已被禁用' });
    }

    req.user = user;
    req.permissions = [];

    next();
  } catch (error) {
    logger.error('认证中间件错误:', error);
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({ code: 401, message: '无效的认证令牌' });
    }
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ code: 401, message: '认证令牌已过期' });
    }
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = authMiddleware;
