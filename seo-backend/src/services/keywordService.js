const { sequelize, models } = require('../config/database');
const IndustryKeyword = models.IndustryKeyword;
const LongtailKeyword = models.LongtailKeyword;
const { generateKeywords } = require('./aiGenerator');

const getKeywords = async (params = {}) => {
  const { page = 1, pageSize = 20, keyword, category } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (keyword) where.keyword = { [Op.like]: `%${keyword}%` };
  if (category) where.category = category;

  const result = await IndustryKeyword.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [['search_volume', 'DESC']],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getKeywordById = async id => {
  return await IndustryKeyword.findByPk(id);
};

const createKeyword = async data => {
  return await IndustryKeyword.create(data);
};

const updateKeyword = async (id, data) => {
  const keyword = await IndustryKeyword.findByPk(id);
  if (!keyword) throw new Error('关键词不存在');
  return await keyword.update(data);
};

const deleteKeyword = async id => {
  const keyword = await IndustryKeyword.findByPk(id);
  if (!keyword) throw new Error('关键词不存在');
  await keyword.destroy();
  return true;
};

const batchCreateKeywords = async keywords => {
  const results = await IndustryKeyword.bulkCreate(keywords);
  return results;
};

const generateLongtailKeywords = async (keywordId, regionIds = []) => {
  const baseKeyword = await IndustryKeyword.findByPk(keywordId);
  if (!baseKeyword) throw new Error('关键词不存在');

  const templates = [
    `${baseKeyword.keyword}价格`,
    `${baseKeyword.keyword}厂家`,
    `${baseKeyword.keyword}批发`,
    `${baseKeyword.keyword}供应商`,
    `${baseKeyword.keyword}报价`,
    `${baseKeyword.keyword}多少钱`,
    `${baseKeyword.keyword}哪家好`,
    `${baseKeyword.keyword}生产厂家`,
    `${baseKeyword.keyword}品牌`,
    `${baseKeyword.keyword}规格`,
  ];

  const results = [];
  for (const regionId of regionIds) {
    for (const template of templates) {
      const longtail = await LongtailKeyword.create({
        region_id: regionId,
        keyword_id: keywordId,
        keyword: template,
      });
      results.push(longtail);
    }
  }

  return results;
};

const generateKeywordsByAI = async (seedKeyword, count = 50) => {
  return await generateKeywords(seedKeyword, count);
};

const getIndustries = async () => {
  const { Op } = require('sequelize');
  const industries = await IndustryKeyword.findAll({
    attributes: ['category', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    where: { category: { [Op.ne]: null } },
    group: ['category'],
  });
  return industries;
};

const getKeywordStats = async () => {
  const total = await IndustryKeyword.count();
  const byCategory = await IndustryKeyword.findAll({
    attributes: ['category', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['category'],
  });
  return { total, byCategory };
};

module.exports = {
  getKeywords,
  getKeywordById,
  createKeyword,
  updateKeyword,
  deleteKeyword,
  batchCreateKeywords,
  generateLongtailKeywords,
  generateKeywordsByAI,
  getIndustries,
  getKeywordStats,
};
