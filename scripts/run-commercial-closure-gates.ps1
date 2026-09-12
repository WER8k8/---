# COMM commercial closure gates — dev-automatable only (honest: not Owner items)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$results = @()

function Add-Result($name, $ok, $detail) {
  $script:results += [ordered]@{ name = $name; ok = $ok; detail = $detail }
}

Write-Host '== validate-stub-matrix-sync =='
$stubOut = python scripts/validate-stub-matrix-sync.py 2>&1 | Out-String
Add-Result 'stub-matrix-sync' ($LASTEXITCODE -eq 0) $stubOut.Trim()

Write-Host '== validate-no-fake-delivery =='
$fakeOut = python scripts/validate-no-fake-delivery.py 2>&1 | Out-String
Add-Result 'no-fake-delivery' ($LASTEXITCODE -eq 0) $fakeOut.Trim()

Write-Host '== validate-cert-screenshot-assignments =='
$certOut = python scripts/validate-cert-screenshot-assignments.py 2>&1 | Out-String
Add-Result 'cert-screenshot-assignments' ($LASTEXITCODE -eq 0) $certOut.Trim()

Write-Host '== cert:login-lock =='
Push-Location frontend/admin
$loginOut = npm run cert:login-lock 2>&1 | Out-String
Add-Result 'cert:login-lock' ($LASTEXITCODE -eq 0) $loginOut.Trim()
Pop-Location

Write-Host '== verify-role-shell-lock =='
$shellOut = powershell -File scripts/verify-role-shell-lock.ps1 2>&1 | Out-String
Add-Result 'role-shell-lock' ($LASTEXITCODE -eq 0) $shellOut.Trim()

$ownerBlockers = @(
  @{ id = 'O-1'; title = 'HTTPS demo domain DNS'; status = 'owner_pending' },
  @{ id = 'O-2'; title = 'Inquiry IM / WeCom secrets'; status = 'owner_pending' },
  @{ id = 'O-3'; title = '5+5 platform table + pricing signoff'; status = 'owner_pending' }
)

Write-Host '== write-commercial-closure-report =='
$closureOut = python scripts/write-commercial-closure-report.py 2>&1 | Out-String
Add-Result 'commercial-closure-report' ($LASTEXITCODE -eq 0) $closureOut.Trim()
$devComplete = ($results | Where-Object { -not $_.ok }).Count -eq 0
Write-Host $closureOut.Trim()
if (-not $devComplete) { exit 1 }
exit 0
