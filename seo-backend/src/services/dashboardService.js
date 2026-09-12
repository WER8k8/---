const { sequelize, models } = require('../config/database');
const GeneratedArticle = models.GeneratedArticle;
const IndexingRecord = models.IndexingRecord;
const PublishTask = models.PublishTask;
const Region = models.Region;
const IndustryKeyword = models.IndustryKeyword;

const getStats = async () => {
  const totalRegions = await Region.count({ where: { status: 1 } });
  const totalKeywords = await IndustryKeyword.count();
  const totalArticles = await GeneratedArticle.count();

  const indexedCount = await IndexingRecord.count({ where: { is_indexed: 1 } });
  const totalChecked = await IndexingRecord.count();
  const successRate = totalChecked > 0 ? ((indexedCount / totalChecked) * 100).toFixed(1) : 0;

  return {
    totalRegions,
    totalKeywords,
    totalArticles,
    successRate: parseFloat(successRate),
  };
};

const getTodayStats = async () => {
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);

  const generated = await GeneratedArticle.count({
    where: { created_at: { [sequelize.Sequelize.Op.gte]: todayStart } },
  });

  const published = await PublishTask.count({
    where: {
      status: 2,
      updated_at: { [sequelize.Sequelize.Op.gte]: todayStart },
    },
  });

  const failed = await PublishTask.count({
    where: {
      status: 3,
      updated_at: { [sequelize.Sequelize.Op.gte]: todayStart },
    },
  });

  const indexed = await IndexingRecord.count({
    where: {
      is_indexed: 1,
      checked_at: { [sequelize.Sequelize.Op.gte]: todayStart },
    },
  });

  return { generated, published, failed, indexed };
};

const getTrend = async (params = {}) => {
  const { days = 7 } = params;
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  const records = await GeneratedArticle.findAll({
    where: { created_at: { [sequelize.Sequelize.Op.gte]: startDate } },
    attributes: [
      [sequelize.fn('DATE', sequelize.col('created_at')), 'date'],
      [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
    ],
    group: [sequelize.fn('DATE', sequelize.col('created_at'))],
    order: [[sequelize.fn('DATE', sequelize.col('created_at')), 'ASC']],
  });

  return records;
};

const getDistribution = async () => {
  const byStatus = await GeneratedArticle.findAll({
    attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['status'],
  });

  const byCategory = await IndustryKeyword.findAll({
    attributes: ['category', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['category'],
  });

  const byRegion = await Region.findAll({
    attributes: ['name', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    include: [
      {
        model: GeneratedArticle,
        as: 'articles',
        attributes: [],
      },
    ],
    group: ['Region.name'],
  });

  return { byStatus, byCategory, byRegion };
};

const getRealTime = async () => {
  const pendingTasks = await PublishTask.count({ where: { status: 0 } });
  const processingTasks = await PublishTask.count({ where: { status: 1 } });
  const todayPublished = await PublishTask.count({
    where: {
      status: 2,
      updated_at: { [sequelize.Sequelize.Op.gte]: new Date(new Date().setHours(0, 0, 0, 0)) },
    },
  });

  return {
    pendingTasks,
    processingTasks,
    todayPublished,
    serverStatus: 'running',
    timestamp: new Date().toISOString(),
  };
};

const getWeeklyReport = async () => {
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);

  const articlesGenerated = await GeneratedArticle.count({
    where: { created_at: { [sequelize.Sequelize.Op.gte]: weekAgo } },
  });

  const tasksCompleted = await PublishTask.count({
    where: {
      status: 2,
      updated_at: { [sequelize.Sequelize.Op.gte]: weekAgo },
    },
  });

  const avgSuccessRate = await getStats();

  return {
    articlesGenerated,
    tasksCompleted,
    avgSuccessRate: avgSuccessRate.successRate,
    period: { start: weekAgo, end: new Date() },
  };
};

module.exports = {
  getStats,
  getTodayStats,
  getTrend,
  getDistribution,
  getRealTime,
  getWeeklyReport,
};
