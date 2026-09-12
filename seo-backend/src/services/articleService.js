const { sequelize, models } = require('../config/database');
const GeneratedArticle = models.GeneratedArticle;
const IndexingRecord = models.IndexingRecord;
const { generateArticle } = require('./aiGenerator');

const getArticles = async (params = {}) => {
  const { page = 1, pageSize = 20, keyword, status, templateId, startDate, endDate } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (keyword) where.title = { [Op.like]: `%${keyword}%` };
  if (status !== undefined) where.status = status;
  if (templateId) where.template_id = templateId;
  if (startDate || endDate) {
    where.created_at = {};
    if (startDate) where.created_at[Op.gte] = startDate;
    if (endDate) where.created_at[Op.lte] = endDate;
  }

  const result = await GeneratedArticle.findAndCountAll({
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

const getArticleById = async id => {
  const article = await GeneratedArticle.findByPk(id, {
    include: [{ model: IndexingRecord, as: 'indexingRecords' }],
  });
  return article;
};

const createArticle = async data => {
  return await GeneratedArticle.create(data);
};

const updateArticle = async (id, data) => {
  const article = await GeneratedArticle.findByPk(id);
  if (!article) throw new Error('文章不存在');
  return await article.update(data);
};

const deleteArticle = async id => {
  const article = await GeneratedArticle.findByPk(id);
  if (!article) throw new Error('文章不存在');
  await article.destroy();
  return true;
};

const batchDeleteArticles = async ids => {
  await GeneratedArticle.destroy({ where: { id: ids } });
  return true;
};

const generateArticleByTemplate = async (templateId, keyword, regionName) => {
  const content = await generateArticle(templateId, keyword, regionName);
  return await GeneratedArticle.create({
    title: `${keyword} - ${regionName}`,
    content,
    template_id: templateId,
    keyword,
    region: regionName,
    status: 1,
    word_count: content.length,
  });
};

const batchGenerateArticles = async (templateId, keywordIds, regionIds, count = 1) => {
  const articles = [];
  for (const keywordId of keywordIds) {
    for (const regionId of regionIds) {
      for (let i = 0; i < count; i++) {
        const article = await generateArticleByTemplate(
          templateId,
          `关键词${keywordId}`,
          `地域${regionId}`
        );
        articles.push(article);
      }
    }
  }
  return articles;
};

const getArticleStats = async () => {
  const total = await GeneratedArticle.count();
  const byStatus = await GeneratedArticle.findAll({
    attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['status'],
  });

  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayCount = await GeneratedArticle.count({
    where: { created_at: { [sequelize.Sequelize.Op.gte]: todayStart } },
  });

  return { total, byStatus, todayCount };
};

const getArticlesByKeyword = async keyword => {
  return await GeneratedArticle.findAll({
    where: { keyword: { [sequelize.Sequelize.Op.like]: `%${keyword}%` } },
  });
};

const getArticlesByRegion = async region => {
  return await GeneratedArticle.findAll({
    where: { region },
  });
};

module.exports = {
  getArticles,
  getArticleById,
  createArticle,
  updateArticle,
  deleteArticle,
  batchDeleteArticles,
  generateArticleByTemplate,
  batchGenerateArticles,
  getArticleStats,
  getArticlesByKeyword,
  getArticlesByRegion,
};
