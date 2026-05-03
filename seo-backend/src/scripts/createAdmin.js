require('dotenv').config();
const bcrypt = require('bcryptjs');
const { sequelize, models } = require('../config/database');
const AdminUser = models.AdminUser;

const createAdmin = async () => {
  try {
    console.log('开始创建管理员账号...');
    
    await sequelize.authenticate();
    console.log('数据库连接成功');

    const existingUser = await AdminUser.findOne({ where: { username: 'admin' } });
    
    if (existingUser) {
      console.log('管理员账号已存在，跳过创建');
      process.exit(0);
    }

    const password = process.env.ADMIN_PASSWORD || 'admin@123';
    const hashedPassword = await bcrypt.hash(password, 10);

    const adminUser = await AdminUser.create({
      username: 'admin',
      nickname: '超级管理员',
      passwordHash: hashedPassword,
      email: 'admin@example.com',
      status: 1,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    console.log('管理员账号创建成功！');
    console.log(`用户名: admin`);
    console.log(`密码: ${password}`);
    console.log(`用户ID: ${adminUser.id}`);
    
    process.exit(0);
  } catch (error) {
    console.error('创建管理员账号失败:', error);
    process.exit(1);
  }
};

createAdmin();