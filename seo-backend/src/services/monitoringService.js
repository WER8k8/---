const { sequelize, models } = require('../config/database');
const IndexingRecord = models.IndexingRecord;
const GeneratedArticle = models.GeneratedArticle;
const SystemAlert = models.SystemAlert;
const { addIndexingJob } = require('../tasks/queue');

const getRecords = async (params = {}) => {
  const { page = 1, pageSize = 20, keyword, isIndexed, searchEngine, startDate, endDate } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (keyword) where.keyword = { [Op.like]: `%${keyword}%` };
  if (isIndexed !== undefined) where.is_indexed = isIndexed ? 1 : 0;
  if (searchEngine) where.search_engine = searchEngine;
  if (startDate || endDate) {
    where.checked_at = {};
    if (startDate) where.checked_at[Op.gte] = startDate;
    if (endDate) where.checked_at[Op.lte] = endDate;
  }

  const result = await IndexingRecord.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [['checked_at', 'DESC']],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getStats = async () => {
  const total = await IndexingRecord.count();
  const indexed = await IndexingRecord.count({ where: { is_indexed: 1 } });
  const notIndexed = await IndexingRecord.count({ where: { is_indexed: 0 } });

  const byEngine = await IndexingRecord.findAll({
    attributes: [
      'search_engine',
      [sequelize.fn('COUNT', sequelize.col('id')), 'total'],
      [sequelize.fn('SUM', sequelize.col('is_indexed')), 'indexed'],
    ],
    group: ['search_engine'],
  });

  const rate = total > 0 ? ((indexed / total) * 100).toFixed(2) : 0;
  return { total, indexed, notIndexed, rate: parseFloat(rate), byEngine };
};

const getTrend = async (days = 7) => {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  const records = await IndexingRecord.findAll({
    where: {
      checked_at: { [sequelize.Sequelize.Op.gte]: startDate },
    },
    attributes: [
      [sequelize.fn('DATE', sequelize.col('checked_at')), 'date'],
      [sequelize.fn('COUNT', sequelize.col('id')), 'total'],
      [sequelize.fn('SUM', sequelize.col('is_indexed')), 'indexed'],
    ],
    group: [sequelize.fn('DATE', sequelize.col('checked_at'))],
    order: [[sequelize.fn('DATE', sequelize.col('checked_at')), 'ASC']],
  });

  return records;
};

const batchCheck = async articleIds => {
  const job = await addIndexingJob(articleIds);
  return { jobId: job.id, message: '批量检测任务已创建' };
};

const checkSingle = async articleId => {
  const article = await GeneratedArticle.findByPk(articleId);
  if (!article) throw new Error('文章不存在');

  const record = await IndexingRecord.create({
    article_id: articleId,
    search_engine: 'baidu',
    keyword: article.title,
    is_indexed: Math.random() > 0.3 ? 1 : 0,
    ranking: Math.random() > 0.5 ? Math.floor(Math.random() * 20) + 1 : 0,
    is_homepage: Math.random() > 0.8 ? 1 : 0,
    checked_at: new Date(),
  });

  return record;
};

const getAlerts = async (params = {}) => {
  const { page = 1, pageSize = 20, type, isHandled } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (type) where.type = type;
  if (isHandled !== undefined) where.is_handled = isHandled ? 1 : 0;

  const result = await SystemAlert.findAndCountAll({
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

const handleAlert = async (id, data) => {
  const alert = await SystemAlert.findByPk(id);
  if (!alert) throw new Error('预警不存在');

  await alert.update({
    is_handled: 1,
    handled_at: new Date(),
    handled_by: data.handledBy || 'system',
    handling_note: data.note || '',
  });

  return alert;
};

const createAlert = async (type, message, data = {}) => {
  return await SystemAlert.create({
    type,
    message,
    level: data.level || 'warning',
    data: JSON.stringify(data),
    is_handled: 0,
  });
};

const getSchedule = async () => {
  const SystemConfig = models.SystemConfig;
  const config = await SystemConfig.findOne({ where: { group: 'indexing', key: 'schedule' } });
  return config ? JSON.parse(config.value) : { enabled: false, interval: 'daily', time: '03:00' };
};

const setSchedule = async schedule => {
  const SystemConfig = models.SystemConfig;
  await SystemConfig.upsert({
    group: 'indexing',
    key: 'schedule',
    value: JSON.stringify(schedule),
  });
  return schedule;
};

module.exports = {
  getRecords,
  getStats,
  getTrend,
  batchCheck,
  checkSingle,
  getAlerts,
  handleAlert,
  createAlert,
  getSchedule,
  setSchedule,
};
