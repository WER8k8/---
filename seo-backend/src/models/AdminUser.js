const { DataTypes } = require('sequelize');

module.exports = (sequelize) => {
  return sequelize.define('AdminUser', {
    id: { type: DataTypes.INTEGER.UNSIGNED, primaryKey: true, autoIncrement: true },
    username: { type: DataTypes.STRING(50), allowNull: false, unique: true },
    passwordHash: { type: DataTypes.STRING(255), allowNull: false, field: 'password_hash' },
    nickname: { type: DataTypes.STRING(50), defaultValue: '' },
    avatar: { type: DataTypes.STRING(255), defaultValue: '' },
    email: { type: DataTypes.STRING(100), defaultValue: '' },
    phone: { type: DataTypes.STRING(20), defaultValue: '' },
    status: { type: DataTypes.TINYINT, defaultValue: 1 },
    lastLoginAt: { type: DataTypes.DATE, field: 'last_login_at' },
    lastLoginIp: { type: DataTypes.STRING(45), field: 'last_login_ip' },
    loginFailCount: { type: DataTypes.TINYINT, defaultValue: 0, field: 'login_fail_count' },
    lockedUntil: { type: DataTypes.DATE, field: 'locked_until' },
    expiresAt: { type: DataTypes.DATE, field: 'expires_at' },
    createdAt: { type: DataTypes.DATE, field: 'created_at', defaultValue: DataTypes.NOW },
    updatedAt: { type: DataTypes.DATE, field: 'updated_at', defaultValue: DataTypes.NOW, onUpdate: DataTypes.NOW }
  }, {
    tableName: 'admin_users',
    timestamps: false
  });
};
