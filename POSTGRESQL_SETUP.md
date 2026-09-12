# PostgreSQL 数据库配置说明

## ✅ 已完成配置

### 1. PostgreSQL 安装
- **版本**: PostgreSQL 17.9
- **安装路径**: `C:\Program Files\PostgreSQL\17`
- **服务状态**: 已启动（自动启动）
- **端口**: 5432

### 2. 数据库配置
- **数据库名**: `youding_seo`
- **用户名**: `youding`
- **密码**: `youding123`
- **连接字符串**: `postgresql://youding:youding123@localhost:5432/youding_seo`

### 3. MCP Server postgres 配置
- **状态**: ✅ 正常运行
- **测试命令**: 
  ```powershell
  mcp-server-postgres "postgresql://youding:youding123@localhost:5432/youding_seo"
  ```

### 4. 项目环境配置
已更新以下文件的数据库配置：
- `.env`
- `backend/.env`

从 SQLite 切换到 PostgreSQL，配置如下：
```env
DATABASE_URL=postgresql://youding:youding123@localhost:5432/youding_seo
DB_TYPE=postgresql
```

## 🔧 常用管理命令

### 启动/停止 PostgreSQL 服务
```powershell
# 启动服务
Start-Service postgresql-x64-17

# 停止服务
Stop-Service postgresql-x64-17

# 重启服务
Restart-Service postgresql-x64-17

# 查看服务状态
Get-Service postgresql-x64-17
```

### 连接数据库
```powershell
# 使用 psql 命令行工具
$env:PGPASSWORD="youding123"; & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U youding -d youding_seo

# 或使用 postgres 超级用户
$env:PGPASSWORD="postgres"; & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
```

### 查看数据库表
```powershell
$env:PGPASSWORD="youding123"; & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U youding -d youding_seo -c "\dt"
```

### 备份数据库
```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U youding -d youding_seo -f backup.sql
```

### 恢复数据库
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U youding -d youding_seo -f backup.sql
```

## 📊 数据库管理工具推荐

### 1. pgAdmin 4（已随 PostgreSQL 安装）
- 访问地址: http://localhost:5432
- 或通过开始菜单启动 pgAdmin 4

### 2. DBeaver（免费开源）
- 下载地址: https://dbeaver.io/
- 支持多种数据库，界面友好

### 3. DataGrip（JetBrains，付费）
- 功能强大，适合专业开发

## ⚠️ 注意事项

1. **防火墙设置**: 如果需要远程访问，需要在 Windows 防火墙中开放 5432 端口
2. **密码安全**: 生产环境请修改默认密码
3. **数据备份**: 建议定期备份数据库
4. **性能优化**: 可根据实际需求调整 PostgreSQL 配置参数

## 🚀 下一步操作

1. 启动后端服务验证数据库连接
2. 运行数据库迁移（如果需要）
3. 导入初始数据（如果需要）

## 📞 故障排查

### 问题 1: 无法连接数据库
```powershell
# 检查服务是否运行
Get-Service postgresql-x64-17

# 检查端口是否监听
netstat -ano | Select-String "5432"
```

### 问题 2: 认证失败
- 确认用户名和密码正确
- 检查 `pg_hba.conf` 配置文件（位于 `C:\Program Files\PostgreSQL\17\data`）

### 问题 3: MCP Server 连接超时
- 确认 PostgreSQL 服务正在运行
- 检查连接字符串格式是否正确
- 验证防火墙设置

---

**配置完成时间**: 2026-05-02
**配置状态**: ✅ 全部完成
