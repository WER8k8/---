# 全国县域建材SEO矩阵AI全自动后台系统 - API接口契约文档

> **文档版本**: v1.0
> **创建日期**: 2026-05-03
> **适用范围**: 前后端开发必须严格遵守此契约，任何修改需经架构师批准

---

## 基础规范

### 1. 接口基础URL
- 开发环境: `http://localhost:3000/api/v1`
- 生产环境: `https://api.youdingjiancai.com/api/v1`

### 2. 认证方式
- JWT Token认证
- Header: `Authorization: Bearer {token}`
- Token有效期: 24小时
- 刷新Token有效期: 7天

### 3. 统一响应格式
```typescript
// 成功响应
{
  code: 200,
  message: "success",
  data: T
}

// 分页响应
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

// 错误响应
{
  code: number,  // 错误码
  message: string  // 错误信息
}
```

### 4. 错误码定义
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 1001 | 登录失败 |
| 1002 | 账号被锁定 |
| 1003 | 账号已过期 |
| 2001 | 地域数据不存在 |
| 2002 | 关键词重复 |
| 3001 | 模板不存在 |
| 3002 | 文章生成失败 |
| 4001 | 平台账号异常 |
| 4002 | 发布失败 |
| 4003 | 账号被冻结 |
| 5001 | 收录检测失败 |

---

## 模块1: 认证与授权

### 1.1 管理员登录
- **POST** `/auth/login`
- **请求体**:
```typescript
{
  username: string,      // 用户名
  password: string,      // 密码
  captcha?: string,      // 验证码
  rememberMe?: boolean   // 记住登录
}
```
- **响应**:
```typescript
{
  token: string,         // 访问令牌
  refreshToken: string,  // 刷新令牌
  expiresIn: number,     // 过期时间(秒)
  user: {
    id: number,
    username: string,
    nickname: string,
    avatar: string,
    roles: string[]
  }
}
```

### 1.2 刷新Token
- **POST** `/auth/refresh`
- **请求体**: `{ refreshToken: string }`
- **响应**: 同登录响应

### 1.3 退出登录
- **POST** `/auth/logout`
- **Header**: 需要Authorization
- **响应**: `{ code: 200, message: "退出成功" }`

### 1.4 获取当前用户信息
- **GET** `/auth/profile`
- **Header**: 需要Authorization
- **响应**:
```typescript
{
  id: number,
  username: string,
  nickname: string,
  avatar: string,
  email: string,
  phone: string,
  roles: string[],
  permissions: string[]
}
```

### 1.5 修改密码
- **PUT** `/auth/password`
- **请求体**:
```typescript
{
  oldPassword: string,
  newPassword: string
}
```

---

## 模块2: 系统全局设置

### 2.1 获取系统配置
- **GET** `/configs`
- **查询参数**: `?group=basic` (可选，按分组筛选)
- **响应**:
```typescript
{
  basic: {
    brand_name: string,
    official_website: string,
    contact_phone: string,
    company_intro: string
  },
  link: {
    link_insert_position: string,
    link_format: string
  },
  ai: {
    ai_model: string,
    article_length: number,
    rewrite_strength: string
  },
  risk: {
    daily_limit_per_platform: number,
    publish_interval_min: number,
    publish_interval_max: number
  }
}
```

### 2.2 更新系统配置
- **PUT** `/configs`
- **请求体**: 配置对象 (同获取响应格式)
- **响应**: `{ code: 200, message: "配置更新成功" }`

### 2.3 获取操作日志
- **GET** `/logs/operations`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  module?: string,
  action?: string,
  userId?: number,
  startDate?: string,
  endDate?: string
}
```
- **响应**: 分页日志列表

### 2.4 获取登录日志
- **GET** `/logs/logins`
- **查询参数**: 同操作日志
- **响应**: 分页登录日志列表

---

## 模块3: 全国地域词库管理

### 3.1 获取地域树
- **GET** `/regions/tree`
- **响应**:
```typescript
{
  id: number,
  name: string,
  code: string,
  level: number,
  children: Region[]
}[]
```

### 3.2 获取地域列表
- **GET** `/regions`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  level?: number,      // 1省 2市 3县
  parentId?: number,
  keyword?: string,    // 搜索关键词
  status?: number      // 1启用 0禁用
}
```
- **响应**: 分页地域列表

### 3.3 批量更新地域状态
- **PUT** `/regions/batch-status`
- **请求体**:
```typescript
{
  ids: number[],
  status: number  // 1启用 0禁用
}
```

### 3.4 导出地域数据
- **GET** `/regions/export`
- **查询参数**: `?format=excel&provinceIds=1,2,3`
- **响应**: Excel文件下载

### 3.5 导入地域数据
- **POST** `/regions/import`
- **Content-Type**: `multipart/form-data`
- **请求体**: `{ file: File }`
- **响应**: `{ code: 200, message: "导入成功", data: { success: number, failed: number } }`

---

## 模块4: 行业关键词库与AI组词

### 4.1 获取行业关键词列表
- **GET** `/keywords/industry`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  category?: string,   // 产品/厂家/工程/价格
  keyword?: string,
  status?: number
}
```

### 4.2 创建行业关键词
- **POST** `/keywords/industry`
- **请求体**:
```typescript
{
  keyword: string,
  category: string,
  searchVolume?: number,
  competition?: number
}
```

### 4.3 批量导入关键词
- **POST** `/keywords/industry/import`
- **Content-Type**: `multipart/form-data`
- **请求体**: `{ file: File }`

### 4.4 AI智能组词
- **POST** `/keywords/generate`
- **请求体**:
```typescript
{
  regionIds: number[],           // 选中的县域ID列表
  templates: string[],           // 组词模板
  // 模板示例: "{县城}+{产品}+厂家"
  categories?: string[]          // 关键词分类过滤
}
```
- **响应**:
```typescript
{
  taskId: string,          // 异步任务ID
  estimatedCount: number,  // 预计生成数量
  message: "组词任务已提交"
}
```

### 4.5 获取组词任务状态
- **GET** `/keywords/generate/{taskId}`
- **响应**:
```typescript
{
  status: "pending" | "running" | "completed" | "failed",
  progress: number,        // 进度百分比
  resultCount: number,     // 已生成数量
  error?: string
}
```

### 4.6 获取长尾关键词列表
- **GET** `/keywords/longtail`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  regionId?: number,
  keyword?: string,
  status?: number
}
```

---

## 模块5: AI文案模板与全自动生成

### 5.1 获取文案模板列表
- **GET** `/templates`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  category?: string,
  status?: number
}
```

### 5.2 创建文案模板
- **POST** `/templates`
- **请求体**:
```typescript
{
  name: string,
  content: string,         // 模板内容，变量用{variable}表示
  category: string,
  variables: string[]      // 变量列表
}
```

### 5.3 更新文案模板
- **PUT** `/templates/{id}`
- **请求体**: 同创建

### 5.4 删除文案模板
- **DELETE** `/templates/{id}`

### 5.5 AI批量生成文章
- **POST** `/articles/generate`
- **请求体**:
```typescript
{
  regionIds: number[],           // 县域ID列表
  templateId: number,            // 模板ID
  keywords?: string[],           // 指定关键词
  options?: {
    duplicateRate?: number,      // 最大重复率
    complianceCheck?: boolean    // 是否合规检测
  }
}
```
- **响应**:
```typescript
{
  taskId: string,
  estimatedCount: number,
  message: "文章生成任务已提交"
}
```

### 5.6 获取文章列表
- **GET** `/articles`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  regionId?: number,
  status?: number,       // 0草稿 1待发布 2已发布 3发布失败
  complianceStatus?: number,
  startDate?: string,
  endDate?: string
}
```

### 5.7 获取文章详情
- **GET** `/articles/{id}`
- **响应**:
```typescript
{
  id: number,
  regionId: number,
  regionName: string,
  templateId: number,
  title: string,
  content: string,
  keywords: string,
  duplicateRate: number,
  complianceStatus: number,
  status: number,
  publishPlatform: string,
  publishUrl: string,
  createdAt: string,
  publishedAt: string
}
```

### 5.8 更新文章
- **PUT** `/articles/{id}`
- **请求体**:
```typescript
{
  title?: string,
  content?: string,
  keywords?: string,
  status?: number
}
```

### 5.9 批量设置文章状态
- **PUT** `/articles/batch-status`
- **请求体**:
```typescript
{
  ids: number[],
  status: number  // 1待发布
}
```

---

## 模块6: 多平台账号管理与AI分发中心

### 6.1 获取平台列表
- **GET** `/platforms`
- **响应**:
```typescript
{
  id: number,
  name: string,
  code: string,
  category: string,
  hasApi: number,
  dailyLimit: number,
  status: number
}[]
```

### 6.2 获取平台账号列表
- **GET** `/platforms/{platformId}/accounts`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  status?: number
}
```

### 6.3 创建平台账号
- **POST** `/platforms/{platformId}/accounts`
- **请求体**:
```typescript
{
  accountName: string,
  username: string,
  password: string,
  // 有API的平台
  accessToken?: string,
  refreshToken?: string,
  // 无API的平台
  cookieData?: string
}
```

### 6.4 更新平台账号
- **PUT** `/platforms/{platformId}/accounts/{accountId}`
- **请求体**: 同创建

### 6.5 删除平台账号
- **DELETE** `/platforms/{platformId}/accounts/{accountId}`

### 6.6 刷新账号Token
- **POST** `/platforms/accounts/{accountId}/refresh-token`
- **响应**: `{ code: 200, message: "Token刷新成功" }`

### 6.7 创建发布任务
- **POST** `/publish/tasks`
- **请求体**:
```typescript
{
  articleIds: number[],          // 文章ID列表
  platformIds: number[],         // 平台ID列表
  scheduleType: "immediate" | "scheduled" | "batch",
  scheduledTime?: string,        // 定时发布时间
  options?: {
    rewriteBeforePublish?: boolean,  // 发布前改写
    randomInterval?: boolean         // 随机间隔
  }
}
```
- **响应**:
```typescript
{
  taskId: string,
  taskCount: number,
  message: "发布任务已创建"
}
```

### 6.8 获取发布任务列表
- **GET** `/publish/tasks`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  status?: number,       // 0待发布 1发布中 2成功 3失败 4重试中
  platformId?: number,
  startDate?: string,
  endDate?: string
}
```

### 6.9 获取发布任务详情
- **GET** `/publish/tasks/{taskId}`
- **响应**:
```typescript
{
  id: string,
  articleId: number,
  articleTitle: string,
  accountId: number,
  accountName: string,
  platformId: number,
  platformName: string,
  status: number,
  retryCount: number,
  errorMessage: string,
  publishUrl: string,
  scheduledAt: string,
  publishedAt: string,
  createdAt: string
}
```

### 6.10 重试失败任务
- **POST** `/publish/tasks/{taskId}/retry`
- **响应**: `{ code: 200, message: "重试任务已提交" }`

### 6.11 获取发布日志
- **GET** `/publish/logs`
- **查询参数**: 同任务列表
- **响应**: 分页日志列表

---

## 模块7: 数据看板与收录监控

### 7.1 获取统计概览
- **GET** `/dashboard/overview`
- **响应**:
```typescript
{
  totalRegions: number,          // 覆盖县域数
  totalKeywords: number,         // 关键词总数
  totalArticles: number,         // 文章总数
  publishedArticles: number,     // 已发布数
  successRate: number,           // 发布成功率
  indexedCount: number,          // 收录数
  homepageCount: number,         // 首页数
  todayStats: {
    generated: number,
    published: number,
    failed: number,
    indexed: number
  }
}
```

### 7.2 获取趋势数据
- **GET** `/dashboard/trends`
- **查询参数**:
```typescript
{
  type: "article" | "publish" | "index",
  days: number  // 天数
}
```
- **响应**:
```typescript
{
  dates: string[],
  values: number[]
}
```

### 7.3 获取地域热力图数据
- **GET** `/dashboard/heatmap`
- **响应**:
```typescript
{
  regionId: number,
  regionName: string,
  province: string,
  articleCount: number,
  publishCount: number,
  indexCount: number,
  homepageCount: number
}[]
```

### 7.4 获取收录监控列表
- **GET** `/monitoring/indexing`
- **查询参数**:
```typescript
{
  page: number,
  pageSize: number,
  isIndexed?: number,    // 1已收录 0未收录
  isHomepage?: number,   // 1首页 0非首页
  platform?: string
}
```

### 7.5 触发收录检测
- **POST** `/monitoring/check-index`
- **请求体**:
```typescript
{
  articleIds?: number[],   // 指定文章ID，不传则检测全部
  platform?: string        // 搜索引擎，默认baidu
}
```
- **响应**:
```typescript
{
  taskId: string,
  message: "收录检测任务已提交"
}
```

### 7.6 获取异常预警
- **GET** `/monitoring/alerts`
- **响应**:
```typescript
{
  accountAlerts: {         // 账号异常
    accountId: number,
    accountName: string,
    reason: string,
    frozenUntil: string
  }[],
  publishAlerts: {         // 发布异常
    platformId: number,
    platformName: string,
    failRate: number,
    failCount: number
  }[],
  regionAlerts: {          // 县域异常
    regionId: number,
    regionName: string,
    reason: string
  }[]
}
```

---

## 附录: 数据字典

### 文章状态
| 值 | 说明 |
|----|------|
| 0 | 草稿 |
| 1 | 待发布 |
| 2 | 已发布 |
| 3 | 发布失败 |

### 发布任务状态
| 值 | 说明 |
|----|------|
| 0 | 待发布 |
| 1 | 发布中 |
| 2 | 成功 |
| 3 | 失败 |
| 4 | 重试中 |

### 平台账号状态
| 值 | 说明 |
|----|------|
| 1 | 正常 |
| 0 | 禁用 |
| 2 | 冻结 |
| 3 | 异常 |

### 合规状态
| 值 | 说明 |
|----|------|
| 0 | 未检测 |
| 1 | 通过 |
| 2 | 不通过 |
