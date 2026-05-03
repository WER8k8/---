const jwt = require('jsonwebtoken');
const { models } = require('../config/database');
const AdminUser = models.AdminUser;
const logger = require('../utils/logger');

const authMiddleware = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ code: 401, message: '未提供认证令牌' });
    }

    const token = authHeader.split(' ')[1];
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    const user = await AdminUser.findByPk(decoded.id, {
      include: [{
        association: 'roles',
        include: [{
          association: 'permissions',
          attributes: ['code']
        }]
      }]
    });

    if (!user) {
      return res.status(401).json({ code: 401, message: '用户不存在' });
    }

    if (user.status !== 1) {
      return res.status(403).json({ code: 403, message: '账号已被禁用' });
    }

    if (user.expiresAt && new Date(user.expiresAt) < new Date()) {
      return res.status(403).json({ code: 1003, message: '账号已过期' });
    }

    if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
      return res.status(403).json({ code: 1002, message: '账号已被锁定' });
    }

    req.user = user;
    req.permissions = user.roles.flatMap(role => 
      role.permissions.map(p => p.code)
    );
    
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
