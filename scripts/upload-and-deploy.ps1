# 本机 → 云服务器：同步源码并触发远程部署 + 自动展开
# 用法:
#   $env:DEPLOY_HOST="user@1.2.3.4"
#   $env:DEPLOY_PATH="/opt/youding"
#   powershell -File scripts/upload-and-deploy.ps1
#   powershell -File scripts/upload-and-deploy.ps1 -SkipBuild

param(
    [string]$DeployHost = $env:DEPLOY_HOST,
    [string]$DeployPath = $(if ($env:DEPLOY_PATH) { $env:DEPLOY_PATH } else { "/opt/youding" }),
    [switch]$SkipBuild,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

if (-not $DeployHost) {
    Write-Host "请设置 DEPLOY_HOST，例如: user@your-server-ip" -ForegroundColor Yellow
    Write-Host '  $env:DEPLOY_HOST="root@1.2.3.4"; powershell -File scripts/upload-and-deploy.ps1'
    exit 1
}

$Excludes = @(
    ".git", ".codegraph", ".cursor", "node_modules", "__pycache__",
    ".venv", "venv", "dist", ".env", ".env.prod", "backend/uploads",
    "*.pyc", ".pytest_cache",
    "_ref", "_build_check", "staging-data",
    "frontend/.nuxt", "frontend/.output", "frontend/admin/dist"
)

Write-Host "=== 1. Sync -> ${DeployHost}:${DeployPath} ===" -ForegroundColor Cyan

$hasRsync = Get-Command rsync -ErrorAction SilentlyContinue
if ($DryRun) {
    if ($hasRsync) {
        $excludeArgs = ($Excludes | ForEach-Object { "--exclude=$_" }) -join " "
        Write-Host "rsync -avz --delete --dry-run $excludeArgs `"$Root/`" `${DeployHost}:${DeployPath}/"
    } else {
        Write-Host "rsync not found; would tar+scp from: $Root"
        Write-Host "Excludes: $($Excludes -join ', ')"
    }
} elseif ($hasRsync) {
    $excludeArgs = ($Excludes | ForEach-Object { "--exclude=$_" }) -join " "
    $rsyncCmd = "rsync -avz --delete $excludeArgs `"$Root/`" `${DeployHost}:${DeployPath}/"
    Write-Host $rsyncCmd
    Invoke-Expression $rsyncCmd
} else {
    Write-Host "未找到 rsync，使用 scp 压缩包（较慢）..." -ForegroundColor Yellow
    $tar = Join-Path $env:TEMP "youding-deploy-$(Get-Date -Format yyyyMMddHHmmss).tar.gz"
    Push-Location $Root
    try {
        $tarArgs = @("-czf", $tar)
        foreach ($ex in $Excludes) {
            $tarArgs += "--exclude=$ex"
        }
        $tarArgs += "."
        & tar @tarArgs
        scp $tar "${DeployHost}:${DeployPath}/deploy-bundle.tar.gz"
        ssh $DeployHost "mkdir -p $DeployPath && cd $DeployPath && tar -xzf deploy-bundle.tar.gz && rm -f deploy-bundle.tar.gz"
    } finally {
        Pop-Location
        Remove-Item $tar -ErrorAction SilentlyContinue
    }
}

Write-Host "`n=== 2. 远程部署 + 自动展开 ===" -ForegroundColor Cyan
$remote = @"
set -e
cd '$DeployPath'
export HERMES_AGENCY_AUTO_DOCKER_OLLAMA=1
if [ -f deploy/deploy.sh ]; then
  chmod +x deploy/deploy.sh scripts/cloud-post-deploy.sh scripts/setup-agency-llm-providers.sh 2>/dev/null || true
  if [ '$($SkipBuild.IsPresent)' = 'True' ]; then
    bash scripts/cloud-post-deploy.sh
  else
    ./deploy/deploy.sh --skip-ssl || ./deploy/deploy.sh
    bash scripts/cloud-post-deploy.sh
  fi
else
  bash scripts/cloud-post-deploy.sh
fi
"@

if ($DryRun) {
    Write-Host "[dry-run] ssh $DeployHost <<EOF`n$remote`nEOF"
    exit 0
}

ssh $DeployHost $remote

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host 'Hermes: production backend auto patrol every 15 min when ENVIRONMENT=production'
$manual = ('ssh {0} "cd {1}/backend && python3 scripts/run_ops_jobs.py --job hermes-ops"' -f $DeployHost, $DeployPath)
Write-Host "Manual: $manual"
