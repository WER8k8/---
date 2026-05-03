# Lingma 专属开发规则包
## 全国县域建材SEO矩阵AI全自动后台系统 - 后端开发规范

---

## 一、核心定位

Lingma 负责 **SEO矩阵后台系统的后端开发**，包括：
- Node.js + Express API开发
- MySQL数据库设计与实现
- Redis缓存配置
- BullMQ任务队列
- AI接口集成
- 多平台分发适配器

---

## 二、技术栈规范

### 2.1 强制技术选型
```json
{
  "node": ">=18.0.0",
  "express": "^4.18.2",
  "mysql2": "^3.6.5",
  "sequelize": "^6.35.2",
  "jsonwebtoken": "^9.0.2",
  "bcryptjs": "^2.4.3",
  "cors": "^2.8.5",
  "helmet": "^7.1.0",
  "express-rate-limit": "^7.1.5",
  "express-validator": "^7.0.1",
  "multer": "^1.4.5-lts.1",
  "xlsx": "^0.18.5",
  "bullmq": "^5.1.0",
  "ioredis": "^5.3.2",
  "axios": "^1.6.2",
  "dotenv": "^16.3.1",
  "winston": "^3.11.0",
  "node-cron": "^3.0.3",
  "cheerio": "^1.0.0-rc.12",
  "puppeteer": "^21.6.1",
  "openai": "^4.20.1",
  "crypto-js": "^4.2.0",
  "useragent": "^2.3.0",
  "compression": "^1.7.4",
  "morgan": "^1.10.0"
}
```

### 2.2 项目结构
```
seo-backend/
├── src/
│   ├── app.js                  # 应用入口
│   ├── config/
│   │   ├── database.js         # Sequelize配置
│   │   └── redis.js            # Redis配置
│   ├── controllers/             # 业务控制器
│   │   ├── auth.controller.js  # ✅已完成
│   │   ├── region.controller.js # ✅已完成
│   │   ├── config.controller.js # 待开发
│   │   ├── keyword.controller.js # 待开发
│   │   ├── template.controller.js # 待开发
│   │   ├── article.controller.js # 待开发
│   │   ├── platform.controller.js # 待开发
│   │   ├── publish.controller.js # 待开发
│   │   ├── dashboard.controller.js # 待开发
│   │   ├── monitoring.controller.js # 待开发
│   │   └── log.controller.js # 待开发
│   ├── models/
│   │   ├── AdminUser.js       # ✅已完成
│   │   ├── Region.js          # 待开发
│   │   ├── IndustryKeyword.js # 待开发
│   │   ├── ArticleTemplate.js # 待开发
│   │   ├── GeneratedArticle.js # 待开发
│   │   ├── PlatformAccount.js # 待开发
│   │   ├── PublishTask.js     # 待开发
│   │   ├── IndexingRecord.js  # 待开发
│   │   └── ...
│   ├── routes/                 # ✅11个路由文件已完成
│   ├── middleware/
│   │   ├── auth.js            # ✅已完成
│   │   └── errorHandler.js    # ✅已完成
│   ├── services/              # 业务服务层
│   │   ├── ai.service.js      # AI生成服务
│   │   ├── article.service.js  # 文章服务
│   │   └── publish.service.js  # 发布服务
│   ├── tasks/                  # BullMQ任务
│   │   ├── queue.js           # 队列配置
│   │   ├── article生成.js     # 文章生成任务
│   │   └── publish.js         # 发布任务
│   └── utils/
│       └── logger.js          # ✅已完成
├── database/
│   └── schema.sql             # ✅已设计19张表
└── package.json
```

---

## 三、数据库Schema规范

### 3.1 已有表结构（schema.sql）
```sql
-- 管理员表
CREATE TABLE admin_users (...);

-- 系统配置表
CREATE TABLE system_configs (...);

-- 地域词库表
CREATE TABLE regions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '地域名称',
  code VARCHAR(20) NOT NULL UNIQUE COMMENT '行政区划代码',
  parent_id INT DEFAULT 0 COMMENT '父级ID',
  level TINYINT DEFAULT 1 COMMENT '层级：1省2市3县',
  status TINYINT DEFAULT 1 COMMENT '状态：1启用0禁用',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_parent (parent_id),
  INDEX idx_level (level)
);

-- 行业关键词表
CREATE TABLE industry_keywords (
  id INT PRIMARY KEY AUTO_INCREMENT,
  keyword VARCHAR(200) NOT NULL COMMENT '关键词',
  category VARCHAR(50) DEFAULT '' COMMENT '分类',
  search_volume INT DEFAULT 0 COMMENT '搜索量',
  difficulty INT DEFAULT 0 COMMENT '难度',
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_keyword (keyword)
);

-- 长尾关键词表
CREATE TABLE longtail_keywords (
  id INT PRIMARY KEY AUTO_INCREMENT,
  region_id INT NOT NULL COMMENT '地域ID',
  keyword_id INT NOT NULL COMMENT '父级关键词ID',
  keyword VARCHAR(200) NOT NULL COMMENT '长尾关键词',
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_region (region_id),
  INDEX idx_keyword (keyword)
);

-- 文章模板表
CREATE TABLE article_templates (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '模板名称',
  category VARCHAR(50) DEFAULT '' COMMENT '分类',
  content TEXT NOT NULL COMMENT '模板内容',
  variables JSON COMMENT '变量配置',
  usage_count INT DEFAULT 0 COMMENT '使用次数',
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 生成文章表
CREATE TABLE generated_articles (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL COMMENT '文章标题',
  content TEXT NOT NULL COMMENT '文章内容',
  region_id INT COMMENT '地域ID',
  keyword_id INT COMMENT '关键词ID',
  template_id INT COMMENT '模板ID',
  word_count INT DEFAULT 0 COMMENT '字数',
  duplicate_rate DECIMAL(5,2) DEFAULT 0 COMMENT '重复率',
  compliance_status TINYINT DEFAULT 1 COMMENT '合规状态：1通过0违规',
  status TINYINT DEFAULT 0 COMMENT '发布状态：0待发布1已发布2已下线',
  published_at DATETIME COMMENT '发布时间',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_region (region_id),
  INDEX idx_status (status)
);

-- 平台账号表
CREATE TABLE platform_accounts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  platform_id INT NOT NULL COMMENT '平台ID',
  platform_name VARCHAR(50) NOT NULL COMMENT '平台名称',
  account_name VARCHAR(100) NOT NULL COMMENT '账号名称',
  cookie TEXT COMMENT 'Cookie凭证',
  token VARCHAR(500) COMMENT 'API Token',
  status TINYINT DEFAULT 1 COMMENT '状态：1正常0异常',
  last_publish_at DATETIME COMMENT '最后发布',
  today_publish_count INT DEFAULT 0 COMMENT '今日发布数',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_platform (platform_id),
  INDEX idx_status (status)
);

-- 发布任务表
CREATE TABLE publish_tasks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  article_id INT NOT NULL COMMENT '文章ID',
  platform_account_id INT NOT NULL COMMENT '平台账号ID',
  status TINYINT DEFAULT 0 COMMENT '状态：0待执行1执行中2成功3失败',
  error_message TEXT COMMENT '错误信息',
  retry_count INT DEFAULT 0 COMMENT '重试次数',
  published_url VARCHAR(500) COMMENT '发布后的URL',
  executed_at DATETIME COMMENT '执行时间',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_article (article_id),
  INDEX idx_status (status)
);

-- 收录记录表
CREATE TABLE indexing_records (
  id INT PRIMARY KEY AUTO_INCREMENT,
  article_id INT NOT NULL COMMENT '文章ID',
  search_engine VARCHAR(50) DEFAULT 'baidu' COMMENT '搜索引擎',
  keyword VARCHAR(200) COMMENT '关键词',
  is_indexed TINYINT DEFAULT 0 COMMENT '是否收录：1是0否',
  ranking INT DEFAULT 0 COMMENT '排名',
  is_homepage TINYINT DEFAULT 0 COMMENT '是否首页',
  checked_at DATETIME COMMENT '检测时间',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_article (article_id),
  INDEX idx_indexed (is_indexed)
);

-- 系统预警表
CREATE TABLE system_alerts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  type VARCHAR(50) NOT NULL COMMENT '预警类型',
  title VARCHAR(200) NOT NULL COMMENT '预警标题',
  description TEXT COMMENT '预警描述',
  level TINYINT DEFAULT 1 COMMENT '级别：1低2中3高',
  status TINYINT DEFAULT 1 COMMENT '状态：1未读2已读3已处理',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE operation_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '用户名',
  module VARCHAR(50) NOT NULL COMMENT '模块',
  action VARCHAR(100) NOT NULL COMMENT '操作',
  description TEXT COMMENT '描述',
  ip_address VARCHAR(45) DEFAULT '' COMMENT 'IP地址',
  user_agent TEXT COMMENT 'UserAgent',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user (user_id),
  INDEX idx_module (module),
  INDEX idx_created (created_at)
);

-- 登录日志表
CREATE TABLE login_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT COMMENT '用户ID',
  username VARCHAR(50) NOT NULL COMMENT '用户名',
  ip_address VARCHAR(45) DEFAULT '' COMMENT 'IP地址',
  device VARCHAR(100) DEFAULT '' COMMENT '设备',
  login_result TINYINT DEFAULT 1 COMMENT '登录结果：1成功0失败',
  fail_reason VARCHAR(200) DEFAULT '' COMMENT '失败原因',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_username (username),
  INDEX idx_created (created_at)
);
```

---

## 四、API接口规范

### 4.1 认证接口（已完成）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录 |
| POST | /api/v1/auth/refresh | 刷新令牌 |
| POST | /api/v1/auth/logout | 登出 |
| GET | /api/v1/auth/profile | 获取个人信息 |
| PUT | /api/v1/auth/password | 修改密码 |

### 4.2 系统配置接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/configs | 获取所有配置 |
| GET | /api/v1/configs/:group | 获取指定分组配置 |
| PUT | /api/v1/configs/:group | 更新指定分组配置 |

### 4.3 地域管理接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/regions/tree | 获取地域树形结构 |
| GET | /api/v1/regions | 分页获取地域列表 |
| GET | /api/v1/regions/:id | 获取地域详情 |
| POST | /api/v1/regions | 新增地域 |
| PUT | /api/v1/regions/:id | 更新地域 |
| DELETE | /api/v1/regions/:id | 删除地域 |
| POST | /api/v1/regions/import | 批量导入 |
| GET | /api/v1/regions/export | 导出地域 |

### 4.4 关键词管理接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/keywords | 分页获取关键词 |
| GET | /api/v1/keywords/:id | 获取关键词详情 |
| POST | /api/v1/keywords | 新增关键词 |
| PUT | /api/v1/keywords/:id | 更新关键词 |
| DELETE | /api/v1/keywords/:id | 删除关键词 |
| POST | /api/v1/keywords/import | 批量导入 |
| POST | /api/v1/keywords/generate | AI生成长尾词 |
| GET | /api/v1/keywords/export | 导出关键词 |

### 4.5 模板管理接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/templates | 分页获取模板 |
| GET | /api/v1/templates/:id | 获取模板详情 |
| POST | /api/v1/templates | 新增模板 |
| PUT | /api/v1/templates/:id | 更新模板 |
| DELETE | /api/v1/templates/:id | 删除模板 |

### 4.6 文章管理接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/articles | 分页获取文章 |
| GET | /api/v1/articles/:id | 获取文章详情 |
| POST | /api/v1/articles | 新增文章 |
| PUT | /api/v1/articles/:id | 更新文章 |
| DELETE | /api/v1/articles/:id | 删除文章 |
| POST | /api/v1/articles/generate | AI批量生成文章 |
| POST | /api/v1/articles/publish | 发布文章 |
| GET | /api/v1/articles/stats | 获取文章统计 |

### 4.7 平台管理接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/platforms | 获取平台列表 |
| GET | /api/v1/platforms/:id/accounts | 获取平台账号列表 |
| POST | /api/v1/platforms/:id/accounts | 新增平台账号 |
| PUT | /api/v1/platforms/:id/accounts/:accountId | 更新账号 |
| DELETE | /api/v1/platforms/:id/accounts/:accountId | 删除账号 |

### 4.8 发布任务接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/publish/tasks | 创建发布任务 |
| GET | /api/v1/publish/tasks | 获取任务列表 |
| GET | /api/v1/publish/tasks/:id | 获取任务详情 |
| POST | /api/v1/publish/tasks/:id/retry | 重试失败任务 |
| GET | /api/v1/publish/logs | 获取发布日志 |

### 4.9 数据看板接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/dashboard/overview | 获取概览统计 |
| GET | /api/v1/dashboard/trends | 获取趋势数据 |
| GET | /api/v1/dashboard/heatmap | 获取热力图数据 |

### 4.10 收录监控接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/monitoring/indexing | 获取收录列表 |
| POST | /api/v1/monitoring/check-index | 提交收录检测任务 |
| GET | /api/v1/monitoring/alerts | 获取异常预警 |
| PUT | /api/v1/monitoring/alerts/:id | 处理预警 |

### 4.11 日志接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/logs/operations | 获取操作日志 |
| GET | /api/v1/logs/logins | 获取登录日志 |

---

## 五、响应格式规范

### 5.1 成功响应
```javascript
// 单条数据
{ code: 200, message: "success", data: T }

// 分页数据
{
  code: 200,
  message: "success",
  data: {
    list: T[],
    total: number,
    page: number,
    pageSize: number
  }
}

// 列表数据
{ code: 200, message: "success", data: T[] }
```

### 5.2 错误响应
```javascript
{ code: number, message: string }
```

### 5.3 错误码
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

---

## 六、安全规范

### 6.1 认证与授权
- 所有API（除登录外）需JWT Token认证
- Token放在 `Authorization: Bearer <token>` 头部
- Token有效期24小时，刷新Token有效期7天

### 6.2 密码安全
- 密码使用 bcryptjs 加密存储
- 盐值轮数10
- 登录失败5次锁定30分钟

### 6.3 接口安全
- 使用 helmet 设置安全头
- 使用 cors 限制跨域
- 使用 rate-limit 限制请求频率
- 输入参数使用 express-validator 验证

### 6.4 日志规范
- 使用 Winston 记录日志
- 记录所有操作日志和登录日志
- 敏感操作需记录IP和UserAgent

---

## 七、AI服务集成规范

### 7.1 AI生成文章流程
```javascript
// 1. 接收生成请求
// 2. 查询地域+关键词+模板
// 3. 构造Prompt
// 4. 调用AI接口生成内容
// 5. 检测重复率和合规性
// 6. 保存到数据库
// 7. 返回生成结果
```

### 7.2 Prompt模板变量
```
{{region_name}} - 地域名称
{{province_name}} - 省份名称
{{city_name}} - 城市名称
{{keyword}} - 主关键词
{{longtail_keyword}} - 长尾关键词
{{product_name}} - 产品名称
{{brand_name}} - 品牌名称
{{company_intro}} - 公司简介
{{contact_phone}} - 联系电话
{{article_length}} - 文章字数要求
```

---

## 八、任务队列规范

### 8.1 BullMQ队列
```javascript
// 文章生成队列
const articleQueue = new Queue('article-generation', redisOptions);

// 发布队列
const publishQueue = new Queue('article-publish', redisOptions);

// 收录检测队列
const indexingQueue = new Queue('indexing-check', redisOptions);
```

### 8.2 重试机制
- 失败任务自动重试3次
- 重试间隔：1分钟、5分钟、15分钟
- 3次失败后标记为失败，发送预警

---

## 九、代码风格规范

### 9.1 文件命名
- 控制器：`*.controller.js`
- 模型：`*.model.js`
- 路由：`*.routes.js`
- 中间件：`*.middleware.js`
- 服务：`*.service.js`

### 9.2 变量命名
- 变量/函数：camelCase
- 常量：UPPER_SNAKE_CASE
- 类名：PascalCase

### 9.3 注释规范
```javascript
/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<Object>} 登录结果
 */
const login = async (username, password) => { ... }
```

---

## 十、开发优先级

### P0 - 核心功能（必须完成）
1. ✅ 认证接口（已完成）
2. 🟡 地域管理CRUD
3. 🟡 系统配置CRUD
4. 🟡 数据看板接口

### P1 - 业务功能（重要）
5. 🟡 关键词管理CRUD + AI组词
6. 🟡 模板管理CRUD
7. 🟡 文章管理CRUD + AI生成
8. 🟡 平台账号管理

### P2 - 分发功能（扩展）
9. 🟡 发布任务管理
10. 🟡 收录监控
11. 🟡 系统日志

---

## 十一、交付标准

1. 所有接口返回格式符合规范
2. 所有CRUD操作完整实现
3. 错误处理完善，有友好错误提示
4. 日志记录完整
5. 代码注释清晰
6. 通过Postman测试验证

---

## 十二、文件路径约定

**严格遵守以下路径，禁止更改：**
- 后端入口：`seo-backend/src/app.js`
- 配置文件：`seo-backend/src/config/database.js`
- 数据库Schema：`seo-backend/database/schema.sql`
- 路由文件：`seo-backend/src/routes/*.routes.js`
- 控制器文件：`seo-backend/src/controllers/*.controller.js`
- 模型文件：`seo-backend/src/models/*.model.js`
