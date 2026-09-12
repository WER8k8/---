# 修复 Git 仓库错位：用户主目录误当仓库 vs 项目独立仓库
# 用法: powershell -File scripts/fix-git-isolation.ps1 [-CheckOnly] [-RetireHomeGit]
param(
    [switch]$CheckOnly,
    [switch]$RetireHomeGit
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$HomeGit = Join-Path $env:USERPROFILE ".git"
$ProjectGit = Join-Path $ProjectRoot ".git"

Write-Host "`n=== Git 隔离诊断 ===" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectRoot"
Write-Host "项目 .git: $(if (Test-Path $ProjectGit) { '存在' } else { '缺失' })"
Write-Host "主目录 .git: $(if (Test-Path $HomeGit) { '存在 (问题根源)' } else { '无' })"

Push-Location $ProjectRoot
$top = git rev-parse --show-toplevel 2>$null
Write-Host "当前 git 根: $top"
Pop-Location

if (Test-Path $HomeGit) {
    Push-Location $env:USERPROFILE
    Write-Host "`n--- 主目录仓库 remote ---" -ForegroundColor Yellow
    git remote -v 2>$null
    Write-Host "跟踪文件数: $((git ls-files 2>$null | Measure-Object).Count)"
    Write-Host "最近提交:"
    git log --oneline -3 2>$null
    Pop-Location
}

if ($CheckOnly) { exit 0 }

if (-not (Test-Path $ProjectGit)) {
    Write-Host "`n在项目内初始化 git (main)..." -ForegroundColor Green
    Push-Location $ProjectRoot
    git init -b main
    Pop-Location
}

if ($RetireHomeGit -and (Test-Path $HomeGit)) {
    $backup = Join-Path $env:USERPROFILE ".git.backup-home-accidental-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Host "`n备份并移走主目录 .git -> $backup" -ForegroundColor Yellow
    Rename-Item -Path $HomeGit -NewName (Split-Path $backup -Leaf)
    Write-Host "完成。如需恢复: Rename-Item '$backup' '.git'"
}

Write-Host @"

=== 下一步（在项目目录执行）===

1. 确认 remote（GitHub/Gitea 新建空仓库后）:
   git remote add origin https://github.com/YOUR_ORG/youding-website.git

2. 首次提交（仅产品路径，_ref/.venv/node_modules 已在 .gitignore）:
   git add backend frontend deploy docs scripts .project .gitignore Dockerfile docker-compose*.yml
   git commit -m "chore: 初始化上线网站独立仓库"

3. 推送:
   git push -u origin main

4. 云服务器:
   git clone https://github.com/YOUR_ORG/youding-website.git
   cd youding-website && ./deploy/deploy.sh

参考远程（CodeBuddy 对照仓）:
   https://github.com/WER8k8/-saas-.git

"@ -ForegroundColor Green
