const { Op } = require('sequelize');
const { sequelize, models } = require('../config/database');
const GeneratedArticle = models.GeneratedArticle;
const ArticleTemplate = models.ArticleTemplate;
const Region = models.Region;

const getArticles = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, status, region_id, keyword } = req.query;
    const where = {};
    if (status !== undefined) where.status = status;
    if (region_id) where.region_id = region_id;
    if (keyword) where.title = { [Op.like]: `%${keyword}%` };
    
    const result = await GeneratedArticle.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['created_at', 'DESC']],
      include: [{ model: Region, attributes: ['name'] }, { model: ArticleTemplate, attributes: ['name'] }]
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
    console.error('获取文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getArticleById = async (req, res) => {
  try {
    const { id } = req.params;
    const article = await GeneratedArticle.findByPk(id, {
      include: [{ model: Region, attributes: ['name'] }, { model: ArticleTemplate, attributes: ['name'] }]
    });
    if (!article) return res.status(404).json({ code: 404, message: '文章不存在' });
    res.json({ code: 200, message: 'success', data: article });
  } catch (error) {
    console.error('获取文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const createArticle = async (req, res) => {
  try {
    const { title, content, region_id, keyword_id, template_id } = req.body;
    if (!title || !content) return res.status(400).json({ code: 400, message: '标题和内容不能为空' });
    
    const newArticle = await GeneratedArticle.create({
      title,
      content,
      region_id,
      keyword_id,
      template_id,
      word_count: content.length,
      duplicate_rate: 0,
      compliance_status: 1,
      status: 0
    });
    
    res.json({ code: 200, message: '创建成功', data: newArticle });
  } catch (error) {
    console.error('创建文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updateArticle = async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body;
    
    const article = await GeneratedArticle.findByPk(id);
    if (!article) return res.status(404).json({ code: 404, message: '文章不存在' });
    
    if (data.content) {
      data.word_count = data.content.length;
    }
    
    await article.update(data);
    res.json({ code: 200, message: '更新成功', data: article });
  } catch (error) {
    console.error('更新文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const deleteArticle = async (req, res) => {
  try {
    const { id } = req.params;
    const article = await GeneratedArticle.findByPk(id);
    if (!article) return res.status(404).json({ code: 404, message: '文章不存在' });
    
    await article.destroy();
    res.json({ code: 200, message: '删除成功' });
  } catch (error) {
    console.error('删除文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const generateArticles = async (req, res) => {
  try {
    const { region_ids, keyword_ids, template_id, count = 1 } = req.body;
    
    const template = await ArticleTemplate.findByPk(template_id);
    if (!template) return res.status(404).json({ code: 404, message: '模板不存在' });
    
    const results = [];
    const sampleContent = `这是一篇关于保温建材的文章内容。保温建材是建筑节能的重要组成部分，具有良好的保温隔热性能。\n\n主要特点：\n- 轻质高强\n- 保温隔热效果好\n- 防火性能优异\n- 施工方便快捷\n\n适用于各类建筑的外墙保温、屋面保温等工程。`;
    
    for (const region_id of region_ids) {
      for (const keyword_id of keyword_ids) {
        for (let i = 0; i < count; i++) {
          const region = await Region.findByPk(region_id);
          const title = `${region?.name || '本地'}保温建材厂家直销 - 优质产品推荐`;
          
          const article = await GeneratedArticle.create({
            title,
            content: sampleContent,
            region_id,
            keyword_id,
            template_id,
            word_count: sampleContent.length,
            duplicate_rate: Math.random() * 10,
            compliance_status: 1,
            status: 0
          });
          results.push(article);
        }
      }
    }
    
    res.json({ code: 200, message: `成功生成${results.length}篇文章`, data: results });
  } catch (error) {
    console.error('生成文章失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getArticleStats = async (req, res) => {
  try {
    const stats = await GeneratedArticle.findAll({
      attributes: [
        'status',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count']
      ],
      group: ['status']
    });
    
    const result = { total: 0, pending: 0, published: 0, offline: 0 };
    stats.forEach(s => {
      const status = s.status;
      if (status === 0) result.pending = parseInt(s.dataValues.count);
      else if (status === 1) result.published = parseInt(s.dataValues.count);
      else if (status === 2) result.offline = parseInt(s.dataValues.count);
      result.total += parseInt(s.dataValues.count);
    });
    
    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取统计失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  getArticles, 
  getArticleById, 
  createArticle, 
  updateArticle, 
  deleteArticle,
  generateArticles,
  getArticleStats 
};
