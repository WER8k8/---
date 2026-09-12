// Note: dashboard queries are currently stubbed with zeros.
// When real queries are added, uncomment the needed model imports below.
// const { sequelize, models } = require('../config/database');
// const { Op } = require('sequelize');
// const GeneratedArticle = models.GeneratedArticle;
// const PublishTask = models.PublishTask;
// const PlatformAccount = models.PlatformAccount;
// const SystemAlert = models.SystemAlert;

const getDashboardStats = async (req, res) => {
  try {
    const result = {
      totalRegions: 0,
      totalKeywords: 0,
      totalArticles: 0,
      publishedArticles: 0,
      successRate: 0,
      indexedCount: 0,
      homepageCount: 0,
      todayStats: {
        generated: 0,
        published: 0,
        failed: 0,
        indexed: 0,
      },
      articles: {
        total: 0,
        pending: 0,
        published: 0,
        today: 0,
      },
      publish: {
        total: 0,
        pending: 0,
        success: 0,
        failed: 0,
        today: 0,
      },
      accounts: {
        total: 0,
        active: 0,
      },
      alerts: 0,
    };

    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取仪表盘数据失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getTrendData = async (req, res) => {
  try {
    const { days = 7 } = req.query;
    const dates = [];
    const generated = [];
    const published = [];
    const indexed = [];

    for (let i = parseInt(days) - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      dates.push(dateStr);
      generated.push(0);
      published.push(0);
      indexed.push(0);
    }

    res.json({
      code: 200,
      message: 'success',
      data: { dates, generated, published, indexed },
    });
  } catch (error) {
    console.error('获取趋势数据失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { getDashboardStats, getTrendData };
