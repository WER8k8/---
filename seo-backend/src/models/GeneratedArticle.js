const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('GeneratedArticle', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    title: {
      type: DataTypes.STRING(255),
      allowNull: false
    },
    content: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    region_id: {
      type: DataTypes.INTEGER
    },
    keyword_id: {
      type: DataTypes.INTEGER
    },
    template_id: {
      type: DataTypes.INTEGER
    },
    word_count: {
      type: DataTypes.INTEGER,
      defaultValue: 0
    },
    duplicate_rate: {
      type: DataTypes.DECIMAL(5, 2),
      defaultValue: 0
    },
    compliance_status: {
      type: DataTypes.TINYINT,
      defaultValue: 1
    },
    status: {
      type: DataTypes.TINYINT,
      defaultValue: 0
    },
    published_at: {
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
    tableName: 'generated_articles',
    timestamps: false
  });
};
