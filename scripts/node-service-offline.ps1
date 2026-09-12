# T-NODE-3：Node seo-backend 下线检查清单（不自动删生产）
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Write-Host "Node 下线前置检查"
Write-Host "1. FastAPI seo_matrix 已就绪 -> scripts/seo-node-parity-check.py"
Write-Host "2. 网关移除 seo-backend :3000 上游"
Write-Host "3. docker compose 勿启动 seo-backend 服务"
$compose = Join-Path $Root "docker-compose.dev.yml"
if (Test-Path $compose) {
  $c = Get-Content $compose -Raw
  if ($c -notmatch "seo-backend") { Write-Host "[OK] compose 未依赖 seo-backend" -ForegroundColor Green }
}
Write-Host "详见 docs/出海计/Node服务下线清单.md"
