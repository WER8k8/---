const { Sequelize, Op } = require('sequelize');
const logger = require('../utils/logger');
const path = require('path');

const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, '../../database/database.sqlite'),
  logging: (msg) => logger.debug(msg),
  define: {
    timestamps: false,
    underscored: true,
    freezeTableName: true
  }
});

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
  LoginLog
};

module.exports = { sequelize, models, Op };
