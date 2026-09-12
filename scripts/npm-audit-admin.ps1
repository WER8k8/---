# T-NPM-AUDIT：管理端依赖审计（专家团 P2 #6 — 优先官方 registry）
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "docs\security-npm-audit-admin.json"
$AdminDir = Join-Path $Root "frontend\admin"
$Registries = @(
    "https://registry.npmjs.org",
    "https://registry.npmmirror.com"
)

Push-Location $AdminDir
$ok = $false
foreach ($reg in $Registries) {
    Write-Host "npm audit via $reg" -ForegroundColor Cyan
    $prev = $env:NPM_CONFIG_REGISTRY
    $env:NPM_CONFIG_REGISTRY = $reg
    npm audit --json 2>$null | Out-File -Encoding utf8 $Out
    $exit = $LASTEXITCODE
    if ($prev) { $env:NPM_CONFIG_REGISTRY = $prev } else { Remove-Item Env:NPM_CONFIG_REGISTRY -ErrorAction SilentlyContinue }
    $raw = Get-Content $Out -Raw -ErrorAction SilentlyContinue
    if ($raw -and $raw -notmatch 'NOT_IMPLEMENTED' -and $raw -notmatch '404 Not Found') {
        $ok = $true
        npm audit 2>&1
        break
    }
}
Pop-Location

if (-not $ok) {
    @{ generated_at = (Get-Date).ToUniversalTime().ToString("o"); error = "npm audit unavailable on configured registries"; advisories = @{} } |
        ConvertTo-Json -Depth 4 | Set-Content -Path $Out -Encoding UTF8
    Write-Host "WARN: npm audit skipped — registry security API unavailable" -ForegroundColor Yellow
    exit 0
}

Write-Host "Report: $Out" -ForegroundColor Green
exit 0
