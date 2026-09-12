const { DataTypes } = require('sequelize');

module.exports = sequelize => {
  return sequelize.define(
    'SocialLogin',
    {
      id: { type: DataTypes.INTEGER.UNSIGNED, primaryKey: true, autoIncrement: true },
      userId: { type: DataTypes.INTEGER.UNSIGNED, allowNull: false, field: 'user_id' },
      provider: { type: DataTypes.ENUM('qq', 'wechat', 'email'), allowNull: false },
      providerUserId: { type: DataTypes.STRING(100), allowNull: false, field: 'provider_user_id' },
      providerUsername: {
        type: DataTypes.STRING(100),
        defaultValue: '',
        field: 'provider_username',
      },
      avatar: { type: DataTypes.STRING(255), defaultValue: '' },
      accessToken: { type: DataTypes.TEXT, field: 'access_token' },
      refreshToken: { type: DataTypes.TEXT, field: 'refresh_token' },
      tokenExpiresAt: { type: DataTypes.DATE, field: 'token_expires_at' },
      lastLoginAt: { type: DataTypes.DATE, field: 'last_login_at' },
      createdAt: { type: DataTypes.DATE, field: 'created_at', defaultValue: DataTypes.NOW },
      updatedAt: {
        type: DataTypes.DATE,
        field: 'updated_at',
        defaultValue: DataTypes.NOW,
        onUpdate: DataTypes.NOW,
      },
    },
    {
      tableName: 'social_logins',
      timestamps: false,
    }
  );
};
