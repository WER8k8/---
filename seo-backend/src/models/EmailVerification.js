const { DataTypes } = require('sequelize');

module.exports = sequelize => {
  return sequelize.define(
    'EmailVerification',
    {
      id: { type: DataTypes.INTEGER.UNSIGNED, primaryKey: true, autoIncrement: true },
      email: { type: DataTypes.STRING(100), allowNull: false },
      verificationCode: {
        type: DataTypes.STRING(10),
        allowNull: false,
        field: 'verification_code',
      },
      verificationType: {
        type: DataTypes.ENUM('login', 'bind', 'reset'),
        allowNull: false,
        field: 'verification_type',
      },
      ipAddress: { type: DataTypes.STRING(45), defaultValue: '', field: 'ip_address' },
      expiresAt: { type: DataTypes.DATE, allowNull: false, field: 'expires_at' },
      isUsed: { type: DataTypes.TINYINT, defaultValue: 0, field: 'is_used' },
      createdAt: { type: DataTypes.DATE, field: 'created_at', defaultValue: DataTypes.NOW },
    },
    {
      tableName: 'email_verifications',
      timestamps: false,
    }
  );
};
