const { sequelize, models } = require('../config/database');
const { Op } = require('sequelize');
const GeneratedArticle = models.GeneratedArticle;
const PublishTask = models.PublishTask;
const PlatformAccount = models.PlatformAccount;
const SystemAlert = models.SystemAlert;

const getDashboardStats = async (req, res) => {
  try {
    const [articleStats, publishStats, accountStats, alertStats] = await Promise.all([
      GeneratedArticle.findAndCountAll({
        attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
        group: ['status']
      }),
      PublishTask.findAndCountAll({
        attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
        group: ['status']
      }),
      PlatformAccount.findAndCountAll({
        attributes: ['status', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
        group: ['status']
      }),
      SystemAlert.count({ where: { status: [1, 2] } })
    ]);

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayArticles = await GeneratedArticle.count({
      where: { created_at: { [Op.gte]: today } }
    });
    const todayPublish = await PublishTask.count({
      where: { status: 2, updated_at: { [Op.gte]: today } }
    });

    const result = {
      articles: {
        total: articleStats.count,
        pending: articleStats.rows.find(r => r.status === 0)?.dataValues.count || 0,
        published: articleStats.rows.find(r => r.status === 1)?.dataValues.count || 0,
        today: todayArticles
      },
      publish: {
        total: publishStats.count,
        pending: publishStats.rows.find(r => r.status === 0)?.dataValues.count || 0,
        success: publishStats.rows.find(r => r.status === 2)?.dataValues.count || 0,
        failed: publishStats.rows.find(r => r.status === 3)?.dataValues.count || 0,
        today: todayPublish
      },
      accounts: {
        total: accountStats.count,
        active: accountStats.rows.find(r => r.status === 1)?.dataValues.count || 0
      },
      alerts: alertStats
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
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - parseInt(days) + 1);

    const result = [];
    for (let i = 0; i < parseInt(days); i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      const nextDate = new Date(date);
      nextDate.setDate(nextDate.getDate() + 1);

      const [articles, publishes] = await Promise.all([
        GeneratedArticle.count({
          where: {
            created_at: {
              [Op.gte]: date,
              [Op.lt]: nextDate
            }
          }
        }),
        PublishTask.count({
          where: {
            status: 2,
            updated_at: {
              [Op.gte]: date,
              [Op.lt]: nextDate
            }
          }
        })
      ]);

      result.push({
        date: dateStr,
        articles,
        publishes
      });
    }

    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取趋势数据失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { getDashboardStats, getTrendData };
