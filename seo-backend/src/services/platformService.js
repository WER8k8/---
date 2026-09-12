const { sequelize, models } = require('../config/database');
const Platform = models.Platform;
const PlatformAccount = models.PlatformAccount;

const getPlatforms = async (params = {}) => {
  const { page = 1, pageSize = 20, keyword, status } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (keyword) where.name = { [Op.like]: `%${keyword}%` };
  if (status !== undefined) where.status = status;

  const result = await Platform.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [
      ['sort_order', 'ASC'],
      ['id', 'ASC'],
    ],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getPlatformById = async id => {
  return await Platform.findByPk(id, {
    include: [{ model: PlatformAccount, as: 'accounts' }],
  });
};

const createPlatform = async data => {
  return await Platform.create(data);
};

const updatePlatform = async (id, data) => {
  const platform = await Platform.findByPk(id);
  if (!platform) throw new Error('平台不存在');
  return await platform.update(data);
};

const deletePlatform = async id => {
  const platform = await Platform.findByPk(id);
  if (!platform) throw new Error('平台不存在');
  await platform.destroy();
  return true;
};

const getPlatformAccounts = async platformId => {
  return await PlatformAccount.findAll({
    where: { platform_id: platformId, status: 1 },
  });
};

const getAccountById = async id => {
  return await PlatformAccount.findByPk(id);
};

const addPlatformAccount = async (platformId, data) => {
  return await PlatformAccount.create({
    ...data,
    platform_id: platformId,
  });
};

const updatePlatformAccount = async (id, data) => {
  const account = await PlatformAccount.findByPk(id);
  if (!account) throw new Error('账号不存在');
  return await account.update(data);
};

const deletePlatformAccount = async id => {
  const account = await PlatformAccount.findByPk(id);
  if (!account) throw new Error('账号不存在');
  await account.destroy();
  return true;
};

const testPlatformConnection = async accountId => {
  const account = await PlatformAccount.findByPk(accountId);
  if (!account) throw new Error('账号不存在');

  const platform = await Platform.findByPk(account.platform_id);
  const { testConnection } = require('./platformAdapter');

  try {
    const result = await testConnection(platform, account);
    return { success: true, message: '连接成功', data: result };
  } catch (error) {
    return { success: false, message: error.message };
  }
};

const getPlatformStats = async () => {
  const totalPlatforms = await Platform.count({ where: { status: 1 } });
  const totalAccounts = await PlatformAccount.count({ where: { status: 1 } });

  const accountsByPlatform = await PlatformAccount.findAll({
    attributes: ['platform_id', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    where: { status: 1 },
    group: ['platform_id'],
  });

  return { totalPlatforms, totalAccounts, accountsByPlatform };
};

const enableAccount = async id => {
  const account = await PlatformAccount.findByPk(id);
  if (!account) throw new Error('账号不存在');
  await account.update({ status: 1 });
  return account;
};

const disableAccount = async id => {
  const account = await PlatformAccount.findByPk(id);
  if (!account) throw new Error('账号不存在');
  await account.update({ status: 0 });
  return account;
};

module.exports = {
  getPlatforms,
  getPlatformById,
  createPlatform,
  updatePlatform,
  deletePlatform,
  getPlatformAccounts,
  getAccountById,
  addPlatformAccount,
  updatePlatformAccount,
  deletePlatformAccount,
  testPlatformConnection,
  getPlatformStats,
  enableAccount,
  disableAccount,
};
