require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const { sequelize } = require('./config/database');
const matrixDatabase = require('./config/matrixDatabase');
const { assertJwtSecretsSafeOrThrow } = require('./utils/assertJwtSecrets');
const { validateStartupConfigOrThrow } = require('./utils/startupConfigValidation');
const { errorHandler } = require('./middleware/errorHandler');
const authRouter = require('./routes/auth.routes');
const socialAuthRouter = require('./routes/socialAuth.routes');
const wechatPushRouter = require('./routes/wechatPush.routes');
const configRouter = require('./routes/config.routes');
const regionRouter = require('./routes/region.routes');
const keywordRouter = require('./routes/keyword.routes');
const templateRouter = require('./routes/template.routes');
const articleRouter = require('./routes/article.routes');
const platformRouter = require('./routes/platform.routes');
const publishRouter = require('./routes/publish.routes');
const dashboardRouter = require('./routes/dashboard.routes');
const monitoringRouter = require('./routes/monitoring.routes');
const logRouter = require('./routes/log.routes');
const { startWorkers } = require('./tasks/processors');
const { startCron } = require('./tasks/cron');
const logger = require('./utils/logger');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(
  cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true,
  })
);

app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

app.use(
  morgan('combined', {
    stream: { write: message => logger.info(message.trim()) },
  })
);

const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: { code: 429, message: '请求过于频繁，请稍后再试' },
});
app.use('/api/', limiter);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

const apiPrefix = process.env.API_PREFIX || '/api/v1';
app.use(`${apiPrefix}/auth`, authRouter);
app.use(`${apiPrefix}/social`, socialAuthRouter);
app.use(`${apiPrefix}/wechat`, wechatPushRouter);
app.use(`${apiPrefix}/configs`, configRouter);
app.use(`${apiPrefix}/regions`, regionRouter);
app.use(`${apiPrefix}/keywords`, keywordRouter);
app.use(`${apiPrefix}/templates`, templateRouter);
app.use(`${apiPrefix}/articles`, articleRouter);
app.use(`${apiPrefix}/platforms`, platformRouter);
app.use(`${apiPrefix}/publish`, publishRouter);
app.use(`${apiPrefix}/dashboard`, dashboardRouter);
app.use(`${apiPrefix}/monitoring`, monitoringRouter);
app.use(`${apiPrefix}/logs`, logRouter);

app.use((req, res) => {
  res.status(404).json({ code: 404, message: '接口不存在' });
});

app.use(errorHandler);

async function start() {
  try {
    validateStartupConfigOrThrow();
    assertJwtSecretsSafeOrThrow();

    await sequelize.authenticate();
    logger.info('数据库连接成功');

    if (matrixDatabase.isMatrixMysqlConfigured()) {
      try {
        await matrixDatabase.authenticateMatrixDb();
        logger.info('SEO矩阵第二连接(MySQL)就绪');
      } catch (e) {
        logger.error('SEO矩阵MySQL第二连接失败:', e);
        await matrixDatabase.markMatrixMysqlDegraded(e?.message || String(e));
      }
    }

    if (process.env.NODE_ENV === 'development') {
      const dialect = process.env.DB_DIALECT || 'sqlite';
      if (dialect === 'sqlite') {
        await sequelize.query('PRAGMA foreign_keys = OFF;');
      }
      await sequelize.sync({ alter: true });
      if (dialect === 'sqlite') {
        await sequelize.query('PRAGMA foreign_keys = ON;');
      }
      logger.info('数据库模型同步完成');
    }

    app.listen(PORT, () => {
      logger.info(`服务器启动成功，端口: ${PORT}`);
      logger.info(`环境: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`API前缀: ${apiPrefix}`);

      startWorkers();
      startCron();
    });
  } catch (error) {
    logger.error('服务器启动失败:', error);
    throw error;
  }
}

start();

module.exports = app;
