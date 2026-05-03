const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('Platform', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    name: {
      type: DataTypes.STRING(50),
      allowNull: false
    },
    category: {
      type: DataTypes.STRING(50),
      defaultValue: ''
    },
    has_api: {
      type: DataTypes.TINYINT,
      defaultValue: 0
    },
    daily_limit: {
      type: DataTypes.INTEGER,
      defaultValue: 50
    },
    status: {
      type: DataTypes.TINYINT,
      defaultValue: 1
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
    tableName: 'platforms',
    timestamps: false
  });
};
