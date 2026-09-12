const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const { models, Op } = require('../config/database');
const { SocialLogin, AdminUser, EmailVerification } = models;
const logger = require('../utils/logger');

const generateVerificationCode = () => {
  return Math.random().toString().slice(2, 8);
};

const sendEmailVerificationCode = async (email, code, type) => {
  logger.info(`发送邮箱验证码: ${email} 类型: ${type} 验证码: ${code}`);
  return true;
};

const sendEmailCode = async (req, res) => {
  try {
    const { email, type } = req.body;
    if (!email || !type) {
      return res.status(400).json({ code: 400, message: '邮箱和类型不能为空' });
    }

    const code = generateVerificationCode();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000);

    await EmailVerification.create({
      email,
      verificationCode: code,
      verificationType: type,
      ipAddress: req.ip,
      expiresAt,
      isUsed: 0,
    });

    await sendEmailVerificationCode(email, code, type);

    res.json({ code: 200, message: '验证码发送成功，请查收邮箱' });
  } catch (error) {
    logger.error('发送邮箱验证码失败:', error);
    res.status(500).json({ code: 500, message: '发送失败，请稍后重试' });
  }
};

const emailLogin = async (req, res) => {
  try {
    const { email, code } = req.body;
    if (!email || !code) {
      return res.status(400).json({ code: 400, message: '邮箱和验证码不能为空' });
    }

    const verification = await EmailVerification.findOne({
      where: {
        email,
        verificationCode: code,
        verificationType: 'login',
        isUsed: 0,
        expiresAt: { [Op.gt]: new Date() },
      },
    });

    if (!verification) {
      return res.status(400).json({ code: 400, message: '验证码无效或已过期' });
    }

    await verification.update({ isUsed: 1 });

    let user = await AdminUser.findOne({ where: { email } });

    if (!user) {
      const randomPassword = crypto.randomBytes(8).toString('hex');
      const passwordHash = await bcrypt.hash(randomPassword, 10);
      user = await AdminUser.create({
        username: email.split('@')[0],
        email,
        passwordHash,
        nickname: email.split('@')[0],
        status: 1,
      });
    }

    await SocialLogin.findOrCreate({
      where: { userId: user.id, provider: 'email', providerUserId: email },
      defaults: {
        providerUsername: email,
        lastLoginAt: new Date(),
      },
    });

    const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '24h',
    });
    const refreshToken = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '7d' });

    logger.info(`用户 ${email} 邮箱登录成功`);

    res.json({
      code: 200,
      message: '登录成功',
      data: {
        token,
        refreshToken,
        user: {
          id: user.id,
          username: user.username,
          nickname: user.nickname,
          avatar: user.avatar,
          email: user.email,
          roles: ['super_admin'],
        },
      },
    });
  } catch (error) {
    logger.error('邮箱登录失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const qqAuth = async (req, res) => {
  try {
    const { code, state } = req.body;
    if (!code) {
      return res.status(400).json({ code: 400, message: '授权码不能为空' });
    }

    const mockOpenId = `qq_user_${Date.now()}`;
    const mockUsername = 'QQ用户';

    let socialLogin = await SocialLogin.findOne({
      where: { provider: 'qq', providerUserId: mockOpenId },
    });

    let user;
    if (socialLogin) {
      user = await AdminUser.findByPk(socialLogin.userId);
      await socialLogin.update({ lastLoginAt: new Date() });
    } else {
      const randomPassword = crypto.randomBytes(8).toString('hex');
      const passwordHash = await bcrypt.hash(randomPassword, 10);
      user = await AdminUser.create({
        username: `qq_${Date.now()}`,
        passwordHash,
        nickname: mockUsername,
        status: 1,
      });

      await SocialLogin.create({
        userId: user.id,
        provider: 'qq',
        providerUserId: mockOpenId,
        providerUsername: mockUsername,
        lastLoginAt: new Date(),
      });
    }

    const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, {
      expiresIn: '24h',
    });
    const refreshToken = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '7d' });

    logger.info(`用户 ${user.username} QQ登录成功`);

    res.json({
      code: 200,
      message: '登录成功',
      data: {
        token,
        refreshToken,
        user: {
          id: user.id,
          username: user.username,
          nickname: user.nickname,
          avatar: user.avatar,
          roles: ['super_admin'],
        },
      },
    });
  } catch (error) {
    logger.error('QQ登录失败:', error);
    res.status(500).json({ code: 500, message: '登录失败，请稍后重试' });
  }
};

const wechatAuth = async (req, res) => {
  try {
    const { code, state } = req.body;
    if (!code) {
      return res.status(400).json({ code: 400, message: '授权码不能为空' });
    }

    const mockOpenId = `wechat_user_${Date.now()}`;
    const mockUsername = '微信用户';

    let socialLogin = await SocialLogin.findOne({
      where: { provider: 'wechat', providerUserId: mockOpenId },
    });

    let user;
    if (socialLogin) {
      user = await AdminUser.findByPk(socialLogin.userId);
      await socialLogin.update({ lastLoginAt: new Date() });
    } else {
      const randomPassword = crypto.randomBytes(8).toString('hex');
      const passwordHash = await bcrypt.hash(randomPassword, 10);
      user = await AdminUser.create({
        username: `wechat_${Date.now()}`,
        passwordHash,
        nickname: mockUsername,
        status: 1,
      });

      await SocialLogin.create({
        userId: user.id,
        provider: 'wechat',
        providerUserId: mockOpenId,
        providerUsername: mockUsername,
        lastLoginAt: new Date(),
      });
    }

    const token = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, {
      expiresIn: '24h',
    });
    const refreshToken = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '7d' });

    logger.info(`用户 ${user.username} 微信登录成功`);

    res.json({
      code: 200,
      message: '登录成功',
      data: {
        token,
        refreshToken,
        user: {
          id: user.id,
          username: user.username,
          nickname: user.nickname,
          avatar: user.avatar,
          roles: ['super_admin'],
        },
      },
    });
  } catch (error) {
    logger.error('微信登录失败:', error);
    res.status(500).json({ code: 500, message: '登录失败，请稍后重试' });
  }
};

const getBindStatus = async (req, res) => {
  try {
    const socialLogins = await SocialLogin.findAll({
      where: { userId: req.user.id },
      attributes: ['provider', 'providerUsername', 'lastLoginAt'],
    });

    const bindStatus = {
      qq: socialLogins.find(s => s.provider === 'qq') || null,
      wechat: socialLogins.find(s => s.provider === 'wechat') || null,
      email: socialLogins.find(s => s.provider === 'email') || null,
    };

    res.json({ code: 200, message: 'success', data: bindStatus });
  } catch (error) {
    logger.error('获取绑定状态失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { sendEmailCode, emailLogin, qqAuth, wechatAuth, getBindStatus };
