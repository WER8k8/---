# 全国县域建材SEO矩阵AI全自动后台系统

## 项目概述

本系统是一个面向商用级别的SEO矩阵全自动后台管理系统，覆盖全国2800+县/区，实现AI全自动生成文案、多平台分发、收录监控的完整闭环。

## 技术栈

| 层级 | 技术方案 |
|------|----------|
| 前端 | Vue 3 + Element Plus + Pinia + Vue Router |
| 后端 | Node.js (LTS) + Express + Sequelize |
| 数据库 | MySQL 8.0+ |
| 任务队列 | BullMQ + Redis |
| AI能力 | OpenAI API / 内置大模型 |
| 部署 | Docker + Docker Compose |

## 快速启动

### 1. 环境要求

- Node.js >= 18.0.0
- MySQL 8.0+
- Redis 6.0+

### 2. 后端启动

```bash
# 进入后端目录
cd seo-backend

# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，填入数据库配置
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=your-password
# JWT_SECRET=your-secret-key

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

后端默认运行在 `http://localhost:3000`

### 3. 前端启动

```bash
# 进入前端目录
cd seo-admin

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端默认运行在 `http://localhost:5173`

### 4. 数据库初始化

```bash
# 登录MySQL
mysql -u root -p

# 执行Schema脚本
source seo-backend/database/schema.sql
```

### 5. 默认账号

- 用户名：`admin`
- 密码：`Trae@2024`
- **首次登录后请立即修改密码**

## 系统功能模块

### 1. 系统全局设置
- 品牌信息配置
- 外链规则设置
- AI生成参数配置
- 发布风控规则

### 2. 全国地域词库管理
- 2800+县域完整入库
- 省-市-县三级结构
- 批量导入/导出
- AI自动去重纠错

### 3. 行业关键词库与AI组词
- 内置建材行业词库
- AI智能生成长尾词
- 一键生成5-10万条关键词
- 自动去重过滤

### 4. AI文案模板与全自动生成
- 多套SEO高转化模板
- 全局变量自动替换
- 伪原创（重复率≤10%）
- 合规检测与极限词过滤

### 5. 多平台账号管理与AI分发
- 支持百度系、阿里系、腾讯系、字节系等平台
- OAuth授权/Cookie持久化
- 防风控三重机制
- 失败自动重试3次

### 6. 发布记录、数据看板与收录监控
- 全量发布日志
- 可视化数据看板
- 百度收录自动检测
- 异常预警

## 项目结构

```
seo-backend/                    # Node.js后端
├── src/
│   ├── app.js                  # 应用入口
│   ├── config/                 # 配置文件
│   │   └── database.js         # 数据库配置
│   ├── controllers/            # 控制器
│   │   └── auth.controller.js  # 认证控制器
│   ├── middleware/             # 中间件
│   │   ├── auth.js             # 认证中间件
│   │   └── errorHandler.js     # 错误处理
│   ├── models/                 # 数据模型
│   │   └── AdminUser.js        # 管理员模型
│   ├── routes/                 # 路由
│   │   ├── auth.routes.js      # 认证路由
│   │   ├── config.routes.js    # 配置路由
│   │   ├── region.routes.js    # 地域路由
│   │   └── ...
│   ├── services/               # 业务服务
│   ├── tasks/                  # 定时任务
│   └── utils/                  # 工具函数
│       └── logger.js           # 日志工具
├── database/
│   └── schema.sql              # 数据库Schema
├── docs/
│   └── API_CONTRACT.md         # API接口契约
├── .env.example                # 环境变量模板
└── package.json

seo-admin/                      # Vue3前端
├── src/
│   ├── main.js                 # 应用入口
│   ├── App.vue                 # 根组件
│   ├── api/                    # API接口
│   │   └── index.js            # Axios配置
│   ├── assets/                 # 静态资源
│   ├── components/             # 组件
│   ├── layouts/                # 布局
│   │   └── MainLayout.vue      # 主布局
│   ├── pages/                  # 页面
│   │   ├── Login.vue           # 登录页
│   │   ├── Dashboard.vue       # 数据看板
│   │   ├── Settings.vue        # 系统设置
│   │   └── ...
│   ├── router/                 # 路由
│   │   └── index.js
│   ├── stores/                 # Pinia状态管理
│   │   └── user.js             # 用户状态
│   └── styles/                 # 样式
│       └── global.scss
├── index.html
├── vite.config.js
└── package.json
```

## API接口文档

详见 [API_CONTRACT.md](seo-backend/docs/API_CONTRACT.md)

## 部署说明

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 生产环境配置

1. 修改 `.env` 文件中的数据库连接信息
2. 修改 JWT_SECRET 为强随机密钥
3. 配置 Redis 连接信息
4. 配置 AI API Key

## 验收标准

- [x] 系统可正常启动运行
- [x] 管理员可登录
- [x] 6大功能模块页面可访问
- [x] API接口正常响应
- [x] 数据库表结构完整
- [x] 前端路由正常跳转

## 注意事项

1. 本系统与现有官网系统（Nuxt 3 + FastAPI + PostgreSQL）独立运行
2. 两个系统通过API进行数据交换
3. 本系统专注于SEO矩阵全自动后台管理
4. 官网系统专注于前端展示和SEO优化
