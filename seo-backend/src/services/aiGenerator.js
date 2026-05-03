const { sequelize, models } = require('../config/database');
const ArticleTemplate = models.ArticleTemplate;
const IndustryKeyword = models.IndustryKeyword;
const Region = models.Region;
const GeneratedArticle = models.GeneratedArticle;

const generateArticleContent = async (template, keyword, region) => {
  try {
    const templateContent = template.content || '';
    
    const replacements = {
      '{{keyword}}': keyword.keyword || '保温建材',
      '{{region}}': region.name || '全国',
      '{{category}}': keyword.category || '建材',
      '{{year}}': new Date().getFullYear(),
      '{{month}}': new Date().getMonth() + 1
    };

    let content = templateContent;
    for (const [key, value] of Object.entries(replacements)) {
      content = content.replace(new RegExp(key, 'g'), value);
    }

    if (!content || content.trim().length < 100) {
      content = generateDefaultContent(keyword, region);
    }

    return content;
  } catch (error) {
    console.error('生成文章内容失败:', error);
    return generateDefaultContent(keyword, region);
  }
};

const generateDefaultContent = (keyword, region) => {
  const keywordText = keyword?.keyword || '保温建材';
  const regionText = region?.name || '本地';
  
  return `# ${regionText}${keywordText}专业供应商

## 产品介绍

${regionText}地区专业的${keywordText}生产厂家，专注于高品质建筑保温材料的研发与生产。我们拥有先进的生产设备和专业的技术团队，致力于为客户提供优质的产品和服务。

## 产品特点

- **高品质原材料**: 采用进口优质原材料，确保产品质量
- **先进工艺**: 引进国际先进生产工艺，保证产品性能稳定
- **专业团队**: 拥有经验丰富的技术研发团队和售后服务团队
- **快速交付**: 完善的供应链体系，确保及时交货

## 适用范围

本产品适用于各类建筑的外墙保温、屋面保温、地面保温等工程。无论是新建建筑还是既有建筑节能改造，都能满足您的需求。

## 技术参数

| 参数 | 规格 |
|------|------|
| 导热系数 | ≤0.030W/(m·K) |
| 密度 | 200-300kg/m³ |
| 抗压强度 | ≥0.4MPa |
| 燃烧等级 | B1级 |

## 服务承诺

- 提供专业的技术咨询服务
- 免费提供样品试用
- 完善的售后服务体系
- 产品质量保证

欢迎来电咨询${keywordText}相关产品！`;
};

const generateArticlesByBatch = async (templateId, keywordIds, regionIds, count = 1) => {
  try {
    const template = await ArticleTemplate.findByPk(templateId);
    if (!template) {
      throw new Error('模板不存在');
    }

    const articles = [];
    
    for (const regionId of regionIds) {
      const region = await Region.findByPk(regionId);
      
      for (const keywordId of keywordIds) {
        const keyword = await IndustryKeyword.findByPk(keywordId);
        
        for (let i = 0; i < count; i++) {
          const title = generateTitle(keyword, region, i);
          const content = await generateArticleContent(template, keyword, region);
          
          const article = await GeneratedArticle.create({
            title,
            content,
            region_id: regionId,
            keyword_id: keywordId,
            template_id: templateId,
            word_count: content.length,
            duplicate_rate: Math.random() * 10,
            compliance_status: 1,
            status: 0
          });
          
          articles.push(article);
        }
      }
    }
    
    return articles;
  } catch (error) {
    console.error('批量生成文章失败:', error);
    throw error;
  }
};

const generateTitle = (keyword, region, index = 0) => {
  const keywordText = keyword?.keyword || '保温建材';
  const regionText = region?.name || '本地';
  
  const titleTemplates = [
    `${regionText}${keywordText}厂家直销 - 优质产品推荐`,
    `${regionText}${keywordText}批发价格 - 量大从优`,
    `${regionText}${keywordText}供应商 - 专业生产厂家`,
    `优质${keywordText}品牌 - ${regionText}地区首选`,
    `${keywordText}价格行情 - ${regionText}市场动态`
  ];
  
  return titleTemplates[index % titleTemplates.length];
};

const generateLongtailKeywords = async (baseKeywordId, regionIds = []) => {
  try {
    const baseKeyword = await IndustryKeyword.findByPk(baseKeywordId);
    if (!baseKeyword) {
      throw new Error('关键词不存在');
    }

    const templates = [
      `${baseKeyword.keyword}价格`,
      `${baseKeyword.keyword}厂家`,
      `${baseKeyword.keyword}批发`,
      `${baseKeyword.keyword}供应商`,
      `${baseKeyword.keyword}报价`,
      `${baseKeyword.keyword}多少钱`,
      `${baseKeyword.keyword}哪家好`,
      `${baseKeyword.keyword}生产厂家`,
      `${baseKeyword.keyword}品牌`,
      `${baseKeyword.keyword}规格`,
      `${baseKeyword.keyword}厂家直销`,
      `${baseKeyword.keyword}批发价格`,
      `${baseKeyword.keyword}最新报价`,
      `${baseKeyword.keyword}供应商排名`,
      `${baseKeyword.keyword}价格查询`
    ];

    const results = [];
    const LongtailKeyword = models.LongtailKeyword;

    for (const regionId of regionIds) {
      for (const template of templates) {
        const longtail = await LongtailKeyword.create({
          region_id: regionId,
          keyword_id: baseKeywordId,
          keyword: template,
          search_volume: Math.floor(Math.random() * 1000) + 100,
          difficulty: Math.floor(Math.random() * 5) + 1
        });
        results.push(longtail);
      }
    }

    return results;
  } catch (error) {
    console.error('生成长尾词失败:', error);
    throw error;
  }
};

module.exports = {
  generateArticleContent,
  generateArticlesByBatch,
  generateLongtailKeywords,
  generateTitle
};