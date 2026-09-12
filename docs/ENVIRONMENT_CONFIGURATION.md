# 环境配置与源代码分离规范

## 概述

本项目采用**配置与代码分离**的架构设计，确保：
- 敏感配置信息不随代码版本控制
- 多环境配置独立管理
- 配置变更无需修改源代码
- 生产环境配置安全隔离

---

## 项目目录结构

```
backend/
├── app/                    # 源代码目录（提交到版本控制）
│   ├── api/               # API路由
│   ├── core/              # 核心模块（含config.py）
│   ├── services/          # 业务服务
│   └── main.py            # 应用入口
├── config/                # 环境配置目录（敏感文件不提交）
│   ├── dev/               # 开发环境配置
│   │   ├── .env           # 开发环境变量（不提交）
│   │   └── .env.example   # 开发环境配置示例（提交）
│   ├── test/              # 测试环境配置
│   │   └── .env           # 测试环境变量（不提交）
│   └── prod/              # 生产环境配置
│       ├── .env           # 生产环境变量（不提交）
│       └── .env.example   # 生产环境配置示例（提交）
├── run.py                 # 启动脚本（支持多环境参数）
├── start-dev.ps1          # 开发环境启动脚本
├── start-test.ps1         # 测试环境启动脚本
└── start-prod.ps1         # 生产环境启动脚本
```

---

## 目录职责说明

| 目录/文件 | 职责 | 是否提交版本控制 |
|-----------|------|----------------|
| `backend/app/` | 应用源代码 | ✅ 是 |
| `backend/config/` | 环境配置目录 | ⚠️ 部分 |
| `backend/config/*/.env` | 实际环境配置（含敏感信息） | ❌ 否 |
| `backend/config/*/.env.example` | 配置示例文件 | ✅ 是 |
| `backend/run.py` | 启动脚本 | ✅ 是 |
| `backend/start-*.ps1` | 环境启动脚本 | ✅ 是 |

---

## 配置加载机制

### 配置优先级（从高到低）

1. **命令行参数**：通过 `--port`, `--host` 传入
2. **系统环境变量**：运行时设置的环境变量
3. **环境配置文件**：`config/{env}/.env`
4. **示例配置文件**：`config/{env}/.env.example`（备用）
5. **代码默认值**：`app/core/config.py` 中定义的默认值

### 动态加载流程

```
用户启动命令
    │
    ▼
run.py 解析 --env 参数
    │
    ▼
加载 config/{env}/.env 文件
    │
    ▼
设置系统环境变量
    │
    ▼
初始化 Settings 类
    │
    ▼
应用使用配置
```

---

## 启动方式

### 方式一：使用启动脚本（推荐）

```powershell
# 开发环境
.\start-dev.ps1

# 指定端口
.\start-dev.ps1 -Port 8080

# 测试环境
.\start-test.ps1

# 生产环境
.\start-prod.ps1
```

### 方式二：直接运行

```powershell
# 开发环境（默认）
python run.py

# 指定环境和端口
python run.py --env dev --port 8080

# 测试环境
python run.py --env test --port 8081

# 生产环境
python run.py --env prod --port 8000
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--env` | string | dev | 运行环境：dev/test/prod |
| `--port` | int | 8000 | 服务端口 |
| `--host` | string | 0.0.0.0 | 绑定地址 |

---

## 环境配置文件格式

### 通用配置项

```env
# 基础配置
ENVIRONMENT=development
DEBUG=true
PORT=8000
HOST=0.0.0.0

# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/dbname
SQLITE_PATH=./youding_dev.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-32-char-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 安全配置
SECRET_KEY=your-32-char-secret-key
ALLOWED_HOSTS=["localhost","127.0.0.1"]
```

### 各环境配置差异

| 配置项 | 开发环境 | 测试环境 | 生产环境 |
|--------|---------|---------|---------|
| DEBUG | true | false | false |
| LOG_LEVEL | DEBUG | INFO | WARNING |
| JWT_EXPIRE | 60分钟 | 30分钟 | 15分钟 |
| RATE_LIMIT | 500 | 200 | 100 |

---

## 敏感配置管理

### 安全原则

1. **绝对禁止**在代码中硬编码敏感信息
2. **绝对禁止**将 `.env` 文件提交到版本控制
3. **生产环境**敏感配置应通过环境变量注入
4. **密钥长度**必须 ≥ 32 位随机字符串

### 生成强密钥

```powershell
# 生成32位随机密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 生成JWT密钥
python -c "import secrets; print(secrets.token_hex(32))"
```

### 生产环境配置建议

生产环境应使用以下方式注入敏感配置：

```powershell
# Linux/macOS
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export DB_PASSWORD=your-db-password
python run.py --env prod

# Windows PowerShell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:DB_PASSWORD = "your-db-password"
python run.py --env prod
```

---

## 配置维护流程

### 添加新配置项

1. 在 `app/core/config.py` 中定义配置字段和默认值
2. 在各环境 `.env.example` 文件中添加配置项说明
3. 开发者在本地 `.env` 文件中设置实际值
4. 提交 `config.py` 和 `.env.example` 到版本控制

### 修改配置项

1. 修改 `app/core/config.py` 中的默认值（如需）
2. 更新各环境 `.env.example` 文件
3. 通知团队成员更新本地 `.env` 文件

### 配置文件模板同步

```powershell
# 将示例配置复制为实际配置
Copy-Item config/dev/.env.example config/dev/.env

# 编辑配置
notepad config/dev/.env
```

---

## 验证配置分离

### 测试步骤

1. **启动开发环境**
   ```powershell
   .\start-dev.ps1
   # 验证配置加载：检查日志中显示 "已加载 dev 环境配置"
   ```

2. **启动测试环境**
   ```powershell
   .\start-test.ps1
   # 验证配置加载：检查日志中显示 "已加载 test 环境配置"
   ```

3. **验证配置隔离**
   - 修改 `config/dev/.env` 中的配置
   - 重启开发环境，确认配置生效
   - 测试环境不受影响

### 预期结果

| 环境 | 端口 | 调试模式 | 配置文件 |
|------|------|---------|---------|
| dev | 8080 | ✅ 开启 | config/dev/.env |
| test | 8081 | ❌ 关闭 | config/test/.env |
| prod | 8000 | ❌ 关闭 | config/prod/.env |

---

## 故障排除

### 配置加载失败

```powershell
# 检查配置文件是否存在
Test-Path config/dev/.env

# 检查文件格式是否正确
Get-Content config/dev/.env | Select-Object -First 10

# 手动验证环境变量
$env:ENVIRONMENT
$env:DATABASE_URL
```

### 敏感配置错误

生产环境启动时如果配置包含弱密码模式，会抛出安全错误：

```
ValueError: [安全错误] 生产环境 JWT_SECRET_KEY 包含弱密码模式 'change-me'。
请立即更换为强随机值。
```

**解决方案**：生成强随机密钥并更新配置。

---

## 最佳实践

1. **.gitignore 维护**：定期检查 `.gitignore` 确保敏感文件被正确排除
2. **配置备份**：生产环境配置应妥善备份，建议使用密钥管理服务
3. **配置审计**：定期审计配置文件，移除不再使用的配置项
4. **文档更新**：配置项变更时同步更新本文档

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0 | 2026-05-30 | 初始版本，实现多环境配置分离 |