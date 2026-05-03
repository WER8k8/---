const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('PlatformAccount', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    platform_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    platform_name: {
      type: DataTypes.STRING(50),
      allowNull: false
    },
    account_name: {
      type: DataTypes.STRING(100),
      allowNull: false
    },
    cookie: {
      type: DataTypes.TEXT
    },
    token: {
      type: DataTypes.STRING(500)
    },
    status: {
      type: DataTypes.TINYINT,
      defaultValue: 1
    },
    last_publish_at: {
      type: DataTypes.DATE
    },
    today_publish_count: {
      type: DataTypes.INTEGER,
      defaultValue: 0
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
    tableName: 'platform_accounts',
    timestamps: false
  });
};
