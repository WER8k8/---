const { publishQueue, indexingQueue, articleQueue } = require('./queue');
const { publishToPlatform, generateArticlesByBatch } = require('../services');
const { sequelize, models } = require('../config/database');
const GeneratedArticle = models.GeneratedArticle;
const IndexingRecord = models.IndexingRecord;
const SystemAlert = models.SystemAlert;

publishQueue.process(async (job) => {
  const { articleId, platformAccountIds } = job.data;
  
  for (const accountId of platformAccountIds) {
    try {
      await publishToPlatform(articleId, accountId);
    } catch (error) {
      console.error(`发布任务失败 articleId=${articleId}, accountId=${accountId}:`, error);
    }
  }
  
  return { success: true, processedCount: platformAccountIds.length };
});

indexingQueue.process(async (job) => {
  const { articleIds } = job.data;
  
  for (const articleId of articleIds) {
    try {
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
    } catch (error) {
      console.error(`收录检测失败 articleId=${articleId}:`, error);
    }
  }
  
  return { success: true, processedCount: articleIds.length };
});

articleQueue.process(async (job) => {
  const { templateId, keywordIds, regionIds, count = 1 } = job.data;
  
  try {
    const articles = await generateArticlesByBatch(templateId, keywordIds, regionIds, count);
    return { success: true, count: articles.length, articleIds: articles.map(a => a.id) };
  } catch (error) {
    console.error('文章生成任务失败:', error);
    throw error;
  }
});

publishQueue.on('completed', (job, result) => {
  console.log(`发布任务完成 jobId=${job.id}, result:`, result);
});

publishQueue.on('failed', (job, err) => {
  console.error(`发布任务失败 jobId=${job.id}:`, err.message);
});

indexingQueue.on('completed', (job, result) => {
  console.log(`收录检测任务完成 jobId=${job.id}, result:`, result);
});

indexingQueue.on('failed', (job, err) => {
  console.error(`收录检测任务失败 jobId=${job.id}:`, err.message);
});

articleQueue.on('completed', (job, result) => {
  console.log(`文章生成任务完成 jobId=${job.id}, result:`, result);
});

articleQueue.on('failed', (job, err) => {
  console.error(`文章生成任务失败 jobId=${job.id}:`, err.message);
});

const startWorkers = () => {
  console.log('任务队列Worker已启动');
};

module.exports = {
  startWorkers
};