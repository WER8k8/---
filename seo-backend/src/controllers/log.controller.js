const { Op } = require('sequelize');
const { sequelize, models } = require('../config/database');
const OperationLog = models.OperationLog;
const LoginLog = models.LoginLog;

const getOperationLogs = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, module, username } = req.query;
    const where = {};
    if (module) where.module = module;
    if (username) where.username = { [Op.like]: `%${username}%` };
    
    const result = await OperationLog.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['created_at', 'DESC']]
    });
    
    res.json({ 
      code: 200, 
      message: 'success', 
      data: {
        list: result.rows,
        total: result.count,
        page: parseInt(page),
        pageSize: parseInt(pageSize)
      }
    });
  } catch (error) {
    console.error('获取操作日志失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getLoginLogs = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, username, login_result } = req.query;
    const where = {};
    if (username) where.username = { [Op.like]: `%${username}%` };
    if (login_result !== undefined) where.login_result = login_result;
    
    const result = await LoginLog.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['created_at', 'DESC']]
    });
    
    res.json({ 
      code: 200, 
      message: 'success', 
      data: {
        list: result.rows,
        total: result.count,
        page: parseInt(page),
        pageSize: parseInt(pageSize)
      }
    });
  } catch (error) {
    console.error('获取登录日志失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const createOperationLog = async (userId, username, module, action, description, ipAddress, userAgent) => {
  try {
    await OperationLog.create({
      user_id: userId,
      username,
      module,
      action,
      description,
      ip_address: ipAddress || '',
      user_agent: userAgent || ''
    });
  } catch (error) {
    console.error('记录操作日志失败:', error);
  }
};

const createLoginLog = async (userId, username, ipAddress, device, loginResult, failReason) => {
  try {
    await LoginLog.create({
      user_id: userId,
      username,
      ip_address: ipAddress || '',
      device: device || '',
      login_result: loginResult ? 1 : 0,
      fail_reason: failReason || ''
    });
  } catch (error) {
    console.error('记录登录日志失败:', error);
  }
};

module.exports = { 
  getOperationLogs, 
  getLoginLogs,
  createOperationLog,
  createLoginLog
};
