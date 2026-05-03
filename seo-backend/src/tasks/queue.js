require('dotenv').config();
const Queue = require('bull');

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

const publishQueue = new Queue('publish', REDIS_URL, {
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000
    },
    removeOnComplete: 1000,
    removeOnFail: 500
  }
});

const indexingQueue = new Queue('indexing', REDIS_URL, {
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 5000
    },
    removeOnComplete: 1000,
    removeOnFail: 500
  }
});

const articleQueue = new Queue('article', REDIS_URL, {
  defaultJobOptions: {
    attempts: 2,
    backoff: {
      type: 'fixed',
      delay: 2000
    },
    removeOnComplete: 1000,
    removeOnFail: 500
  }
});

const queues = {
  publish: publishQueue,
  indexing: indexingQueue,
  article: articleQueue
};

const addPublishJob = async (articleId, platformAccountIds) => {
  const job = await publishQueue.add({
    articleId,
    platformAccountIds
  }, {
    delay: 0,
    priority: 1
  });
  
  return job;
};

const addIndexingJob = async (articleIds) => {
  const job = await indexingQueue.add({
    articleIds
  }, {
    delay: 60000,
    priority: 2
  });
  
  return job;
};

const addArticleJob = async (templateId, keywordIds, regionIds, count) => {
  const job = await articleQueue.add({
    templateId,
    keywordIds,
    regionIds,
    count
  }, {
    delay: 0,
    priority: 1
  });
  
  return job;
};

module.exports = {
  publishQueue,
  indexingQueue,
  articleQueue,
  queues,
  addPublishJob,
  addIndexingJob,
  addArticleJob
};