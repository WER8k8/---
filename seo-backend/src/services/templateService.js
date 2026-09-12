const { sequelize, models } = require('../config/database');
const ArticleTemplate = models.ArticleTemplate;

const getTemplates = async (params = {}) => {
  const { page = 1, pageSize = 20, keyword, category } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (keyword) where.name = { [Op.like]: `%${keyword}%` };
  if (category) where.category = category;

  const result = await ArticleTemplate.findAndCountAll({
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

const getTemplateById = async id => {
  return await ArticleTemplate.findByPk(id);
};

const createTemplate = async data => {
  return await ArticleTemplate.create(data);
};

const updateTemplate = async (id, data) => {
  const template = await ArticleTemplate.findByPk(id);
  if (!template) throw new Error('模板不存在');
  return await template.update(data);
};

const deleteTemplate = async id => {
  const template = await ArticleTemplate.findByPk(id);
  if (!template) throw new Error('模板不存在');
  await template.destroy();
  return true;
};

const copyTemplate = async id => {
  const original = await ArticleTemplate.findByPk(id);
  if (!original) throw new Error('模板不存在');

  const { dataValues } = original;
  delete dataValues.id;
  dataValues.name = `${original.name} (副本)`;

  return await ArticleTemplate.create(dataValues);
};

const previewTemplate = async (id, variables = {}) => {
  const template = await ArticleTemplate.findByPk(id);
  if (!template) throw new Error('模板不存在');

  let content = template.content;
  for (const [key, value] of Object.entries(variables)) {
    content = content.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }

  return { content };
};

const validateTemplate = async template => {
  const required = ['name', 'content', 'category'];
  const missing = required.filter(field => !template[field]);
  if (missing.length > 0) {
    throw new Error(`缺少必填字段: ${missing.join(', ')}`);
  }

  const variablePattern = /\{\{([^}]+)\}\}/g;
  const variables = [];
  let match;
  while ((match = variablePattern.exec(template.content)) !== null) {
    variables.push(match[1]);
  }

  return { valid: true, variables };
};

const getTemplateCategories = async () => {
  const categories = await ArticleTemplate.findAll({
    attributes: ['category', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['category'],
  });
  return categories;
};

module.exports = {
  getTemplates,
  getTemplateById,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  copyTemplate,
  previewTemplate,
  validateTemplate,
  getTemplateCategories,
};
