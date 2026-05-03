const { sequelize, models } = require('../config/database');
const Platform = models.Platform || require('../models/Platform');
const PlatformAccount = models.PlatformAccount || require('../models/PlatformAccount');

const getPlatforms = async (req, res) => {
  try {
    const platforms = await Platform.findAll();
    res.json({ code: 200, message: 'success', data: platforms });
  } catch (error) {
    console.error('获取平台失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const getPlatformAccounts = async (req, res) => {
  try {
    const { id } = req.params;
    const { page = 1, pageSize = 20 } = req.query;
    
    const result = await PlatformAccount.findAndCountAll({
      where: { platform_id: id },
      offset: (page - 1) * pageSize,
      limit: parseInt(pageSize)
    });
    
    res.json({ 
      code: 200, 
      message: 'success', 
      data: {
        list: result.rows,
        total: result.count,
        page: parseInt(page),
        pageSize: parseInt(pageSize)
      }
    });
  } catch (error) {
    console.error('获取账号失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const createPlatformAccount = async (req, res) => {
  try {
    const { id } = req.params;
    const { account_name, cookie, token } = req.body;
    
    const platform = await Platform.findByPk(id);
    if (!platform) return res.status(404).json({ code: 404, message: '平台不存在' });
    
    const newAccount = await PlatformAccount.create({
      platform_id: id,
      platform_name: platform.name,
      account_name,
      cookie,
      token
    });
    
    res.json({ code: 200, message: '创建成功', data: newAccount });
  } catch (error) {
    console.error('创建账号失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const updatePlatformAccount = async (req, res) => {
  try {
    const { id, accountId } = req.params;
    const data = req.body;
    
    const account = await PlatformAccount.findByPk(accountId);
    if (!account) return res.status(404).json({ code: 404, message: '账号不存在' });
    
    await account.update(data);
    res.json({ code: 200, message: '更新成功', data: account });
  } catch (error) {
    console.error('更新账号失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

const deletePlatformAccount = async (req, res) => {
  try {
    const { id, accountId } = req.params;
    
    const account = await PlatformAccount.findByPk(accountId);
    if (!account) return res.status(404).json({ code: 404, message: '账号不存在' });
    
    await account.destroy();
    res.json({ code: 200, message: '删除成功' });
  } catch (error) {
    console.error('删除账号失败:', error);
    res.status(500).json({ code: 500, message: '服务器内部错误' });
  }
};

module.exports = { 
  getPlatforms, 
  getPlatformAccounts, 
  createPlatformAccount, 
  updatePlatformAccount, 
  deletePlatformAccount 
};
