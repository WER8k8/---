# Trae 与 Lingma 开发分工文档

## 一、分工原则

| 角色 | 核心定位 | 技术栈 |
|------|----------|--------|
| **Trae** | 前端主导、架构统筹、智能体调度 | Vue3/Nuxt3、Element Plus、TypeScript、SCSS |
| **Lingma** | 后端主导、接口开发、数据库设计 | Node.js/Express、MySQL、Redis、BullMQ |

---

## 二、项目一：官网系统（已上线，协作维护）

### 2.1 前端开发 → Trae 负责
- `frontend/` - Nuxt 3 全栈前端
- `frontend/admin/` - Vue 3 后台管理前端
- 现有页面功能迭代、样式优化、Bug修复

### 2.2 后端开发 → Lingma 负责
- `backend/` - FastAPI Python 后端
- `ai-engine/` - AI 引擎模块
- 数据库维护、API扩展、功能升级

### 2.3 协作维护规则
- 两方不得修改对方负责模块的核心数据结构
- 接口变动需双方确认后执行
- 共用 `.env` 配置通过环境变量管理

---

## 三、项目二：SEO矩阵后台系统（新建，核心协作）

### 3.1 前端开发 → Trae 负责
```
seo-admin/               # Vue 3 + Element Plus 管理后台
├── src/
│   ├── pages/          # 10个功能页面（Dashboard/Settings/Regions/Keywords/Templates/Articles/Platforms/PublishTasks/Monitoring/Logs）
│   ├── layouts/        # 主布局组件
│   ├── components/     # 业务组件
│   ├── api/            # Axios接口封装
│   ├── stores/         # Pinia状态管理
│   └── router/         # 路由配置
├── vite.config.js
└── package.json
```

### 3.2 后端开发 → Lingma 负责
```
seo-backend/             # Node.js + Express + MySQL
├── src/
│   ├── app.js          # Express应用入口
│   ├── config/         # 数据库/Redis配置
│   ├── controllers/    # 业务控制器（需完善）
│   ├── models/         # Sequelize数据模型
│   ├── routes/         # API路由（框架已有）
│   ├── middleware/     # JWT认证/错误处理
│   ├── services/       # 业务服务层（需新建）
│   ├── tasks/          # BullMQ任务队列（需新建）
│   └── utils/          # 工具函数
├── database/
│   └── schema.sql     # MySQL数据库Schema（19张表）
└── package.json
```

---

## 四、SEO矩阵后台详细分工

### 4.1 Trae 前端任务清单

| 优先级 | 模块 | 任务描述 | 状态 |
|--------|------|----------|------|
| P0 | 登录页 | 表单验证、记住登录、JWT存储 | ✅已完成框架 |
| P0 | 主布局 | 侧边栏导航、顶栏用户信息、退出功能 | ✅已完成框架 |
| P0 | 数据看板 | ECharts图表、统计卡片、实时刷新 | 🟡需完善 |
| P1 | 地域词库 | 树形表格、批量导入导出、搜索过滤 | 🟡需完善 |
| P1 | 关键词管理 | 行业关键词列表、AI组词Tab | 🟡需完善 |
| P1 | 模板管理 | 模板列表、编辑、新增功能 | 🟡需完善 |
| P1 | 文章管理 | 文章列表、状态筛选、批量发布 | 🟡需完善 |
| P1 | 平台管理 | 平台列表、账号绑定弹窗 | 🟡需完善 |
| P1 | 发布任务 | 任务列表、状态标签、重试按钮 | 🟡需完善 |
| P1 | 收录监控 | 收录检测Tab、异常预警Tab | 🟡需完善 |
| P1 | 系统日志 | 操作日志、登录日志Tab切换 | 🟡需完善 |
| P2 | 系统设置 | 4个Tab配置表单保存功能 | 🟡需完善 |

### 4.2 Lingma 后端任务清单

| 优先级 | 模块 | 任务描述 | 状态 |
|--------|------|----------|------|
| P0 | 认证接口 | 登录/刷新令牌/登出/密码修改 | ✅已完成 |
| P0 | 地域管理 | CRUD接口、省市区树形结构 | 🟡需完善 |
| P0 | 配置管理 | 读取/更新各分组配置 | 🟡需完善 |
| P0 | 数据看板 | 统计数据接口、趋势数据接口 | 🟡需完善 |
| P1 | 关键词管理 | CRUD接口、AI组词生成接口 | 🟡需新建 |
| P1 | 模板管理 | CRUD接口 | 🟡需新建 |
| P1 | 文章管理 | CRUD接口、批量生成接口 | 🟡需新建 |
| P1 | 平台管理 | CRUD接口、账号管理接口 | 🟡需新建 |
| P1 | 发布任务 | 创建任务、查询列表、重试接口 | 🟡需新建 |
| P1 | 收录监控 | 收录检测、异常预警接口 | 🟡需新建 |
| P1 | 日志管理 | 操作日志、登录日志接口 | 🟡需新建 |
| P2 | AI生成服务 | 调用AI接口生成文案 | 🟡需新建 |
| P2 | 多平台分发 | 各平台API适配器 | 🟡需新建 |
| P2 | 任务队列 | BullMQ异步任务配置 | 🟡需新建 |

---

## 五、接口契约（双方共同遵守）

### 5.1 基础规范
- Base URL: `/api/v1`
- 认证方式: `Bearer JWT Token`
- 请求格式: `Content-Type: application/json`
- 分页格式: `?page=1&pageSize=20`

### 5.2 响应格式
```javascript
// 成功
{ code: 200, message: "success", data: T }

// 分页
{ code: 200, message: "success", data: { list: T[], total: number, page: number, pageSize: number } }

// 错误
{ code: number, message: string }
```

### 5.3 错误码
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权/Token过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 六、数据库规范（双方共同遵守）

### 6.1 MySQL配置（seo-backend）
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=seo_matrix_db
DB_USER=root
DB_PASSWORD=your-password
```

### 6.2 核心表结构（已定义19张表）
- `admin_users` - 管理员
- `regions` - 地域词库
- `industry_keywords` - 行业关键词
- `article_templates` - 文章模板
- `generated_articles` - 生成文章
- `platform_accounts` - 平台账号
- `publish_tasks` - 发布任务
- `indexing_records` - 收录记录
- `system_alerts` - 系统预警
- `operation_logs` - 操作日志
- `login_logs` - 登录日志

详细Schema见: `seo-backend/database/schema.sql`

---

## 七、开发规范

### 7.1 Trae 前端规范
- Vue 3 Composition API
- Element Plus 组件
- Pinia 状态管理
- SCSS 样式
- 移动端自适应

### 7.2 Lingma 后端规范
- Node.js 18+
- Express 4.x
- Sequelize ORM
- MySQL 8.0
- JWT (jsonwebtoken)
- 密码加密 (bcryptjs)

### 7.3 代码风格
- 变量命名: 驼峰命名
- 文件命名: 英文小写+下划线
- 缩进: 2空格
- 注释: 中文注释

---

## 八、协作流程

1. **需求确认**: 用户提出需求 → Trae拆分任务 → 分配给对应智能体
2. **开发执行**: Trae负责前端、Lingma负责后端，并行开发
3. **接口联调**: 后端先完成接口定义 → 前端对接调试
4. **集成测试**: 双方共同验证功能完整性
5. **Bug修复**: 谁引入谁修复，双方互助

---

## 九、文件权限约定

| 目录/文件 | Trae权限 | Lingma权限 |
|-----------|----------|------------|
| `seo-admin/` | ✅ 完全控制 | ❌ 只读 |
| `seo-backend/` | ❌ 只读 | ✅ 完全控制 |
| `frontend/` | ✅ 完全控制 | ❌ 只读 |
| `backend/` | ❌ 只读 | ✅ 完全控制 |
| `database/` | ⚠️ 需协商 | ⚠️ 需协商 |
| `prompt_lib/` | ✅ 完全控制 | ❌ 只读 |

---

## 十、沟通机制

- 本项目通过 Trae IDE 进行协作
- Lingma 开发完成后通知 Trae 进行联调
- 遇到冲突由用户（超级架构指挥官）仲裁
