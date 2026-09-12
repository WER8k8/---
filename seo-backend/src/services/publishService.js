const { sequelize, models } = require('../config/database');
const PublishTask = models.PublishTask;
const GeneratedArticle = models.GeneratedArticle;
const { addPublishJob } = require('../tasks/queue');

const getTasks = async (params = {}) => {
  const { page = 1, pageSize = 20, status, articleId, platformId, startDate, endDate } = params;
  const { Op } = require('sequelize');
  const where = {};
  if (status !== undefined) where.status = status;
  if (articleId) where.article_id = articleId;
  if (platformId) where.platform_id = platformId;
  if (startDate || endDate) {
    where.created_at = {};
    if (startDate) where.created_at[Op.gte] = startDate;
    if (endDate) where.created_at[Op.lte] = endDate;
  }

  const result = await PublishTask.findAndCountAll({
    where,
    offset: (parseInt(page) - 1) * pageSize,
    limit: parseInt(pageSize),
    order: [['created_at', 'DESC']],
    include: [{ model: GeneratedArticle, as: 'article' }],
  });

  return {
    list: result.rows,
    total: result.count,
    page: parseInt(page),
    pageSize: parseInt(pageSize),
  };
};

const getTaskById = async id => {
  return await PublishTask.findByPk(id, {
    include: [{ model: GeneratedArticle, as: 'article' }],
  });
};

const createTask = async data => {
  const task = await PublishTask.create({
    ...data,
    status: 0,
  });

  await addPublishJob(task.article_id, [task.account_id]);

  return task;
};

const updateTask = async (id, data) => {
  const task = await PublishTask.findByPk(id);
  if (!task) throw new Error('任务不存在');
  return await task.update(data);
};

const cancelTask = async id => {
  const task = await PublishTask.findByPk(id);
  if (!task) throw new Error('任务不存在');
  if (task.status === 2) throw new Error('已完成的任务无法取消');

  await task.update({ status: 4 });
  return task;
};

const retryTask = async id => {
  const task = await PublishTask.findByPk(id);
  if (!task) throw new Error('任务不存在');
  if (task.status !== 3) throw new Error('只能重试失败的任务');

  await task.update({ status: 0, retry_count: task.retry_count + 1, error_message: null });
  await addPublishJob(task.article_id, [task.account_id]);

  return task;
};

const deleteTask = async id => {
  const task = await PublishTask.findByPk(id);
  if (!task) throw new Error('任务不存在');
  await task.destroy();
  return true;
};

const batchCreateTasks = async tasks => {
  const created = [];
  for (const taskData of tasks) {
    const task = await PublishTask.create({
      ...taskData,
      status: 0,
    });
    created.push(task);
    await addPublishJob(task.article_id, [task.account_id]);
  }
  return created;
};

const getTaskLogs = async taskId => {
  return await PublishTask.findByPk(taskId, {
    attributes: ['id', 'logs', 'created_at', 'updated_at'],
  });
};

const getTaskStats = async () => {
  const total = await PublishTask.count();
  const pending = await PublishTask.count({ where: { status: 0 } });
  const processing = await PublishTask.count({ where: { status: 1 } });
  const completed = await PublishTask.count({ where: { status: 2 } });
  const failed = await PublishTask.count({ where: { status: 3 } });

  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayTotal = await PublishTask.count({
    where: { created_at: { [sequelize.Sequelize.Op.gte]: todayStart } },
  });

  return { total, pending, processing, completed, failed, todayTotal };
};

const updateTaskStatus = async (id, status, logs = null) => {
  const task = await PublishTask.findByPk(id);
  if (!task) throw new Error('任务不存在');

  const updateData = { status };
  if (logs) {
    updateData.logs = task.logs ? `${task.logs}\n${logs}` : logs;
  }

  await task.update(updateData);
  return task;
};

const markTaskSuccess = async (id, result) => {
  return await updateTaskStatus(id, 2, `发布成功: ${JSON.stringify(result)}`);
};

const markTaskFailed = async (id, errorMessage) => {
  return await updateTaskStatus(id, 3, `发布失败: ${errorMessage}`);
};

module.exports = {
  getTasks,
  getTaskById,
  createTask,
  updateTask,
  cancelTask,
  retryTask,
  deleteTask,
  batchCreateTasks,
  getTaskLogs,
  getTaskStats,
  updateTaskStatus,
  markTaskSuccess,
  markTaskFailed,
};
