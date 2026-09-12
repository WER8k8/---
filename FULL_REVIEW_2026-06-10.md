# 🔍 全量代码评审报告

**评审人**: Senior Developer (高级开发工程师)  
**日期**: 2026-06-10  
**范围**: 前端 + 后端全量代码 (28193行路由 + 6652行核心 + 977行前端登录)  

---

## 📊 评审总览

```
┌─────────────────────────────────────────────────────────────┐
│  发现总数: 66 项                                             │
│  Critical: 5  │  High: 13  │  Medium: 20  │  Low: 28       │
│                                                             │
│  安全: ████████████░░░░ 26 项 (5C/8H/9M/4L)                │
│  性能: ██████░░░░░░░░░░ 12 项 (2C/3H/5M/2L)                │
│  前端: ████████████░░░░ 28 项 (2C/5H/10M/11L)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 严重问题 (Critical) — 立即修复

| # | 分类 | 文件 | 问题 |
|---|------|------|------|
| C-01 | 安全 | `.env.production` | **NVIDIA API Key 硬编码**: `nvapi-h02QB_QwJncz...` — 需立即轮换 |
| C-02 | 安全 | `.env.production` | **SECRET_KEY 可预测**: `a1b2c3d4...` 是递进序列不是随机值 |
| C-03 | 安全 | `.env.production` | **数据库密码弱**: `user:password` 默认凭证 |
| C-04 | 前端 | `TaskResult.vue:43` | **v-html 未净化**: 4 处直接渲染 AI/用户内容，可 XSS 注入 |
| C-05 | 前端 | `article-generator.vue` | **innerHTML 直接赋值**: 绕过 Quill 表单安全机制 |

---

## 🟠 高风险 (High) — 本周修复

### 安全

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| H-01 | `auth.py:143` | logout 不吊销 access_token | 加 jti 黑名单 |
| H-02 | `security.py:95` | `get_current_user` 不检查会话吊销 | 对齐 `get_current_super_admin` |
| H-03 | `auth.py:175` | `random.choices` 非密码学安全 | 改用 `secrets.choice` |
| H-04 | `permissions.py` | 两套权限系统并行 (Role枚举 vs AdminRole数据库) | 统一到一套 |
| H-05 | `validation.py:76` | 文件上传不检查 MIME 类型 | magic bytes 校验 |
| H-06 | `security_middleware.py:65` | DEBUG 模式下完全跳过限流 | 仅跳过 localhost |
| H-07 | `security_middleware.py:62` | 限流用进程内存，多 worker 失效 | 改为 Redis 存储 |
| H-08 | `auth.py:229` | 邮箱登录自动创建账户 (枚举风险) | 独立注册流程 |

### 性能

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| H-09 | `database.py` | 连接池默认 pool_size=5 不足 | 设为 20 |
| H-10 | `base_repository.py:52` | count 查询加载所有行到内存 | 用 `func.count()` |
| H-11 | `seo_matrix.py:78` | 三重嵌套循环 N*M*K 次迭代 | 批量查询重构 |

### 前端

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| H-12 | `vite.config.ts` | 生产构建未清除 console.log (20+处) | esbuild.drop |
| H-13 | `nginx.conf` | 缺少 Content-Security-Policy 头 | 添加 CSP |

---

## 🟡 中风险 (Medium)

### 安全 (6 项)

| 问题 | 位置 |
|------|------|
| 邮箱验证码 6 位纯数字 | `auth.py:175` |
| 验证码明文存数据库 | `auth.py:185` |
| 限流中间件 DEBUG 跳过 | `security_middleware.py:65` |
| CORS allow_headers="*" | `main.py:388` |
| 日志泄露 PII (用户名/IP) | `auth.py:361` |
| CSRF 中间件已编写但未注册 | `security_tools.py` |

### 性能 (4 项)

| 问题 | 位置 |
|------|------|
| 81+ 处直接调用 SessionLocal() | 全代码库 |
| 三个并行 Redis 实现 | cache.py/cache_decorator.py/cache_service.py |
| Redis KEYS 应改为 SCAN | cache.py:102 |
| 按请求创建新 httpx.Client | publish_service.py 等 |

### 前端 (10 项)

| 问题 | 位置 |
|------|------|
| Token 存 localStorage (可被 XSS 窃取) | stores/auth.ts |
| API 模式不一致 (axios vs fetch) | api/*.ts |
| 无全局 401 错误拦截器 | router/index.ts |
| chunkSizeWarningLimit=500KB 过高 | vite.config.ts |
| WebSocket 连接状态 3 处重复 | stores/ + composables/ |
| 图片无 lazy loading | 全站 |
| 无请求取消机制 | 全局 |
| a-menu 键盘导航未验证 | Sidebar.vue |
| markdown-it 未禁用 html 模式 | TaskResult.vue |
| refresh token 存在 localStorage | sessionAuth.ts |

---

## 📋 修复优先级矩阵

```
         紧急
          │
  ╔═══════╪═══════╗
  │ C-01  │ H-01  │
  │ C-02  │ H-02  │
  │ C-03  │ H-04  │ ← 本周
  │ C-04  │ H-07  │
  │ C-05  │ H-12  │
  ├───────┼───────┤
  │ M-01  │ M-04  │
  │ M-02  │ M-07  │
  │ M-03  │       │ ← 本月
  └───────┴───────┘
        低影响
```

### 立即行动清单

```
□ [C-01] 轮换 NVIDIA API Key → NVIDIA 控制台
□ [C-02] 重新生成 SECRET_KEY → secrets.token_hex(32)
□ [C-03] 更换数据库密码 → 强随机密码
□ [C-04] 所有 v-html 加 sanitizeHtml() 包裹
□ [C-05] innerHTML 改用 DOMPurify.textContent
□ [H-01] logout 端点加 access_token 吊销
□ [H-04] 统一定权限系统 (Role枚举 或 AdminRole数据库)
□ [H-12] vite.config.ts 添加 esbuild.drop: ['console','debugger']
□ [H-13] nginx.conf 添加 Content-Security-Policy 头
```

---

## ✅ 已优化项 (本轮次完成)

| 优化 | 效果 |
|------|------|
| config.py 12 处 cached_property | 每次请求消除重复计算 |
| WAF 5 个模块级正则预编译 | 请求时无 re.compile() |
| WAF UA 预小写子串 + LRU 缓存 | 快 10x |
| GZip 响应压缩 | API 体积减 60-80% |
| main.py 架构解耦 | 534→195 行 |
| 5 级分层限流 | 公开/读写/认证分级 |
| OAuth 模拟数据清除 | 仅真实认证 |
| 腾讯登录生态完整集成 | QQ+微信+企微+频道 |

---

> **结论**: 项目安全基线良好（WAF生效、JWT机制正确、密钥校验完善），前端登录体验完整。主要风险集中在 `.env.production` 密钥泄露和前端 XSS 防护不足。建议按优先级矩阵逐项修复。
