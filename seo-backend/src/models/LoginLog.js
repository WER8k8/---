const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('LoginLog', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    user_id: {
      type: DataTypes.INTEGER
    },
    username: {
      type: DataTypes.STRING(50),
      allowNull: false
    },
    ip_address: {
      type: DataTypes.STRING(45),
      defaultValue: ''
    },
    device: {
      type: DataTypes.STRING(100),
      defaultValue: ''
    },
    login_result: {
      type: DataTypes.TINYINT,
      defaultValue: 1
    },
    fail_reason: {
      type: DataTypes.STRING(200),
      defaultValue: ''
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'login_logs',
    timestamps: false
  });
};
