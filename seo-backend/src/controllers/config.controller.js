const { sequelize, models } = require('../config/database');
const SystemConfig = models.SystemConfig || require('../models/SystemConfig');

const getConfigs = async (req, res) => {
  try {
    const configs = await SystemConfig.findAll();
    const result = {};
    configs.forEach(c => {
      if (!result[c.group]) result[c.group] = {};
      result[c.group][c.key] = c.value;
    });
    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取配置失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getConfigByGroup = async (req, res) => {
  try {
    const { group } = req.params;
    const configs = await SystemConfig.findAll({ where: { group } });
    const result = {};
    configs.forEach(c => {
      result[c.key] = c.value;
    });
    res.json({ code: 200, message: 'success', data: result });
  } catch (error) {
    console.error('获取配置失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updateConfig = async (req, res) => {
  try {
    const { group } = req.params;
    const configData = req.body;
    
    for (const [key, value] of Object.entries(configData)) {
      await SystemConfig.upsert({
        group,
        key,
        value: typeof value === 'object' ? JSON.stringify(value) : String(value)
      });
    }
    
    res.json({ code: 200, message: '配置更新成功', data: configData });
  } catch (error) {
    console.error('更新配置失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { getConfigs, getConfigByGroup, updateConfig };
