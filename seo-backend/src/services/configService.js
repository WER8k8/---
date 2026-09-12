const { sequelize, models } = require('../config/database');
const SystemConfig = models.SystemConfig;

const getGroups = async () => {
  const groups = await SystemConfig.findAll({
    attributes: ['group', [sequelize.fn('COUNT', sequelize.col('id')), 'count']],
    group: ['group'],
  });
  return groups;
};

const getConfig = async group => {
  const configs = await SystemConfig.findAll({ where: { group } });
  const result = {};
  configs.forEach(config => {
    result[config.key] = config.value;
  });
  return result;
};

const updateConfig = async (group, data) => {
  for (const [key, value] of Object.entries(data)) {
    await SystemConfig.upsert({
      group,
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value),
    });
  }
  return await getConfig(group);
};

const resetConfig = async group => {
  await SystemConfig.destroy({ where: { group } });
  return { message: '配置已重置' };
};

const exportConfig = async () => {
  const configs = await SystemConfig.findAll();
  const result = {};
  configs.forEach(config => {
    if (!result[config.group]) result[config.group] = {};
    result[config.group][config.key] = config.value;
  });
  return result;
};

const importConfig = async data => {
  for (const [group, items] of Object.entries(data)) {
    for (const [key, value] of Object.entries(items)) {
      await SystemConfig.upsert({
        group,
        key,
        value: typeof value === 'object' ? JSON.stringify(value) : String(value),
      });
    }
  }
  return { message: '配置导入成功' };
};

const getPublicConfigs = async () => {
  const configs = await SystemConfig.findAll({
    where: { is_public: 1 },
  });
  const result = {};
  configs.forEach(config => {
    result[config.key] = config.value;
  });
  return result;
};

const setConfig = async (group, key, value) => {
  await SystemConfig.upsert({
    group,
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value),
  });
  return { group, key, value };
};

const getConfigByKey = async (group, key) => {
  const config = await SystemConfig.findOne({ where: { group, key } });
  return config ? config.value : null;
};

module.exports = {
  getGroups,
  getConfig,
  updateConfig,
  resetConfig,
  exportConfig,
  importConfig,
  getPublicConfigs,
  setConfig,
  getConfigByKey,
};
