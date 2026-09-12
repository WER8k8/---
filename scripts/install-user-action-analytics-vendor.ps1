# 将 oeljeklaus-you/UserActionAnalyzePlatform 克隆到 deploy/vendor（Spark 源码，不进入 backend/）
param(
    [string]$Target = (Join-Path $PSScriptRoot "..\deploy\vendor\UserActionAnalyzePlatform"),
    [string]$Ref = "master"
)

$ErrorActionPreference = "Stop"
$Target = [System.IO.Path]::GetFullPath($Target)
$Repo = "https://github.com/oeljeklaus-you/UserActionAnalyzePlatform.git"

if (Test-Path (Join-Path $Target ".git")) {
    Write-Host "已存在：$Target — 执行 git pull"
    Push-Location $Target
    git fetch origin $Ref
    git checkout $Ref 2>$null
    git pull origin $Ref
    Pop-Location
    exit 0
}

$parent = Split-Path $Target -Parent
if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
if (Test-Path $Target) { Remove-Item $Target -Recurse -Force }

Write-Host "克隆 $Repo -> $Target"
git clone --depth 1 --branch $Ref $Repo $Target
Write-Host "完成。构建：cd $Target ; mvn -q package -DskipTests"
