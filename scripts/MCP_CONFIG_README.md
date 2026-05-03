# MCP Server 配置管理工具

> 超级架构指挥官 · MCP 自动化配置管理系统 v1.0.0

## 📋 概述

本工具集提供完整的 MCP (Model Context Protocol) Server 配置管理能力,包括:
- ✅ 自动化添加/删除/更新 MCP Servers
- ✅ 配置验证与备份
- ✅ 快速批量配置
- ✅ 状态监控与报告

## 🛠️ 工具列表

### 1. mcp-config-manager.ps1 - 核心管理器

功能完整的 MCP 配置管理工具,支持所有操作。

**用法示例:**

```powershell
# 查看当前状态
.\mcp-config-manager.ps1 -Action Status

# 列出所有配置的 Servers
.\mcp-config-manager.ps1 -Action List

# 添加 GitHub MCP Server
.\mcp-config-manager.ps1 -Action Add -ServerName github -Config '{"command":"npx","args":["-y","@modelcontextprotocol/server-github"],"env":{"GITHUB_TOKEN":""}}'

# 删除某个 Server
.\mcp-config-manager.ps1 -Action Remove -ServerName github

# 验证配置
.\mcp-config-manager.ps1 -Action Validate

# 创建备份
.\mcp-config-manager.ps1 -Action Backup

# 强制覆盖已存在的配置
.\mcp-config-manager.ps1 -Action Add -ServerName github -Config '...' -Force
```

**参数说明:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `-Action` | string | 是 | 操作类型: Add, Remove, List, Validate, Backup, Status |
| `-ServerName` | string | 条件 | Server 名称(Add/Remove 时必填) |
| `-Config` | string | 条件 | JSON 配置字符串(Add 时必填) |
| `-Force` | switch | 否 | 强制覆盖已存在的配置 |

### 2. mcp-quick-setup.ps1 - 快速配置工具

一键添加常用 MCP Servers,内置配置模板。

**用法示例:**

```powershell
# 配置所有可用 Servers
.\mcp-quick-setup.ps1 -Server all

# 仅配置 GitHub
.\mcp-quick-setup.ps1 -Server github

# 强制覆盖已有配置
.\mcp-quick-setup.ps1 -Server all -Force
```

**支持的 Server 类型:**

| Server | 描述 | 所需环境变量 |
|--------|------|-------------|
| `github` | GitHub API 集成 | GITHUB_TOKEN |
| `gitlab` | GitLab API 集成 | GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_API_URL |
| `slack` | Slack 机器人集成 | SLACK_BOT_TOKEN, SLACK_TEAM_ID |
| `redis` | Redis 数据库 | REDIS_URL |
| `docker` | Docker 容器管理 | 无 |

## 📁 文件结构

```
scripts/
├── mcp-config-manager.ps1    # 核心管理器
├── mcp-quick-setup.ps1       # 快速配置工具
└── README.md                  # 本文档

配置文件位置:
%APPDATA%\Lingma\SharedClientCache\mcp.json

备份目录:
%APPDATA%\Lingma\SharedClientCache\mcp-backups/
```

## 🔧 配置示例

### GitHub MCP Server

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx"
    }
  }
}
```

**获取 Token:**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限: `repo`, `read:user`
4. 生成并复制 Token

### GitLab MCP Server

```json
{
  "gitlab": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-gitlab"],
    "env": {
      "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat-xxxxxxxxxxxx",
      "GITLAB_API_URL": "https://gitlab.com/api/v4"
    }
  }
}
```

### Slack MCP Server

```json
{
  "slack": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "xoxb-xxxxxxxxxxxx",
      "SLACK_TEAM_ID": "T01234567"
    }
  }
}
```

## 🔄 工作流程

### 添加新 MCP Server

```mermaid
graph LR
    A[准备配置] --> B[执行 Add 命令]
    B --> C[自动备份]
    C --> D[验证配置]
    D --> E[保存配置]
    E --> F[重启 Lingma]
```

### 配置验证流程

1. **结构检查**: 确保 `mcpServers` 节点存在
2. **必需字段**: 每个 Server 必须有 `command` 或 `url`
3. **格式验证**: 检查 `env`, `args` 等字段格式
4. **JSON 有效性**: 确保配置文件是有效的 JSON

## 💾 备份与恢复

### 自动备份

每次修改配置时,系统会自动创建备份:
- 备份位置: `%APPDATA%\Lingma\SharedClientCache\mcp-backups/`
- 命名格式: `mcp-backup-YYYYMMDD-HHMMSS.json`
- 保留策略: 自动保留最近 10 个备份

### 手动备份

```powershell
.\mcp-config-manager.ps1 -Action Backup
```

### 恢复配置

手动从备份目录复制需要的备份文件,替换主配置文件:

```powershell
Copy-Item "$env:APPDATA\Lingma\SharedClientCache\mcp-backups\mcp-backup-20260504-120000.json" "$env:APPDATA\Lingma\SharedClientCache\mcp.json" -Force
```

## 🛡️ 安全建议

1. **Token 管理**
   - 不要将包含 Token 的配置文件提交到 Git
   - 使用 `.gitignore` 排除 `mcp.json`
   - 定期轮换 Token

2. **权限最小化**
   - 为每个 Token 分配最小必要权限
   - 避免使用全权限 Token

3. **备份保护**
   - 备份文件同样包含敏感信息
   - 确保备份目录有适当的访问控制

## 📊 状态监控

查看当前配置状态:

```powershell
.\mcp-config-manager.ps1 -Action Status
```

输出示例:

```
========================================
  MCP 配置管理器 - 状态报告
========================================

配置文件: C:\Users\xxx\AppData\Roaming\Lingma\SharedClientCache\mcp.json
状态: ✅ 存在
大小: 1234 bytes
最后修改: 2026-05-04 12:00:00

备份目录: C:\Users\xxx\AppData\Roaming\Lingma\SharedClientCache\mcp-backups
状态: ✅ 存在 (5 个备份)

已配置 Servers: 7 个

========================================
  MCP Servers 配置列表
========================================

总计: 7 个 Server

[1] supabase
    类型: Command
    命令: mcp-server-supabase

[2] github
    类型: Command
    命令: npx
    参数: -y @modelcontextprotocol/server-github
    环境变量: GITHUB_TOKEN

...

========================================
```

## ❓ 常见问题

### Q: 如何知道某个 MCP Server 是否已安装?

A: 使用 npm 全局查询:
```powershell
npm list -g @modelcontextprotocol/server-github
```

### Q: 配置后 Lingma 无法启动?

A: 
1. 检查配置文件语法: `.\mcp-config-manager.ps1 -Action Validate`
2. 恢复最近的备份
3. 检查日志: `%TEMP%\mcp-config-manager.log`

### Q: 如何卸载某个 MCP Server?

A: 
1. 从配置中删除: `.\mcp-config-manager.ps1 -Action Remove -ServerName github`
2. 如需完全卸载 npm 包: `npm uninstall -g @modelcontextprotocol/server-github`

### Q: 备份文件太多怎么办?

A: 系统会自动保留最近 10 个备份,无需手动清理。

## 📝 更新日志

### v1.0.0 (2026-05-04)
- ✨ 初始版本发布
- ✅ 实现核心管理功能
- ✅ 添加快速配置工具
- ✅ 支持自动备份与恢复
- ✅ 完整的配置验证机制

## 🤝 贡献

如有问题或建议,请联系超级架构指挥官。

---

*本工具由超级架构指挥官开发,遵循 15S 管理规则*
*最后更新: 2026-05-04*

