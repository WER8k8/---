const { sequelize, models } = require('../config/database');
const PublishTask = models.PublishTask || require('../models/PublishTask');
const GeneratedArticle = models.GeneratedArticle || require('../models/GeneratedArticle');
const PlatformAccount = models.PlatformAccount || require('../models/PlatformAccount');

const createPublishTask = async (req, res) => {
  try {
    const { article_id, platform_account_ids } = req.body;
    
    const article = await GeneratedArticle.findByPk(article_id);
    if (!article) return res.status(404).json({ code: 404, message: '文章不存在' });
    
    const tasks = [];
    for (const accountId of platform_account_ids) {
      const account = await PlatformAccount.findByPk(accountId);
      if (account) {
        const task = await PublishTask.create({
          article_id,
          platform_account_id: accountId,
          status: 0
        });
        tasks.push(task);
      }
    }
    
    res.json({ code: 200, message: `成功创建${tasks.length}个发布任务`, data: { taskIds: tasks.map(t => t.id) } });
  } catch (error) {
    console.error('创建任务失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getPublishTasks = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, status, article_id } = req.query;
    const where = {};
    if (status !== undefined) where.status = status;
    if (article_id) where.article_id = article_id;
    
    const result = await PublishTask.findAndCountAll({
      where,
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['created_at', 'DESC']],
      include: [
        { model: GeneratedArticle, attributes: ['title'] },
        { model: PlatformAccount, attributes: ['platform_name', 'account_name'] }
      ]
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
    console.error('获取任务失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getPublishTaskById = async (req, res) => {
  try {
    const { id } = req.params;
    const task = await PublishTask.findByPk(id, {
      include: [
        { model: GeneratedArticle, attributes: ['title'] },
        { model: PlatformAccount, attributes: ['platform_name', 'account_name'] }
      ]
    });
    if (!task) return res.status(404).json({ code: 404, message: '任务不存在' });
    res.json({ code: 200, message: 'success', data: task });
  } catch (error) {
    console.error('获取任务失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const retryPublishTask = async (req, res) => {
  try {
    const { id } = req.params;
    
    const task = await PublishTask.findByPk(id);
    if (!task) return res.status(404).json({ code: 404, message: '任务不存在' });
    
    if (task.retry_count >= 3) {
      return res.status(400).json({ code: 400, message: '已达到最大重试次数' });
    }
    
    await task.update({ 
      status: 0, 
      retry_count: task.retry_count + 1 
    });
    
    res.json({ code: 200, message: '任务已重新加入队列', data: task });
  } catch (error) {
    console.error('重试任务失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getPublishLogs = async (req, res) => {
  try {
    const { page = 1, pageSize = 20 } = req.query;
    
    const result = await PublishTask.findAndCountAll({
      where: { status: [2, 3] },
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize),
      order: [['executed_at', 'DESC']],
      include: [
        { model: GeneratedArticle, attributes: ['title'] },
        { model: PlatformAccount, attributes: ['platform_name', 'account_name'] }
      ]
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
    console.error('获取日志失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  createPublishTask, 
  getPublishTasks, 
  getPublishTaskById, 
  retryPublishTask,
  getPublishLogs 
};
