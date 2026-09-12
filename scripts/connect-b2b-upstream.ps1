# Wire cloned B2B upstream into backend/config/dev/.env
# Usage:
#   powershell -File scripts/connect-b2b-upstream.ps1
#   powershell -File scripts/connect-b2b-upstream.ps1 -UpstreamUrl http://127.0.0.1:8080

param(
  [ValidateSet('AI_Find_Customer', 'LibreTranslate')]
  [string]$Name = 'AI_Find_Customer',
  [string]$UpstreamUrl = 'http://127.0.0.1:8080'
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$CloneDir = Join-Path $Root "deploy\upstreams\$Name"
$DevEnv = Join-Path $Root 'backend\config\dev\.env'

function Set-EnvLine([string]$Text, [string]$Key, [string]$Value) {
  $pattern = "(?m)^$([regex]::Escape($Key))=.*$"
  $line = "$Key=$Value"
  if ($Text -match $pattern) {
    return [regex]::Replace($Text, $pattern, $line)
  }
  if (-not $Text.EndsWith("`n")) { $Text += "`r`n" }
  return $Text + $line + "`r`n"
}

if (-not (Test-Path -LiteralPath $DevEnv)) {
  Write-Error "Missing $DevEnv"
}

if (-not (Test-Path -LiteralPath $CloneDir)) {
  Write-Host "WARN clone dir missing: $CloneDir — run scripts/clone-b2b-upstreams.ps1" -ForegroundColor Yellow
}

$text = Get-Content -LiteralPath $DevEnv -Raw -Encoding UTF8

if ($Name -eq 'AI_Find_Customer') {
  $text = Set-EnvLine $text 'AI_FIND_CUSTOMER_URL' 'http://127.0.0.1:8092'
  $text = Set-EnvLine $text 'AI_FIND_CUSTOMER_TOKEN' 'dev-sidecar-token'
  $text = Set-EnvLine $text 'AI_HUNTER_UPSTREAM_URL' $UpstreamUrl
  $text = Set-EnvLine $text 'AI_FIND_CUSTOMER_ALLOW_DEV_STUB' '0'
}

if ($Name -eq 'LibreTranslate') {
  $text = Set-EnvLine $text 'LIBRETRANSLATE_URL' 'http://127.0.0.1:8098'
  $text = Set-EnvLine $text 'LIBRETRANSLATE_TOKEN' 'dev-sidecar-token'
  $text = Set-EnvLine $text 'LIBRETRANSLATE_ALLOW_DEV_STUB' '0'
}

Set-Content -LiteralPath $DevEnv -Value $text -Encoding UTF8 -NoNewline
Write-Host "OK wired $Name upstream=$UpstreamUrl" -ForegroundColor Green
Write-Host "Next: start sidecars + restart backend (launch-dev-admin-safe.ps1 -ForceRestart)" -ForegroundColor Yellow
