# SEO 核心功能设计

## 1. LLMs.txt 生成器

### 功能描述
为 AI 搜索引擎（如 Claude、GPT、Gemini）生成优化的 llms.txt 文件，提高网站被 AI 模型收录和引用的概率。

### 核心代码结构
```python
class LLMSTxtGenerator:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.technical_whitelist = {
            'density_range': (800, 1950),
            'strength_grades': ['LC5.0', 'LC7.5', 'LC10', 'LC15', 'LC20', 'LC25', 'LC30', 'LC35', 'LC40', 'LC45', 'LC50'],
            'thermal_conductivity': (0.18, 0.28)
        }
    
    async def generate_llms_txt(self, config):
        # AI-powered generation with compliance validation
    
    def validate_compliance(self, content):
        # Check technical parameters and forbidden words
    
    def add_technical_disclaimer(self, content):
        # Add JGJ/T 12-2019 disclaimer
```

### API 端点
```
POST /api/v1/seo/generate-llms-txt
POST /api/v1/seo/validate-llms-txt
```

## 2. AI 内容优化器

### 功能描述
自动优化网页内容的 Meta 标题、Meta 描述、Alt 文本等 SEO 元素，同时保证专业技术参数不被 AI 篡改。

### 核心逻辑
1. 提取原文中的技术参数（密度、强度等级、导热系数等）
2. 调用 AI 进行内容优化
3. 将技术参数还原并验证合规性
4. 生成优化报告（含改动点、Token消耗、费用）

### API 端点
```
POST /api/v1/seo/optimize-content
```

### 优化类型
| 类型 | 说明 | 目标长度 |
|------|------|---------|
| title | Meta标题优化 | 15-30字 |
| description | Meta描述优化 | 50-120字 |
| alt_text | 图片Alt文本优化 | 5-20字 |
| content | 正文内容优化 | 500-2000字 |

## 3. 网站审计引擎

### 功能描述
11 维度自动化网站 SEO 审计，80+ 检查规则，生成优先级推荐。

### 审计维度
| # | 维度 | 检查项数 | 说明 |
|---|------|---------|------|
| 1 | 技术合规 | 8 | 密度范围、强度等级、禁用营销词 |
| 2 | AI搜索优化 | 6 | llms.txt存在性、EEAT信号 |
| 3 | Meta标签 | 10 | 标题长度、描述质量、关键词密度 |
| 4 | 页面结构 | 8 | H标签层级、Schema标记 |
| 5 | 移动端适配 | 6 | Viewport、触摸友好 |
| 6 | 性能优化 | 8 | LCP、FID、CLS核心指标 |
| 7 | 链接质量 | 6 | 内链结构、外链质量、死链检测 |
| 8 | 内容质量 | 8 | 原创度、关键词密度、可读性 |
| 9 | 安全合规 | 6 | HTTPS、CSP、广告法合规 |
| 10 | AI爬虫友好 | 6 | robots.txt、sitemap、llms.txt |
| 11 | 社交媒体 | 4 | OG标签、Twitter Card |

### 评分算法
```
score = max(0, 100 - (high_issues * 10 + medium_issues * 5 + low_issues * 2))
```

### API 端点
```
POST /api/v1/seo/audit
GET /api/v1/seo/audit/{id}
```

## 4. 关键词排名追踪

### 功能描述
自动化追踪核心关键词在百度的排名变化，提供趋势分析和预警。

### 数据结构
```python
@dataclass
class KeywordRanking:
    keyword_id: UUID
    keyword: str
    current_rank: int
    previous_rank: int
    rank_change: int  # 正值上升，负值下降
    search_engine: str
    check_date: date
```

## 5. Schema 标记生成

### 支持的 Schema 类型
| 类型 | 适用页面 | 说明 |
|------|---------|------|
| Product | 产品详情页 | 产品规格、价格、评价 |
| Article | 新闻/文章页 | 标题、作者、发布日期 |
| BreadcrumbList | 所有页面 | 面包屑导航 |
| FAQPage | FAQ页面 | 问答结构化数据 |
| Organization | 关于我们 | 企业信息、联系方式 |
| LocalBusiness | 联系我们 | 本地商家信息、地图 |

## 6. EEAT 信号增强

### 实现方式
1. 作者信息结构化（Author Schema）
2. 引用来源标注（Citation markup）
3. 资质证书展示（Certification schema）
4. 行业标准引用（JGJ/T 12-2019）
5. 客户案例结构化（Review schema）
6. 更新时间标注（lastReviewed）
