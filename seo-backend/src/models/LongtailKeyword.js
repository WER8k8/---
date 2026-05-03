const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('LongtailKeyword', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    region_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    keyword_id: {
      type: DataTypes.INTEGER,
      allowNull: false
    },
    keyword: {
      type: DataTypes.STRING(200),
      allowNull: false
    },
    status: {
      type: DataTypes.TINYINT,
      defaultValue: 1
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'longtail_keywords',
    timestamps: false
  });
};
