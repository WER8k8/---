#Requires -Version 5.1
<#
.SYNOPSIS
  一键全局安装：CodeGraph + Hey AI README + Agency 184 + ECC 38 对话栈

.DESCRIPTION
  - 安装/升级 CodeGraph CLI 并配置 Cursor MCP（global + 本项目）
  - 初始化本项目 .codegraph/ 索引
  - 写入用户级 Cursor 规则（跨项目 fallback）
  - 验证 Agency/ECC/CodeGraph 状态

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/install-ai-stack-global.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$UserCursorRules = Join-Path $env:USERPROFILE ".cursor\rules"
$UserCursorMcp = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$ExternalInstaller = Join-Path $RepoRoot "scripts\install-dev-stack-external.ps1"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AI 全局栈安装：CodeGraph + Hey AI README + Agency + ECC" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  仓库: $RepoRoot"
Write-Host ""

# --- 1. CodeGraph CLI ---
Write-Host "[1/6] 安装 CodeGraph CLI..." -ForegroundColor Yellow
npm i -g @colbymchenry/codegraph@latest | Out-Host
$cg = Get-Command codegraph -ErrorAction SilentlyContinue
if (-not $cg) {
    throw "codegraph 未在 PATH 中。请重启终端或检查 npm global bin 路径。"
}
Write-Host "  OK: $($cg.Source)" -ForegroundColor Green

# --- 2. Cursor global MCP + instructions ---
Write-Host "[2/6] 配置 Cursor（global）..." -ForegroundColor Yellow
& codegraph install --target=cursor --location=global --yes
Write-Host "  OK: codegraph install (global)" -ForegroundColor Green

# --- 3. 开发工具栈隔离 + CodeGraph 本地索引（gitignore）---
Write-Host "[3/6] 开发工具栈外部化 + CodeGraph..." -ForegroundColor Yellow
if (Test-Path $ExternalInstaller) {
    & $ExternalInstaller -SkipCodegraph
} else {
    Write-Warning "Missing install-dev-stack-external.ps1 — 仅初始化 .codegraph"
}
Push-Location $RepoRoot
try {
    if (-not (Test-Path ".codegraph")) {
        & codegraph init -i
    } else {
        & codegraph sync
    }
    & codegraph status
} finally {
    Pop-Location
}
Write-Host "  OK: dev-stack + .codegraph/（本地，不进 git）" -ForegroundColor Green

# --- 4. 用户级规则（全局对话栈）---
Write-Host "[4/6] 写入用户级 Cursor 规则..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $UserCursorRules | Out-Null

$GlobalRulePath = Join-Path $UserCursorRules "00-ai-stack-global.mdc"
@'
---
description: 【用户级全局】CodeGraph + Hey AI README + Agency 184 + ECC 38 — 每条对话默认启用
alwaysApply: true
---

# 用户级：AI 全局对话栈

<HARD-GATE>
在 **上线网站** 工作区（`Desktop/上线网站`）或 **website CodeBuddy** 工作区内，每条用户消息自动启用：

1. **Agency 184 + ECC 38** — 项目规则 `00-agency-ecc-global-autoload.mdc` + `python scripts/agency-launch.py`
2. **Hey AI README** — `docs/Hey-AI-README.md`、`.cursor/rules/hey-ai-readme.mdc`（若存在）
3. **CodeGraph** — 存在 `.codegraph/` 时工程探索优先 MCP；MCP 名 `codegraph`
4. **开发工具隔离** — ECC/Cursor 在 `%USERPROFILE%\.devstack\shangxian-website\`；`.codegraph/` gitignore
5. **生产隔离** — 遵守 `.project/rules/00-workspace-isolation.mdc`
</HARD-GATE>

## 跨项目 fallback

非本仓库但为实质性开发任务时：

- Agency：`C:/Users/97907/.claude/agents/`
- 若项目含 `.codegraph/`，优先 CodeGraph MCP
- 若存在 `.cursor/agents/`，按 ECC 门控委派

## 安装/修复

在 **上线网站** 工作区运行：`scripts/install-dev-stack-external.ps1`
'@ | Set-Content -Path $GlobalRulePath -Encoding UTF8

Write-Host "  OK: $GlobalRulePath" -ForegroundColor Green

# 合并用户级 mcp.json 中的 codegraph
function Merge-CodegraphMcp([string]$Path) {
    if (-not (Test-Path $Path)) {
        @{ mcpServers = @{} } | ConvertTo-Json -Depth 10 | Set-Content $Path -Encoding UTF8
    }
    $json = Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $json.mcpServers) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue (@{}) -Force }
    $entry = @{
        command = "codegraph"
        args    = @("serve", "--mcp")
    }
    $json.mcpServers | Add-Member -NotePropertyName codegraph -NotePropertyValue $entry -Force
    $json | ConvertTo-Json -Depth 10 | Set-Content $Path -Encoding UTF8
}

Merge-CodegraphMcp $UserCursorMcp
# 不在产品仓库内写入 .cursor/mcp.json（开发工具隔离）

Write-Host "  OK: MCP codegraph → $UserCursorMcp" -ForegroundColor Green

# --- 5. 验证 Agency + ECC ---
Write-Host "[5/6] 验证 222 人编排..." -ForegroundColor Yellow
Push-Location $RepoRoot
try {
    python (Join-Path $RepoRoot "scripts\agency-launch.py")
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  安装完成。请重启 Cursor 使 MCP 与规则全局生效。" -ForegroundColor Green
Write-Host "  文档: docs/Hey-AI-README.md" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
