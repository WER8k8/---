const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { models } = require('../config/database');

const refreshToken = async (req, res) => {
  try {
    const { refreshToken } = req.body;
    if (!refreshToken) {
      return res.status(400).json({ code: 400, message: '请提供刷新令牌' });
    }

    const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET);
    const user = await models.AdminUser.findByPk(decoded.id);

    if (!user || user.status !== 1) {
      return res.status(401).json({ code: 401, message: '用户不存在或已被禁用' });
    }

    const newToken = jwt.sign({ id: user.id, username: user.username }, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '24h',
    });

    res.json({ code: 200, message: 'success', data: { token: newToken, refreshToken } });
  } catch (error) {
    res.status(401).json({ code: 401, message: '刷新令牌无效' });
  }
};

const getProfile = async (req, res) => {
  try {
    const user = await models.AdminUser.findByPk(req.user.id, {
      attributes: { exclude: ['passwordHash'] },
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

    const user = await models.AdminUser.findByPk(req.user.id);
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

module.exports = { refreshToken, getProfile, updatePassword };
