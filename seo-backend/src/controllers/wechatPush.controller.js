const { models, Op } = require('../config/database');
const { WechatPushConfig, WechatPushLog, GeneratedArticle, PublishTask } = models;
const logger = require('../utils/logger');

const sendWechatMessage = async (openid, title, content) => {
  logger.info(`发送微信消息到 ${openid}: ${title}`);
  return true;
};

const getWechatPushConfig = async (req, res) => {
  try {
    let config = await WechatPushConfig.findOne();
    if (!config) {
      config = await WechatPushConfig.create({
        pushEnabled: 0,
        pushTime: '09:00',
        pushTypes: 'daily,alert',
      });
    }
    res.json({ code: 200, message: 'success', data: config });
  } catch (error) {
    logger.error('获取微信推送配置失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updateWechatPushConfig = async (req, res) => {
  try {
    const { appId, appSecret, targetUserIds, targetOpenids, pushEnabled, pushTime, pushTypes } =
      req.body;

    let config = await WechatPushConfig.findOne();
    if (!config) {
      config = await WechatPushConfig.create({});
    }

    await config.update({
      appId: appId || '',
      appSecret: appSecret || '',
      targetUserIds: targetUserIds || '',
      targetOpenids: targetOpenids || '',
      pushEnabled: pushEnabled !== undefined ? pushEnabled : config.pushEnabled,
      pushTime: pushTime || '09:00',
      pushTypes: pushTypes || 'daily,alert',
    });

    logger.info('微信推送配置更新成功');
    res.json({ code: 200, message: '配置更新成功' });
  } catch (error) {
    logger.error('更新微信推送配置失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getPushLogs = async (req, res) => {
  try {
    const { page = 1, pageSize = 20, pushType } = req.query;
    const offset = (page - 1) * pageSize;

    const where = {};
    if (pushType) where.pushType = pushType;

    const { count, rows } = await WechatPushLog.findAndCountAll({
      where,
      order: [['createdAt', 'DESC']],
      limit: parseInt(pageSize),
      offset,
    });

    res.json({
      code: 200,
      message: 'success',
      data: {
        list: rows,
        total: count,
        page: parseInt(page),
        pageSize: parseInt(pageSize),
      },
    });
  } catch (error) {
    logger.error('获取推送记录失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const sendDailyReport = async () => {
  try {
    const config = await WechatPushConfig.findOne();
    if (!config || !config.pushEnabled || !config.targetOpenids) {
      return;
    }

    const today = new Date().toISOString().slice(0, 10);
    const articleCount = await GeneratedArticle.count({
      where: { createdAt: { [Op.gte]: today } },
    });
    const publishSuccessCount = await PublishTask.count({
      where: { status: 2, createdAt: { [Op.gte]: today } },
    });
    const publishFailCount = await PublishTask.count({
      where: { status: 3, createdAt: { [Op.gte]: today } },
    });

    const title = '【SEO系统】今日数据报告';
    const content = `
📊 今日数据概览:
  ✍️  生成文章: ${articleCount} 篇
  ✅  发布成功: ${publishSuccessCount} 篇
  ❌  发布失败: ${publishFailCount} 篇
  📈  成功率: ${publishSuccessCount + publishFailCount > 0 ? Math.round((publishSuccessCount / (publishSuccessCount + publishFailCount)) * 100) : 0}%

发送时间: ${new Date().toLocaleString()}
    `.trim();

    const openids = config.targetOpenids.split(',').filter(o => o.trim());
    for (const openid of openids) {
      await sendWechatMessage(openid.trim(), title, content);

      await WechatPushLog.create({
        pushType: 'daily',
        title,
        content,
        targetOpenid: openid.trim(),
        sendStatus: 1,
        sentAt: new Date(),
      });
    }

    logger.info('每日报告推送完成');
  } catch (error) {
    logger.error('推送每日报告失败:', error);
  }
};

const sendAlert = async (title, content) => {
  try {
    const config = await WechatPushConfig.findOne();
    if (!config || !config.pushEnabled || !config.targetOpenids) {
      return;
    }

    const pushTypes = config.pushTypes.split(',');
    if (!pushTypes.includes('alert')) {
      return;
    }

    const openids = config.targetOpenids.split(',').filter(o => o.trim());
    for (const openid of openids) {
      await sendWechatMessage(openid.trim(), title, content);

      await WechatPushLog.create({
        pushType: 'alert',
        title,
        content,
        targetOpenid: openid.trim(),
        sendStatus: 1,
        sentAt: new Date(),
      });
    }

    logger.info('预警消息推送完成');
  } catch (error) {
    logger.error('推送预警消息失败:', error);
  }
};

const manualSendDaily = async (req, res) => {
  try {
    await sendDailyReport();
    res.json({ code: 200, message: '日报推送成功' });
  } catch (error) {
    logger.error('手动推送日报失败:', error);
    res.status(500).json({ code: 500, message: '推送失败' });
  }
};

module.exports = {
  getWechatPushConfig,
  updateWechatPushConfig,
  getPushLogs,
  sendDailyReport,
  sendAlert,
  manualSendDaily,
};
