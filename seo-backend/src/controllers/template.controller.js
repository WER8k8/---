const { Op } = require('sequelize');
const { sequelize, models } = require('../config/database');
const ArticleTemplate = models.ArticleTemplate;

const getTemplates = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, name, category } = req.query;
    const where = {};
    if (name) where.name = { [Op.like]: `%${name}%` };
    if (category) where.category = category;
    
    const result = await ArticleTemplate.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize)
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
    console.error('获取模板失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getTemplateById = async (req, res) => {
  try {
    const { id } = req.params;
    const template = await ArticleTemplate.findByPk(id);
    if (!template) return res.status(404).json({ code: 404, message: '模板不存在' });
    res.json({ code: 200, message: 'success', data: template });
  } catch (error) {
    console.error('获取模板失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const createTemplate = async (req, res) => {
  try {
    const { name, category, content, variables } = req.body;
    if (!name || !content) return res.status(400).json({ code: 400, message: '名称和内容不能为空' });
    
    const newTemplate = await ArticleTemplate.create({
      name,
      category,
      content,
      variables: typeof variables === 'object' ? JSON.stringify(variables) : null
    });
    
    res.json({ code: 200, message: '创建成功', data: newTemplate });
  } catch (error) {
    console.error('创建模板失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updateTemplate = async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body;
    
    const template = await ArticleTemplate.findByPk(id);
    if (!template) return res.status(404).json({ code: 404, message: '模板不存在' });
    
    if (data.variables && typeof data.variables === 'object') {
      data.variables = JSON.stringify(data.variables);
    }
    
    await template.update(data);
    res.json({ code: 200, message: '更新成功', data: template });
  } catch (error) {
    console.error('更新模板失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const deleteTemplate = async (req, res) => {
  try {
    const { id } = req.params;
    const template = await ArticleTemplate.findByPk(id);
    if (!template) return res.status(404).json({ code: 404, message: '模板不存在' });
    
    await template.destroy();
    res.json({ code: 200, message: '删除成功' });
  } catch (error) {
    console.error('删除模板失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  getTemplates, 
  getTemplateById, 
  createTemplate, 
  updateTemplate, 
  deleteTemplate 
};
