const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('IndustryKeyword', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    keyword: {
      type: DataTypes.STRING(200),
      allowNull: false
    },
    category: {
      type: DataTypes.STRING(50),
      defaultValue: ''
    },
    search_volume: {
      type: DataTypes.INTEGER,
      defaultValue: 0
    },
    difficulty: {
      type: DataTypes.INTEGER,
      defaultValue: 0
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
    tableName: 'industry_keywords',
    timestamps: false
  });
};
