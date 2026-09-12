const { DataTypes } = require('sequelize');

module.exports = sequelize => {
  return sequelize.define(
    'WechatPushLog',
    {
      id: { type: DataTypes.BIGINT.UNSIGNED, primaryKey: true, autoIncrement: true },
      pushType: { type: DataTypes.STRING(20), allowNull: false, field: 'push_type' },
      title: { type: DataTypes.STRING(200), defaultValue: '' },
      content: { type: DataTypes.TEXT },
      targetOpenid: { type: DataTypes.STRING(100), defaultValue: '', field: 'target_openid' },
      targetUserId: { type: DataTypes.INTEGER.UNSIGNED, allowNull: true, field: 'target_user_id' },
      sendStatus: { type: DataTypes.TINYINT, defaultValue: 0, field: 'send_status' },
      sendResult: { type: DataTypes.TEXT, field: 'send_result' },
      createdAt: { type: DataTypes.DATE, field: 'created_at', defaultValue: DataTypes.NOW },
      sentAt: { type: DataTypes.DATE, field: 'sent_at' },
    },
    {
      tableName: 'wechat_push_logs',
      timestamps: false,
    }
  );
};
