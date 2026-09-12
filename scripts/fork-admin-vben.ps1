# FE-01 · 从 _ref/vue-vben-admin-full 初始化 frontend/admin-vben
# 用法: pwsh -File scripts/fork-admin-vben.ps1 [-Force]

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$Src = Join-Path $Root "_ref\vue-vben-admin-full"
$Dst = Join-Path $Root "frontend\admin-vben"

if (-not (Test-Path $Src)) {
    Write-Error "源不存在: $Src — 先运行 python scripts/clone-open-source-refs.py"
}

if ((Test-Path $Dst) -and -not $Force) {
    Write-Host "已存在 $Dst — 跳过（加 -Force 覆盖 apps/web-antd 以外根文件）"
    exit 0
}

New-Item -ItemType Directory -Force -Path $Dst | Out-Null

$Exclude = @("node_modules", ".git", "dist", ".turbo", ".pnpm-store")
$RoboArgs = @($Src, $Dst, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS")
foreach ($x in $Exclude) {
    $RoboArgs += "/XD"
    $RoboArgs += (Join-Path $Src $x)
}
robocopy @RoboArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $LASTEXITCODE" }

$Marker = Join-Path $Dst ".youding-fork.json"
@{
    source = "_ref/vue-vben-admin-full"
    forkedAt = (Get-Date -Format "yyyy-MM-dd")
    task = "FE-01"
    devCommand = "pnpm install; pnpm dev:antd"
    bffBase = "/api/v1/admin-bff"
} | ConvertTo-Json | Set-Content -Encoding UTF8 $Marker

Write-Host "OK: admin-vben -> $Dst"
Write-Host "Next: cd frontend/admin-vben && pnpm install && pnpm dev:antd"
