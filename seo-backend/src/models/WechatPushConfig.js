const { DataTypes } = require('sequelize');

module.exports = sequelize => {
  return sequelize.define(
    'WechatPushConfig',
    {
      id: { type: DataTypes.INTEGER.UNSIGNED, primaryKey: true, autoIncrement: true },
      appId: { type: DataTypes.STRING(100), defaultValue: '', field: 'app_id' },
      appSecret: { type: DataTypes.STRING(100), defaultValue: '', field: 'app_secret' },
      accessToken: { type: DataTypes.TEXT, field: 'access_token' },
      tokenExpiresAt: { type: DataTypes.DATE, field: 'token_expires_at' },
      targetUserIds: { type: DataTypes.TEXT, field: 'target_user_ids' },
      targetOpenids: { type: DataTypes.TEXT, field: 'target_openids' },
      pushEnabled: { type: DataTypes.TINYINT, defaultValue: 1, field: 'push_enabled' },
      pushTime: { type: DataTypes.STRING(20), defaultValue: '09:00', field: 'push_time' },
      pushTypes: { type: DataTypes.STRING(100), defaultValue: 'daily,alert', field: 'push_types' },
      createdAt: { type: DataTypes.DATE, field: 'created_at', defaultValue: DataTypes.NOW },
      updatedAt: {
        type: DataTypes.DATE,
        field: 'updated_at',
        defaultValue: DataTypes.NOW,
        onUpdate: DataTypes.NOW,
      },
    },
    {
      tableName: 'wechat_push_configs',
      timestamps: false,
    }
  );
};
