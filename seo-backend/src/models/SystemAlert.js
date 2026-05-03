const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('SystemAlert', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    type: {
      type: DataTypes.STRING(50),
      allowNull: false
    },
    title: {
      type: DataTypes.STRING(200),
      allowNull: false
    },
    description: {
      type: DataTypes.TEXT
    },
    level: {
      type: DataTypes.TINYINT,
      defaultValue: 1
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
    tableName: 'system_alerts',
    timestamps: false
  });
};
