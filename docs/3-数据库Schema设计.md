# 数据库 Schema 设计

## 核心表结构 (PostgreSQL)

### 1. 用户表 (users)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| role | ENUM('admin','editor','viewer') | DEFAULT 'viewer' | 角色 |
| is_active | BOOLEAN | DEFAULT true | 是否激活 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 2. 产品表 (products)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(200) | NOT NULL | 产品名称 |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL别名 |
| category_id | UUID | FK → categories.id | 分类 |
| density | DECIMAL(6,2) | CHECK(800-1950) | 干密度(kg/m³) |
| strength_grade | VARCHAR(10) | CHECK(LC5.0-LC50) | 强度等级 |
| thermal_conductivity | DECIMAL(4,2) | CHECK(0.18-0.28) | 导热系数(W/m·K) |
| description | TEXT | | 产品描述 |
| meta_title | VARCHAR(100) | | SEO标题 |
| meta_description | VARCHAR(200) | | SEO描述 |
| sort_order | INTEGER | DEFAULT 0 | 排序 |
| is_published | BOOLEAN | DEFAULT false | 发布状态 |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### 3. 分类表 (categories)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(100) | NOT NULL | 分类名称 |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL别名 |
| parent_id | UUID | FK → categories.id, NULLABLE | 父分类 |
| sort_order | INTEGER | DEFAULT 0 | 排序 |
| created_at | TIMESTAMP | DEFAULT NOW() | |

### 4. 内容页面表 (content_pages)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| title | VARCHAR(200) | NOT NULL | 页面标题 |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL别名 |
| content | TEXT | NOT NULL | 页面内容(HTML) |
| meta_title | VARCHAR(100) | | SEO标题 |
| meta_description | VARCHAR(200) | | SEO描述 |
| page_type | ENUM('about','news','contact','custom') | | 页面类型 |
| is_published | BOOLEAN | DEFAULT false | |
| published_at | TIMESTAMP | | 发布时间 |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### 5. SEO 元数据表 (seo_metadata)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型(product/page) |
| resource_id | UUID | NOT NULL | 资源ID |
| meta_title | VARCHAR(100) | | Meta标题 |
| meta_description | VARCHAR(200) | | Meta描述 |
| meta_keywords | TEXT | | Meta关键词 |
| og_title | VARCHAR(100) | | Open Graph标题 |
| og_description | VARCHAR(200) | | Open Graph描述 |
| og_image | VARCHAR(500) | | Open Graph图片 |
| schema_markup | JSONB | | Schema标记(JSON-LD) |
| canonical_url | VARCHAR(500) | | 规范URL |
| robots | VARCHAR(100) | | Robots指令 |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### 6. 关键词表 (keywords)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| keyword | VARCHAR(200) | UNIQUE, NOT NULL | 关键词 |
| search_volume | INTEGER | DEFAULT 0 | 搜索量 |
| difficulty | DECIMAL(3,1) | CHECK(0-100) | 竞争难度 |
| current_rank | INTEGER | | 当前排名 |
| target_rank | INTEGER | DEFAULT 1 | 目标排名 |
| group_name | VARCHAR(100) | | 关键词分组 |
| is_active | BOOLEAN | DEFAULT true | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### 7. 关键词排名记录表 (keyword_rankings)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| keyword_id | UUID | FK → keywords.id | 关键词ID |
| rank | INTEGER | | 当前排名 |
| search_engine | VARCHAR(50) | DEFAULT 'baidu' | 搜索引擎 |
| check_date | DATE | NOT NULL | 检查日期 |
| created_at | TIMESTAMP | DEFAULT NOW() | |

### 8. 网站审计记录表 (site_audits)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| url | VARCHAR(500) | NOT NULL | 审计URL |
| audit_type | VARCHAR(50) | | 审计类型(full/quick) |
| score | INTEGER | CHECK(0-100) | 总分 |
| issues | JSONB | | 问题列表 |
| recommendations | JSONB | | 建议列表 |
| raw_data | JSONB | | 原始数据 |
| started_at | TIMESTAMP | | 开始时间 |
| completed_at | TIMESTAMP | | 完成时间 |
| created_at | TIMESTAMP | DEFAULT NOW() | |

### 9. AI 优化日志表 (ai_optimization_logs)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型 |
| resource_id | UUID | NOT NULL | 资源ID |
| optimization_type | VARCHAR(50) | | 优化类型 |
| original_content | TEXT | | 原始内容 |
| optimized_content | TEXT | | 优化后内容 |
| ai_model | VARCHAR(50) | | 使用的AI模型 |
| tokens_used | INTEGER | | Token消耗 |
| cost | DECIMAL(10,6) | | 花费($) |
| status | ENUM('pending','success','failed') | | 状态 |
| created_at | TIMESTAMP | DEFAULT NOW() | |

### 10. LLMs 配置表 (llms_config)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_type | VARCHAR(100) | | 业务类型 |
| keywords | TEXT[] | | 核心关键词列表 |
| ai_model | VARCHAR(50) | | AI模型选择 |
| temperature | DECIMAL(2,1) | DEFAULT 0.3 | 温度参数 |
| max_tokens | INTEGER | DEFAULT 2000 | 最大Token |
| auto_update | BOOLEAN | DEFAULT false | 自动更新 |
| content | TEXT | | 生成的llms.txt内容 |
| version | VARCHAR(20) | | 版本号 |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### 11. 操作日志表 (operation_logs)
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id | 操作人 |
| action | VARCHAR(100) | NOT NULL | 操作动作 |
| resource_type | VARCHAR(50) | | 资源类型 |
| resource_id | UUID | | 资源ID |
| details | JSONB | | 操作详情 |
| ip_address | VARCHAR(45) | | IP地址 |
| created_at | TIMESTAMP | DEFAULT NOW() | |

## 索引设计
| 表 | 索引字段 | 类型 | 说明 |
|----|---------|------|------|
| products | (category_id, is_published) | B-tree | 分类筛选 |
| products | slug | UNIQUE | URL查找 |
| products | (strength_grade, density) | B-tree | 技术参数查询 |
| content_pages | (slug, is_published) | B-tree | URL查找 |
| keywords | keyword | UNIQUE | 关键词查重 |
| keywords | (group_name, is_active) | B-tree | 分组筛选 |
| keyword_rankings | (keyword_id, check_date) | B-tree | 排名趋势 |
| seo_metadata | (resource_type, resource_id) | UNIQUE | 资源关联 |
| site_audits | (url, created_at) | B-tree | 审计历史 |
| operation_logs | (user_id, created_at) | B-tree | 审计追踪 |
