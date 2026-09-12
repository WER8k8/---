require('dotenv').config();
const cron = require('node-cron');
const { sendDailyReport } = require('../controllers/wechatPush.controller');
const logger = require('../utils/logger');

const scheduleWechatPush = () => {
  cron.schedule(
    '0 9 * * *',
    async () => {
      logger.info('执行每日微信推送定时任务');
      await sendDailyReport();
    },
    {
      scheduled: true,
      timezone: 'Asia/Shanghai',
    }
  );

  logger.info('微信推送定时任务已启动，每日9:00执行');
};

const startCron = () => {
  scheduleWechatPush();
  logger.info('所有定时任务已启动');
};

module.exports = { startCron };
