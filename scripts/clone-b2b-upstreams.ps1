# Clone B2B upstream repos for production sidecar deployment (optional local refs)
# Usage: powershell -File scripts/clone-b2b-upstreams.ps1
#        powershell -File scripts/clone-b2b-upstreams.ps1 -Shallow

param(
  [switch]$Shallow
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Dest = Join-Path $Root 'deploy\upstreams'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$repos = @(
  @{ Name = 'AI_Find_Customer'; Url = 'https://github.com/xiongQvQ/AI_Find_Customer.git'; Port = 8080; Sidecar = 8092 },
  @{ Name = 'EmailExtractor'; Url = 'https://github.com/zj1244/EmailExtractor.git'; Port = 0; Sidecar = 8093 },
  @{ Name = 'MediaCrawler'; Url = 'https://github.com/NanmiCoder/MediaCrawler.git'; Port = 0; Sidecar = 8094 },
  @{ Name = 'linkedin-scraper'; Url = 'https://github.com/joeyism/linkedin_scraper.git'; Port = 0; Sidecar = 8095 },
  @{ Name = 'CustomsDataSpider'; Url = 'https://github.com/CustomsDataSpider/CustomsDataSpider.git'; Port = 0; Sidecar = 8096 },
  @{ Name = 'LibreTranslate'; Url = 'https://github.com/LibreTranslate/LibreTranslate.git'; Port = 5000; Sidecar = 8098 }
)

foreach ($r in $repos) {
  $target = Join-Path $Dest $r.Name
  if (Test-Path -LiteralPath (Join-Path $target '.git')) {
    Write-Host "SKIP $($r.Name) (already cloned)" -ForegroundColor DarkGray
    continue
  }
  $depth = if ($Shallow) { @('--depth', '1') } else { @() }
  Write-Host "CLONE $($r.Name) -> $target" -ForegroundColor Cyan
  git clone @depth $r.Url $target
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL clone $($r.Name) (exit $LASTEXITCODE)" -ForegroundColor Red
    continue
  }
  if ($r.Port -gt 0) {
    $envExample = Join-Path $target '.env.youding-sidecar.example'
    @"
# YouDing sidecar wiring for $($r.Name)
# Sidecar adapter port: $($r.Sidecar)
# Upstream port (if applicable): $($r.Port)
UPSTREAM_URL=http://127.0.0.1:$($r.Port)
SIDECAR_TOKEN=change-me
ENVIRONMENT=production
HUMAN_VERIFY_REQUIRED=true
"@ | Set-Content -LiteralPath $envExample -Encoding UTF8
  }
}

Write-Host ''
Write-Host 'Upstream clones ready under deploy/upstreams/' -ForegroundColor Green
Write-Host 'Production: build sidecar adapters from deploy/examples/* and point env vars' -ForegroundColor Yellow
Write-Host 'Dev stubs: scripts/start-p6-sidecars-dev.ps1 (8092-8098 mock)' -ForegroundColor Yellow
