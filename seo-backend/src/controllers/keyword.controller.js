const { Op } = require('sequelize');
const { sequelize, models } = require('../config/database');
const IndustryKeyword = models.IndustryKeyword;
const LongtailKeyword = models.LongtailKeyword;

const getKeywords = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, keyword, category } = req.query;
    const where = {};
    if (keyword) where.keyword = { [Op.like]: `%${keyword}%` };
    if (category) where.category = category;
    
    const result = await IndustryKeyword.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['search_volume', 'DESC']]
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
    console.error('获取关键词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getKeywordById = async (req, res) => {
  try {
    const { id } = req.params;
    const keyword = await IndustryKeyword.findByPk(id);
    if (!keyword) return res.status(404).json({ code: 404, message: '关键词不存在' });
    res.json({ code: 200, message: 'success', data: keyword });
  } catch (error) {
    console.error('获取关键词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const createKeyword = async (req, res) => {
  try {
    const { keyword, category, search_volume = 0, difficulty = 0 } = req.body;
    if (!keyword) return res.status(400).json({ code: 400, message: '关键词不能为空' });
    
    const newKeyword = await IndustryKeyword.create({
      keyword,
      category,
      search_volume,
      difficulty
    });
    
    res.json({ code: 200, message: '创建成功', data: newKeyword });
  } catch (error) {
    console.error('创建关键词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updateKeyword = async (req, res) => {
  try {
    const { id } = req.params;
    const data = req.body;
    
    const keyword = await IndustryKeyword.findByPk(id);
    if (!keyword) return res.status(404).json({ code: 404, message: '关键词不存在' });
    
    await keyword.update(data);
    res.json({ code: 200, message: '更新成功', data: keyword });
  } catch (error) {
    console.error('更新关键词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const deleteKeyword = async (req, res) => {
  try {
    const { id } = req.params;
    const keyword = await IndustryKeyword.findByPk(id);
    if (!keyword) return res.status(404).json({ code: 404, message: '关键词不存在' });
    
    await keyword.destroy();
    res.json({ code: 200, message: '删除成功' });
  } catch (error) {
    console.error('删除关键词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const generateLongtailKeywords = async (req, res) => {
  try {
    const { keywordId, regionIds = [] } = req.body;
    
    const baseKeyword = await IndustryKeyword.findByPk(keywordId);
    if (!baseKeyword) return res.status(404).json({ code: 404, message: '关键词不存在' });
    
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
      `${baseKeyword.keyword}规格`
    ];
    
    const results = [];
    for (const regionId of regionIds) {
      for (const template of templates) {
        const longtail = await LongtailKeyword.create({
          region_id: regionId,
          keyword_id: keywordId,
          keyword: template
        });
        results.push(longtail);
      }
    }
    
    res.json({ code: 200, message: `成功生成${results.length}条长尾词`, data: results });
  } catch (error) {
    console.error('生成长尾词失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  getKeywords, 
  getKeywordById, 
  createKeyword, 
  updateKeyword, 
  deleteKeyword,
  generateLongtailKeywords 
};
