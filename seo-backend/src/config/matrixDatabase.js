/**
 * SEO 矩阵库第二连接（MySQL），与主库 DB_* / sqlite 并存。
 * 用于生产环境矩阵 admin_users 与主应用库分离部署。
 */
const { Sequelize } = require('sequelize');
const logger = require('../utils/logger');

let matrixSequelize = null;
/** 启动时第二连接认证失败后置为 true，避免反复建连；矩阵读仍可由主站 Python 完成 */
let matrixMysqlDegraded = false;

function isMatrixMysqlConfigured() {
  const host = (process.env.SEO_MATRIX_DB_HOST || '').trim();
  const name = (process.env.SEO_MATRIX_DB_NAME || '').trim();
  const user = process.env.SEO_MATRIX_DB_USER;
  return !!(host && name && user !== undefined && String(user).trim() !== '');
}

function getMatrixSequelize() {
  if (!isMatrixMysqlConfigured() || matrixMysqlDegraded) {
    return null;
  }
  if (matrixSequelize) {
    return matrixSequelize;
  }
  matrixSequelize = new Sequelize(
    process.env.SEO_MATRIX_DB_NAME,
    process.env.SEO_MATRIX_DB_USER,
    process.env.SEO_MATRIX_DB_PASSWORD || '',
    {
      host: process.env.SEO_MATRIX_DB_HOST,
      port: parseInt(process.env.SEO_MATRIX_DB_PORT || '3306', 10),
      dialect: 'mysql',
      logging: msg => logger.debug(msg),
      pool: { max: 5, min: 0, acquire: 30000, idle: 10000 },
      define: {
        timestamps: false,
        underscored: true,
        freezeTableName: true,
        charset: 'utf8mb4',
        collate: 'utf8mb4_unicode_ci',
      },
    }
  );
  return matrixSequelize;
}

async function authenticateMatrixDb() {
  const s = getMatrixSequelize();
  if (!s) {
    return;
  }
  await s.authenticate();
}

function closeMatrixDb() {
  if (matrixSequelize) {
    return matrixSequelize.close();
  }
  return Promise.resolve();
}

/**
 * 第二连接不可用时的降级：关闭连接并不再尝试使用矩阵 MySQL 实例（主业务库不受影响）。
 */
async function markMatrixMysqlDegraded(reason) {
  matrixMysqlDegraded = true;
  try {
    await closeMatrixDb();
  } catch (_) {
    /* ignore */
  }
  matrixSequelize = null;
  logger.warn(
    `[矩阵第二连接降级] ${reason || '连接失败'}；已关闭矩阵 MySQL 连接，进程继续运行。admin_users 联邦校验仍可由主站 Python 完成。`
  );
}

module.exports = {
  isMatrixMysqlConfigured,
  getMatrixSequelize,
  authenticateMatrixDb,
  closeMatrixDb,
  markMatrixMysqlDegraded,
};
