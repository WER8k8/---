# MCP 配置管理工具 - 快速开始指南

## 🚀 立即使用

### 1. 查看当前状态

```powershell
cd "c:\Users\97907\Desktop\UJ\wang  zhan\scripts"
.\mcp-config-manager.ps1 -Action Status
```

### 2. 列出所有配置的 Servers

```powershell
.\mcp-config-manager.ps1 -Action List
```

### 3. 添加新的 MCP Server

**示例: 添加 GitLab**

```powershell
$gitlabConfig = '{"command":"npx","args":["-y","@modelcontextprotocol/server-gitlab"],"env":{"GITLAB_PERSONAL_ACCESS_TOKEN":"","GITLAB_API_URL":"https://gitlab.com/api/v4"}}'
.\mcp-config-manager.ps1 -Action Add -ServerName gitlab -Config $gitlabConfig
```

**示例: 添加 Redis**

```powershell
$redisConfig = '{"command":"npx","args":["-y","@modelcontextprotocol/server-redis"],"env":{"REDIS_URL":"redis://localhost:6379"}}'
.\mcp-config-manager.ps1 -Action Add -ServerName redis -Config $redisConfig
```

### 4. 删除 MCP Server

```powershell
.\mcp-config-manager.ps1 -Action Remove -ServerName gitlab
```

### 5. 创建备份

```powershell
.\mcp-config-manager.ps1 -Action Backup
```

## 📋 常用 MCP Server 配置模板

### GitHub

```powershell
$config = '{"command":"npx","args":["-y","@modelcontextprotocol/server-github"],"env":{"GITHUB_TOKEN":""}}'
.\mcp-config-manager.ps1 -Action Add -ServerName github -Config $config
```

### GitLab

```powershell
$config = '{"command":"npx","args":["-y","@modelcontextprotocol/server-gitlab"],"env":{"GITLAB_PERSONAL_ACCESS_TOKEN":"","GITLAB_API_URL":"https://gitlab.com/api/v4"}}'
.\mcp-config-manager.ps1 -Action Add -ServerName gitlab -Config $config
```

### Slack

```powershell
$config = '{"command":"npx","args":["-y","@modelcontextprotocol/server-slack"],"env":{"SLACK_BOT_TOKEN":"","SLACK_TEAM_ID":""}}'
.\mcp-config-manager.ps1 -Action Add -ServerName slack -Config $config
```

### Docker

```powershell
$config = '{"command":"npx","args":["-y","@modelcontextprotocol/server-docker"]}'
.\mcp-config-manager.ps1 -Action Add -ServerName docker -Config $config
```

### PostgreSQL

```powershell
$config = '{"command":"npx","args":["-y","@modelcontextprotocol/server-postgres"],"env":{"POSTGRES_CONNECTION_STRING":"postgresql://user:pass@localhost:5432/dbname"}}'
.\mcp-config-manager.ps1 -Action Add -ServerName postgres-mcp -Config $config
```

## 🔧 高级用法

### 强制覆盖已存在的配置

```powershell
.\mcp-config-manager.ps1 -Action Add -ServerName github -Config $config -Force
```

### 批量添加多个 Servers

创建脚本 `add-all-servers.ps1`:

```powershell
$servers = @{
    github = '{"command":"npx","args":["-y","@modelcontextprotocol/server-github"],"env":{"GITHUB_TOKEN":""}}'
    gitlab = '{"command":"npx","args":["-y","@modelcontextprotocol/server-gitlab"],"env":{"GITLAB_PERSONAL_ACCESS_TOKEN":"","GITLAB_API_URL":"https://gitlab.com/api/v4"}}'
    docker = '{"command":"npx","args":["-y","@modelcontextprotocol/server-docker"]}'
}

foreach ($name in $servers.Keys) {
    Write-Host "Adding $name..."
    .\mcp-config-manager.ps1 -Action Add -ServerName $name -Config $servers[$name] -Force
}
```

执行:

```powershell
.\add-all-servers.ps1
```

## 📁 文件位置

- **配置文件**: `%APPDATA%\Lingma\SharedClientCache\mcp.json`
- **备份目录**: `%APPDATA%\Lingma\SharedClientCache\mcp-backups\`
- **日志文件**: `%TEMP%\mcp-config-manager.log`

## ⚠️ 注意事项

1. **重启 Lingma**: 每次修改配置后,必须重启 Lingma 才能生效
2. **Token 安全**: 不要将包含 Token 的配置文件提交到 Git
3. **自动备份**: 每次修改都会自动创建备份,保留最近 10 个
4. **验证配置**: 修改前建议先查看当前状态

## 🆘 故障排除

### 问题: 配置后 Lingma 无法启动

**解决方案:**
1. 恢复最近的备份
2. 检查配置语法

```powershell
# 查看备份列表
Get-ChildItem "$env:APPDATA\Lingma\SharedClientCache\mcp-backups\" | Sort-Object LastWriteTime -Descending

# 恢复备份(替换为实际文件名)
Copy-Item "$env:APPDATA\Lingma\SharedClientCache\mcp-backups\mcp-backup-20260504-120000.json" "$env:APPDATA\Lingma\SharedClientCache\mcp.json" -Force
```

### 问题: 提示 JSON 格式错误

**解决方案:**
使用在线 JSON 验证工具检查配置字符串,或手动编辑配置文件。

### 问题: Server 无法正常工作

**解决方案:**
1. 检查是否安装了相应的 npm 包
2. 检查环境变量是否正确配置
3. 查看 Lingma 日志文件

```powershell
# 检查 npm 包
npm list -g @modelcontextprotocol/server-github

# 安装缺失的包
npm install -g @modelcontextprotocol/server-github
```

## 📊 当前配置状态

运行以下命令查看完整状态:

```powershell
.\mcp-config-manager.ps1 -Action Status
```

输出示例:

```
========================================
  MCP Configuration Status
========================================

Config File: C:\Users\xxx\AppData\Roaming\Lingma\SharedClientCache\mcp.json
Status: EXISTS
Size: 2356 bytes
Modified: 05/04/2026 05:00:10

Backup Directory: C:\Users\xxx\AppData\Roaming\Lingma\SharedClientCache\mcp-backups
Status: EXISTS (3 backups)

Configured Servers: 7

[详细列表...]
```

## 🎯 下一步

1. ✅ 配置已完成,重启 Lingma
2. 📝 根据需要配置各 Server 的环境变量(Token等)
3. 🧪 测试各个 MCP Server 功能
4. 📖 阅读完整文档: `MCP_CONFIG_README.md`

---

*最后更新: 2026-05-04*
*版本: 1.0.0*
