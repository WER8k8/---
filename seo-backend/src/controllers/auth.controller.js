const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { models, Op } = require('../config/database');
const AdminUser = models.AdminUser;
const logger = require('../utils/logger');

const login = async (req, res) => {
  try {
    const { username, password, captcha, rememberMe } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ code: 400, message: '用户名和密码不能为空' });
    }

    const user = await AdminUser.findOne({ where: { username } });
    if (!user) {
      return res.status(401).json({ code: 1001, message: '用户名或密码错误' });
    }

    if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
      return res.status(403).json({ code: 1002, message: `账号已被锁定至${user.lockedUntil}` });
    }

    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
      const failCount = user.loginFailCount + 1;
      const maxAttempts = parseInt(process.env.LOGIN_MAX_ATTEMPTS) || 5;
      
      if (failCount >= maxAttempts) {
        const lockDuration = parseInt(process.env.LOGIN_LOCK_DURATION) || 15;
        const lockedUntil = new Date(Date.now() + lockDuration * 60 * 1000);
        await user.update({ loginFailCount: failCount, lockedUntil });
        return res.status(403).json({ code: 1002, message: `密码错误次数过多，账号已锁定${lockDuration}分钟` });
      }
      
      await user.update({ loginFailCount: failCount });
      return res.status(401).json({ code: 1001, message: `用户名或密码错误（剩余${maxAttempts - failCount}次机会）` });
    }

    await user.update({ 
      loginFailCount: 0, 
      lockedUntil: null, 
      lastLoginAt: new Date(),
      lastLoginIp: req.ip
    });

    const expiresIn = rememberMe ? '7d' : (process.env.JWT_EXPIRES_IN || '24h');
    const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, { expiresIn });
    const refreshToken = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d' });

    logger.info(`用户 ${username} 登录成功`);

    res.json({
      code: 200,
      message: '登录成功',
      data: {
        token,
        refreshToken,
        expiresIn,
        user: {
          id: user.id,
          username: user.username,
          nickname: user.nickname,
          avatar: user.avatar,
          roles: ['super_admin']
        }
      }
    });
  } catch (error) {
    logger.error('登录失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const refreshToken = async (req, res) => {
  try {
    const { refreshToken } = req.body;
    if (!refreshToken) {
      return res.status(400).json({ code: 400, message: '请提供刷新令牌' });
    }

    const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET);
    const user = await AdminUser.findByPk(decoded.id);
    
    if (!user || user.status !== 1) {
      return res.status(401).json({ code: 401, message: '用户不存在或已被禁用' });
    }

    const newToken = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, { expiresIn: process.env.JWT_EXPIRES_IN || '24h' });
    
    res.json({ code: 200, message: 'success', data: { token: newToken, refreshToken } });
  } catch (error) {
    res.status(401).json({ code: 401, message: '刷新令牌无效' });
  }
};

const getProfile = async (req, res) => {
  try {
    const user = await AdminUser.findByPk(req.user.id, {
      attributes: { exclude: ['passwordHash'] }
    });
    res.json({ code: 200, message: 'success', data: user });
  } catch (error) {
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updatePassword = async (req, res) => {
  try {
    const { oldPassword, newPassword } = req.body;
    if (!oldPassword || !newPassword) {
      return res.status(400).json({ code: 400, message: '请提供旧密码和新密码' });
    }

    const user = await AdminUser.findByPk(req.user.id);
    const isValid = await bcrypt.compare(oldPassword, user.passwordHash);
    if (!isValid) {
      return res.status(400).json({ code: 400, message: '旧密码不正确' });
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await user.update({ passwordHash: hashedPassword });

    res.json({ code: 200, message: '密码修改成功' });
  } catch (error) {
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { login, refreshToken, getProfile, updatePassword };
