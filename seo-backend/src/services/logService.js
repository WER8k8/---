const { sequelize, models } = require('../config/database');
const OperationLog = models.OperationLog;
const LoginLog = models.LoginLog;

const getOperationLogs = async (params = {}) => {
  const { page = 1, pageSize = 20, userId, action, startDate, endDate } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (userId) where.user_id = userId;
  if (action) where.action = action;
  if (startDate || endDate) {
    where.created_at = {};
    if (startDate) where.created_at[Op.gte] = startDate;
    if (endDate) where.created_at[Op.lte] = endDate;
  }

  const result = await OperationLog.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [['created_at', 'DESC']],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getLoginLogs = async (params = {}) => {
  const { page = 1, pageSize = 20, userId, status, startDate, endDate } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (userId) where.user_id = userId;
  if (status !== undefined) where.status = status;
  if (startDate || endDate) {
    where.created_at = {};
    if (startDate) where.created_at[Op.gte] = startDate;
    if (endDate) where.created_at[Op.lte] = endDate;
  }

  const result = await LoginLog.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [['created_at', 'DESC']],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getLogById = async (id, type = 'operation') => {
  const Model = type === 'login' ? LoginLog : OperationLog;
  return await Model.findByPk(id);
};

const createOperationLog = async (userId, action, detail, req = null) => {
  return await OperationLog.create({
    user_id: userId,
    action,
    detail,
    ip: req?.ip || req?.connection?.remoteAddress || 'unknown',
    user_agent: req?.headers?.['user-agent'] || '',
  });
};

const createLoginLog = async (userId, status, message, req = null) => {
  return await LoginLog.create({
    user_id: userId,
    status,
    message,
    ip: req?.ip || req?.connection?.remoteAddress || 'unknown',
    user_agent: req?.headers?.['user-agent'] || '',
  });
};

const cleanLogs = async data => {
  const { type, beforeDate } = data;
  const { Op } = require('sequelize');

  if (type === 'operation' || type === 'all') {
    await OperationLog.destroy({
      where: { created_at: { [Op.lt]: new Date(beforeDate) } },
    });
  }

  if (type === 'login' || type === 'all') {
    await LoginLog.destroy({
      where: { created_at: { [Op.lt]: new Date(beforeDate) } },
    });
  }

  return { message: '日志清理完成' };
};

const getLogStats = async (days = 30) => {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  const operationStats = await OperationLog.findAll({
    attributes: ['action', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    where: { created_at: { [sequelize.Sequelize.Op.gte]: startDate } },
    group: ['action'],
  });

  const loginStats = await LoginLog.findAll({
    attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    where: { created_at: { [sequelize.Sequelize.Op.gte]: startDate } },
    group: ['status'],
  });

  return { operationStats, loginStats };
};

module.exports = {
  getOperationLogs,
  getLoginLogs,
  getLogById,
  createOperationLog,
  createLoginLog,
  cleanLogs,
  getLogStats,
};
