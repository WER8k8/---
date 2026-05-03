const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('PublishTask', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    article_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    platform_account_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    status: {
      type: DataTypes.TINYINT,
      defaultValue: 0
    },
    error_message: {
      type: DataTypes.TEXT
    },
    retry_count: {
      type: DataTypes.INTEGER,
      defaultValue: 0
    },
    published_url: {
      type: DataTypes.STRING(500)
    },
    executed_at: {
      type: DataTypes.DATE
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW
    },
    updated_at: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW,
      onUpdate: DataTypes.NOW
    }
  }, {
    tableName: 'publish_tasks',
    timestamps: false
  });
};
