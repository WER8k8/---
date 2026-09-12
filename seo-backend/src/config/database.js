const { Sequelize, Op } = require('sequelize');
const logger = require('../utils/logger');
const path = require('path');

const dialect = process.env.DB_DIALECT || 'sqlite';

const sequelize =
  dialect === 'sqlite'
    ? new Sequelize({
        dialect: 'sqlite',
        storage: path.join(__dirname, '../..', 'database', 'database.sqlite'),
        logging: msg => logger.debug(msg),
        define: {
          timestamps: false,
          underscored: true,
          freezeTableName: true,
        },
        dialectOptions: {
          foreignKeys: false,
        },
        dialectModule: require('./sqlite3-shim'),
      })
    : new Sequelize(
        process.env.DB_NAME || 'seo_matrix_db',
        process.env.DB_USER || 'root',
        process.env.DB_PASSWORD || '',
        {
          host: process.env.DB_HOST || 'localhost',
          port: parseInt(process.env.DB_PORT) || 3306,
          dialect: 'mysql',
          dialectOptions: {
            charset: 'utf8mb4',
            collate: 'utf8mb4_unicode_ci',
          },
          logging: msg => logger.debug(msg),
          define: {
            timestamps: false,
            underscored: true,
            freezeTableName: true,
            charset: 'utf8mb4',
            collate: 'utf8mb4_unicode_ci',
          },
          pool: {
            max: 10,
            min: 0,
            acquire: 30000,
            idle: 10000,
          },
        }
      );

const AdminUser = require('../models/AdminUser')(sequelize);
const SystemConfig = require('../models/SystemConfig')(sequelize);
const Region = require('../models/Region')(sequelize);
const IndustryKeyword = require('../models/IndustryKeyword')(sequelize);
const LongtailKeyword = require('../models/LongtailKeyword')(sequelize);
const ArticleTemplate = require('../models/ArticleTemplate')(sequelize);
const GeneratedArticle = require('../models/GeneratedArticle')(sequelize);
const Platform = require('../models/Platform')(sequelize);
const PlatformAccount = require('../models/PlatformAccount')(sequelize);
const PublishTask = require('../models/PublishTask')(sequelize);
const IndexingRecord = require('../models/IndexingRecord')(sequelize);
const SystemAlert = require('../models/SystemAlert')(sequelize);
const OperationLog = require('../models/OperationLog')(sequelize);
const LoginLog = require('../models/LoginLog')(sequelize);
const SocialLogin = require('../models/SocialLogin')(sequelize);
const WechatPushConfig = require('../models/WechatPushConfig')(sequelize);
const WechatPushLog = require('../models/WechatPushLog')(sequelize);
const EmailVerification = require('../models/EmailVerification')(sequelize);

Region.belongsTo(Region, { as: 'parent', foreignKey: 'parent_id' });
Region.hasMany(Region, { as: 'children', foreignKey: 'parent_id' });

LongtailKeyword.belongsTo(Region, { foreignKey: 'region_id' });
LongtailKeyword.belongsTo(IndustryKeyword, { foreignKey: 'keyword_id' });

GeneratedArticle.belongsTo(Region, { foreignKey: 'region_id' });
GeneratedArticle.belongsTo(IndustryKeyword, { foreignKey: 'keyword_id' });
GeneratedArticle.belongsTo(ArticleTemplate, { foreignKey: 'template_id' });

PlatformAccount.belongsTo(Platform, { foreignKey: 'platform_id' });

PublishTask.belongsTo(GeneratedArticle, { foreignKey: 'article_id' });
PublishTask.belongsTo(PlatformAccount, { foreignKey: 'platform_account_id' });

IndexingRecord.belongsTo(GeneratedArticle, { foreignKey: 'article_id' });

SocialLogin.belongsTo(AdminUser, { foreignKey: 'user_id' });
AdminUser.hasMany(SocialLogin, { foreignKey: 'user_id' });

WechatPushLog.belongsTo(AdminUser, { foreignKey: 'target_user_id' });

const models = {
  AdminUser,
  SystemConfig,
  Region,
  IndustryKeyword,
  LongtailKeyword,
  ArticleTemplate,
  GeneratedArticle,
  Platform,
  PlatformAccount,
  PublishTask,
  IndexingRecord,
  SystemAlert,
  OperationLog,
  LoginLog,
  SocialLogin,
  WechatPushConfig,
  WechatPushLog,
  EmailVerification,
};

module.exports = { sequelize, models, Op };
