const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('IndexingRecord', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    article_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    search_engine: {
      type: DataTypes.STRING(50),
      defaultValue: 'baidu'
    },
    keyword: {
      type: DataTypes.STRING(200)
    },
    is_indexed: {
      type: DataTypes.TINYINT,
      defaultValue: 0
    },
    ranking: {
      type: DataTypes.INTEGER,
      defaultValue: 0
    },
    is_homepage: {
      type: DataTypes.TINYINT,
      defaultValue: 0
    },
    checked_at: {
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
    tableName: 'indexing_records',
    timestamps: false
  });
};
