require('dotenv').config();
const { sequelize, models } = require('../config/database');

const Platform = models.Platform;
const Region = models.Region;
const SystemConfig = models.SystemConfig;
const IndustryKeyword = models.IndustryKeyword;
const ArticleTemplate = models.ArticleTemplate;

const platforms = [
  { id: 1, name: '百度贴吧', icon: 'tieba', status: 1 },
  { id: 2, name: '知乎', icon: 'zhihu', status: 1 },
  { id: 3, name: '小红书', icon: 'xiaohongshu', status: 1 },
  { id: 4, name: '抖音', icon: 'douyin', status: 1 },
  { id: 5, name: '微信公众号', icon: 'wechat', status: 1 },
  { id: 6, name: '新浪博客', icon: 'sina', status: 1 },
  { id: 7, name: 'CSDN', icon: 'csdn', status: 1 },
  { id: 8, name: '简书', icon: 'jianshu', status: 1 }
];

const regions = [
  { id: 1, name: '北京市', code: '110000', level: 1, parentId: null, status: 1, sortOrder: 1 },
  { id: 2, name: '天津市', code: '120000', level: 1, parentId: null, status: 1, sortOrder: 2 },
  { id: 3, name: '河北省', code: '130000', level: 1, parentId: null, status: 1, sortOrder: 3 },
  { id: 4, name: '山西省', code: '140000', level: 1, parentId: null, status: 1, sortOrder: 4 },
  { id: 5, name: '内蒙古自治区', code: '150000', level: 1, parentId: null, status: 1, sortOrder: 5 },
  { id: 6, name: '辽宁省', code: '210000', level: 1, parentId: null, status: 1, sortOrder: 6 },
  { id: 7, name: '吉林省', code: '220000', level: 1, parentId: null, status: 1, sortOrder: 7 },
  { id: 8, name: '黑龙江省', code: '230000', level: 1, parentId: null, status: 1, sortOrder: 8 },
  { id: 9, name: '上海市', code: '310000', level: 1, parentId: null, status: 1, sortOrder: 9 },
  { id: 10, name: '江苏省', code: '320000', level: 1, parentId: null, status: 1, sortOrder: 10 },
  { id: 11, name: '浙江省', code: '330000', level: 1, parentId: null, status: 1, sortOrder: 11 },
  { id: 12, name: '安徽省', code: '340000', level: 1, parentId: null, status: 1, sortOrder: 12 },
  { id: 13, name: '福建省', code: '350000', level: 1, parentId: null, status: 1, sortOrder: 13 },
  { id: 14, name: '江西省', code: '360000', level: 1, parentId: null, status: 1, sortOrder: 14 },
  { id: 15, name: '山东省', code: '370000', level: 1, parentId: null, status: 1, sortOrder: 15 },
  { id: 16, name: '河南省', code: '410000', level: 1, parentId: null, status: 1, sortOrder: 16 },
  { id: 17, name: '湖北省', code: '420000', level: 1, parentId: null, status: 1, sortOrder: 17 },
  { id: 18, name: '湖南省', code: '430000', level: 1, parentId: null, status: 1, sortOrder: 18 },
  { id: 19, name: '广东省', code: '440000', level: 1, parentId: null, status: 1, sortOrder: 19 },
  { id: 20, name: '广西壮族自治区', code: '450000', level: 1, parentId: null, status: 1, sortOrder: 20 },
  { id: 21, name: '海南省', code: '460000', level: 1, parentId: null, status: 1, sortOrder: 21 },
  { id: 22, name: '重庆市', code: '500000', level: 1, parentId: null, status: 1, sortOrder: 22 },
  { id: 23, name: '四川省', code: '510000', level: 1, parentId: null, status: 1, sortOrder: 23 },
  { id: 24, name: '贵州省', code: '520000', level: 1, parentId: null, status: 1, sortOrder: 24 },
  { id: 25, name: '云南省', code: '530000', level: 1, parentId: null, status: 1, sortOrder: 25 },
  { id: 26, name: '西藏自治区', code: '540000', level: 1, parentId: null, status: 1, sortOrder: 26 },
  { id: 27, name: '陕西省', code: '610000', level: 1, parentId: null, status: 1, sortOrder: 27 },
  { id: 28, name: '甘肃省', code: '620000', level: 1, parentId: null, status: 1, sortOrder: 28 },
  { id: 29, name: '青海省', code: '630000', level: 1, parentId: null, status: 1, sortOrder: 29 },
  { id: 30, name: '宁夏回族自治区', code: '640000', level: 1, parentId: null, status: 1, sortOrder: 30 },
  { id: 31, name: '新疆维吾尔自治区', code: '650000', level: 1, parentId: null, status: 1, sortOrder: 31 },
  { id: 32, name: '香港特别行政区', code: '810000', level: 1, parentId: null, status: 1, sortOrder: 32 },
  { id: 33, name: '澳门特别行政区', code: '820000', level: 1, parentId: null, status: 1, sortOrder: 33 },
  { id: 34, name: '台湾省', code: '710000', level: 1, parentId: null, status: 1, sortOrder: 34 },
  
  { id: 101, name: '东城区', code: '110101', level: 2, parentId: 1, status: 1, sortOrder: 1 },
  { id: 102, name: '西城区', code: '110102', level: 2, parentId: 1, status: 1, sortOrder: 2 },
  { id: 103, name: '朝阳区', code: '110105', level: 2, parentId: 1, status: 1, sortOrder: 3 },
  { id: 104, name: '海淀区', code: '110108', level: 2, parentId: 1, status: 1, sortOrder: 4 },
  
  { id: 3101, name: '黄浦区', code: '310101', level: 2, parentId: 9, status: 1, sortOrder: 1 },
  { id: 3102, name: '徐汇区', code: '310104', level: 2, parentId: 9, status: 1, sortOrder: 2 },
  { id: 3103, name: '浦东新区', code: '310115', level: 2, parentId: 9, status: 1, sortOrder: 3 },
  { id: 3104, name: '静安区', code: '310106', level: 2, parentId: 9, status: 1, sortOrder: 4 }
];

const systemConfigs = [
  { group: 'seo', key: 'title_length', value: '60' },
  { group: 'seo', key: 'description_length', value: '160' },
  { group: 'seo', key: 'keyword_density', value: '2-8' },
  { group: 'seo', key: 'min_content_length', value: '300' },
  
  { group: 'publish', key: 'max_per_day', value: '50' },
  { group: 'publish', key: 'interval', value: '30000' },
  { group: 'publish', key: 'max_retry', value: '3' },
  
  { group: 'ai', key: 'api_timeout', value: '60000' },
  { group: 'ai', key: 'max_tokens', value: '4096' },
  { group: 'ai', key: 'temperature', value: '0.7' },
  
  { group: 'system', key: 'login_max_attempts', value: '5' },
  { group: 'system', key: 'login_lock_duration', value: '15' },
  { group: 'system', key: 'token_expire_hours', value: '24' }
];

const keywords = [
  { keyword: '保温建材', category: '建筑材料', search_volume: 15000, difficulty: 3 },
  { keyword: '外墙保温', category: '建筑材料', search_volume: 12000, difficulty: 4 },
  { keyword: '保温板', category: '建筑材料', search_volume: 8000, difficulty: 2 },
  { keyword: '聚氨酯保温', category: '建筑材料', search_volume: 6000, difficulty: 3 },
  { keyword: '岩棉板', category: '建筑材料', search_volume: 5000, difficulty: 2 },
  { keyword: '挤塑板', category: '建筑材料', search_volume: 4500, difficulty: 2 },
  { keyword: '保温砂浆', category: '建筑材料', search_volume: 4000, difficulty: 2 },
  { keyword: '玻璃棉', category: '建筑材料', search_volume: 3500, difficulty: 3 },
  { keyword: '保温工程', category: '工程服务', search_volume: 3000, difficulty: 4 },
  { keyword: '节能保温', category: '建筑材料', search_volume: 2500, difficulty: 3 },
  { keyword: '保温材料厂家', category: '企业服务', search_volume: 2000, difficulty: 3 },
  { keyword: '保温材料价格', category: '市场行情', search_volume: 1800, difficulty: 2 }
];

const templates = [
  {
    name: '产品介绍模板',
    category: '产品',
    content: '# {{region}}{{keyword}}专业供应商\n\n## 产品概述\n\n{{region}}地区专业的{{keyword}}生产厂家，专注于高品质建筑保温材料的研发与生产。\n\n## 产品特点\n\n- 高品质原材料\n- 先进生产工艺\n- 专业技术团队\n- 完善售后服务\n\n## 适用范围\n\n适用于各类建筑的外墙保温、屋面保温、地面保温等工程。\n\n## 联系我们\n\n欢迎来电咨询{{keyword}}相关产品！',
    variables: JSON.stringify(['keyword', 'region'])
  },
  {
    name: '行业资讯模板',
    category: '资讯',
    content: '# {{keyword}}行业最新动态\n\n## 行业趋势\n\n{{year}}年{{keyword}}行业发展趋势分析，市场需求持续增长。\n\n## 政策解读\n\n最新建筑节能政策对{{keyword}}行业的影响分析。\n\n## 技术创新\n\n{{keyword}}生产技术创新与发展方向。\n\n## 市场展望\n\n未来{{keyword}}市场发展前景展望。',
    variables: JSON.stringify(['keyword', 'year', 'month'])
  },
  {
    name: '技术文章模板',
    category: '技术',
    content: '# {{keyword}}技术详解\n\n## 产品原理\n\n{{keyword}}的工作原理和技术特点。\n\n## 技术参数\n\n| 参数 | 规格 |\n|------|------|\n| 导热系数 | ≤0.030W/(m·K) |\n| 密度 | 200-300kg/m³ |\n| 抗压强度 | ≥0.4MPa |\n\n## 施工工艺\n\n{{keyword}}的正确施工方法和注意事项。\n\n## 质量标准\n\n国家相关质量标准和检测方法。',
    variables: JSON.stringify(['keyword'])
  }
];

const initData = async () => {
  try {
    console.log('开始初始化基础数据...');
    
    await sequelize.authenticate();
    console.log('数据库连接成功');

    await sequelize.sync({ alter: true });
    console.log('数据库模型同步完成');

    const platformCount = await Platform.count();
    if (platformCount === 0) {
      await Platform.bulkCreate(platforms);
      console.log('平台数据初始化完成');
    } else {
      console.log('平台数据已存在，跳过初始化');
    }

    const regionCount = await Region.count();
    if (regionCount === 0) {
      await sequelize.query('PRAGMA foreign_keys = OFF');
      await Region.bulkCreate(regions);
      await sequelize.query('PRAGMA foreign_keys = ON');
      console.log('地域数据初始化完成');
    } else {
      console.log('地域数据已存在，跳过初始化');
    }

    const configCount = await SystemConfig.count();
    if (configCount === 0) {
      await SystemConfig.bulkCreate(systemConfigs);
      console.log('系统配置初始化完成');
    } else {
      console.log('系统配置已存在，跳过初始化');
    }

    const keywordCount = await IndustryKeyword.count();
    if (keywordCount === 0) {
      await IndustryKeyword.bulkCreate(keywords);
      console.log('关键词数据初始化完成');
    } else {
      console.log('关键词数据已存在，跳过初始化');
    }

    const templateCount = await ArticleTemplate.count();
    if (templateCount === 0) {
      await ArticleTemplate.bulkCreate(templates);
      console.log('文章模板初始化完成');
    } else {
      console.log('文章模板已存在，跳过初始化');
    }

    console.log('基础数据初始化完成！');
    process.exit(0);
  } catch (error) {
    console.error('数据初始化失败:', error);
    process.exit(1);
  }
};

initData();