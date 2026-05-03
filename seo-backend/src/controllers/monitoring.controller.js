const { sequelize, models } = require('../config/database');
const IndexingRecord = models.IndexingRecord || require('../models/IndexingRecord');
const GeneratedArticle = models.GeneratedArticle || require('../models/GeneratedArticle');
const SystemAlert = models.SystemAlert || require('../models/SystemAlert');

const getIndexingRecords = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, is_indexed, article_id } = req.query;
    const where = {};
    if (is_indexed !== undefined) where.is_indexed = is_indexed;
    if (article_id) where.article_id = article_id;
    
    const result = await IndexingRecord.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['checked_at', 'DESC']],
      include: [{ model: GeneratedArticle, attributes: ['title'] }]
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
    console.error('获取收录记录失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const checkIndex = async (req, res) => {
  try {
    const { article_ids } = req.body;
    
    for (const articleId of article_ids) {
      const article = await GeneratedArticle.findByPk(articleId);
      if (article) {
        await IndexingRecord.create({
          article_id: articleId,
          search_engine: 'baidu',
          keyword: article.title,
          is_indexed: Math.random() > 0.3 ? 1 : 0,
          ranking: Math.random() > 0.5 ? Math.floor(Math.random() * 20) + 1 : 0,
          is_homepage: Math.random() > 0.8 ? 1 : 0,
          checked_at: new Date()
        });
      }
    }
    
    res.json({ code: 200, message: '收录检测任务已提交', data: { taskId: 'task_' + Date.now() } });
  } catch (error) {
    console.error('提交检测任务失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getAlerts = async (req, res) => {
  try {
    const alerts = await SystemAlert.findAll({
      where: { status: [1, 2] },
      order: [['created_at', 'DESC']]
    });
    
    const result = {
      accountAlerts: alerts.filter(a => a.type === 'account'),
      publishAlerts: alerts.filter(a => a.type === 'publish'),
      regionAlerts: alerts.filter(a => a.type === 'region')
    };
    
    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取预警失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const handleAlert = async (req, res) => {
  try {
    const { id } = req.params;
    
    const alert = await SystemAlert.findByPk(id);
    if (!alert) return res.status(404).json({ code: 404, message: '预警不存在' });
    
    await alert.update({ status: 3 });
    res.json({ code: 200, message: '预警已处理', data: alert });
  } catch (error) {
    console.error('处理预警失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  getIndexingRecords, 
  checkIndex, 
  getAlerts, 
  handleAlert 
};
