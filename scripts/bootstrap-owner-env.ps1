# 从 .env.example 生成 backend/.env 骨架（Owner O-1/O-2 填真实值）
# Usage: powershell -File scripts/bootstrap-owner-env.ps1

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Example = Join-Path $Root '.env.example'
$Target = Join-Path $Root 'backend\.env'

if (-not (Test-Path -LiteralPath $Example)) {
  Write-Error "Missing $Example"
}

if (Test-Path -LiteralPath $Target) {
  Write-Host "backend/.env already exists — not overwriting. Edit manually or rename first." -ForegroundColor Yellow
  exit 0
}

$devBlock = @'

# --- bootstrap-owner-env.ps1 dev overrides ---
ENVIRONMENT=development
DATABASE_URL=sqlite:///./youding_dev.db
REDIS_ENABLED=false
LOGIN_BF_USE_REDIS=false
MVP_LAUNCH=1
JWT_SECRET_KEY=dev-local-change-me-32chars-min!!
SECRET_KEY=dev-local-change-me-32chars-min!!

# --- Owner O-2 · AiToEarn（Publish / Engage / Analytics）---
# 1. 填入 AITOEARN_API_KEY（运维控制台获取）
# 2. 超管 /tenants/dashboard → 租户行「AiToEarn」自动分配矩阵槽位
# 3. 租户 /client/distribute → 同步矩阵号 → 视频真发 / 定时排期
# 4. 租户 /client/engage → 拉评 + AiToEarn 真回复
# 未配 Key 时 API 返回 503，禁止假成功（见 docs/ops/ai-key-setup.md §7）
# AITOEARN_API_KEY=
# AITOEARN_API_BASE=https://mcp.aitoearn.cn
'@

(Get-Content -LiteralPath $Example -Raw -Encoding UTF8) + $devBlock | Set-Content -LiteralPath $Target -Encoding UTF8
Write-Host "Created $Target" -ForegroundColor Green
Write-Host "Next steps (Owner O-2):" -ForegroundColor Cyan
Write-Host "  1. AITOEARN_API_KEY + AI_DEEPSEEK_API_KEY in backend/.env"
Write-Host "  2. Admin /tenants/dashboard -> AiToEarn -> auto-assign per tenant"
Write-Host "  3. Tenant /client/distribute -> sync matrix -> publish"
Write-Host "Also: DEMO_HTTPS_DOMAIN, WECOM_*, DOUYIN_* for production rehearsal"
