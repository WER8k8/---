# Sprint-R1 · 研发门禁一键验证（第七轮 · 含 ARCH-01 / QA-04 / MOD-04/08）
# Usage:
#   powershell -File scripts/run-r1-dev-gate.ps1
#   powershell -File scripts/run-r1-dev-gate.ps1 -RefreshLocustDryrun
param([switch]$RefreshLocustDryrun)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
$Report = Join-Path $Root "docs\r1-dev-gate-latest.json"
$results = New-Object System.Collections.Generic.List[object]

function Run-Step($Name, $ScriptBlock) {
  Write-Host "=== $Name ===" -ForegroundColor Cyan
  $exit = 0
  try { & $ScriptBlock } catch { $exit = 1 }
  if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { $exit = $LASTEXITCODE }
  $ok = ($exit -eq 0)
  $results.Add([ordered]@{ step = $Name; ok = $ok; exit = $exit }) | Out-Null
  if ($ok) { Write-Host "$Name PASS" -ForegroundColor Green } else { Write-Host "$Name FAIL ($exit)" -ForegroundColor Red }
}

Run-Step "ARCH-01 preflight" { & $Py (Join-Path $Root "scripts\validate-arch-01-preflight.py") }
Run-Step "COMP-02 brand strict" { & $Py (Join-Path $Root "scripts\validate-brand-strict.py") }
Run-Step "QA-02 cert gate" { & $Py (Join-Path $Root "scripts\validate-qa-02-cert-gate.py") }
Run-Step "Owner blockers sync" { & $Py (Join-Path $Root "scripts\sync-owner-blockers-from-records.py") }
Run-Step "ARCH-04 compose" { powershell -File (Join-Path $Root "scripts\run-arch-04-https-compose.ps1") }
Run-Step "ARCH-04 certbot preflight" { & $Py (Join-Path $Root "scripts\validate-arch-04-certbot-preflight.py") }
Run-Step "ARCH-04 staging https" { & $Py (Join-Path $Root "scripts\validate-arch-04-staging-https.py") }
Run-Step "BJ-01 Formily" { & $Py (Join-Path $Root "scripts\validate-bj-01-formily.py") }
Run-Step "BE-06 export" { & $Py (Join-Path $Root "scripts\validate-be-06-export.py") }
Run-Step "BE-06 s2 readiness" { & $Py (Join-Path $Root "scripts\validate-be-06-s2-readiness.py") }
Run-Step "QA-04 locust bundle" { & $Py (Join-Path $Root "scripts\validate-qa-04-locust-bundle.py") }
if ($RefreshLocustDryrun) {
  Run-Step "QA-04 locust dryrun" { powershell -File (Join-Path $Root "scripts\qa-locust-72h-dryrun.ps1") }
}
Run-Step "MOD-02 IM keys" { & $Py (Join-Path $Root "scripts\validate-mod-02-im-keys.py") }
Run-Step "MOD-02 webhook smoke" { & $Py (Join-Path $Root "scripts\validate-mod-02-webhook-smoke.py") }
Run-Step "MOD-02 staging handoff" { & $Py (Join-Path $Root "scripts\validate-mod-02-staging-handoff.py") }
Run-Step "MOD-04 recording prep" { & $Py (Join-Path $Root "scripts\validate-mod-04-recording-prep.py") }
Run-Step "MOD-04 recording routes" { & $Py (Join-Path $Root "scripts\validate-mod-04-recording-routes.py") }
Run-Step "MOD-04 recording rehearsal" { powershell -File (Join-Path $Root "scripts\run-mod-04-recording-rehearsal.ps1") }
Run-Step "MOD-04 https step" { & $Py (Join-Path $Root "scripts\validate-mod-04-https-step.py") }
Run-Step "MOD-04 rehearsal screenshots" { powershell -File (Join-Path $Root "scripts\run-mod-04-rehearsal-screenshots.ps1") }
Run-Step "MOD-03 platform signoff" { & $Py (Join-Path $Root "scripts\validate-mod-03-platform-signoff.py") }
Run-Step "MOD-07 trade matrix" { & $Py (Join-Path $Root "scripts\validate-mod-07-trade-matrix-signoff.py") }
Run-Step "MOD-05 migrations" { & $Py (Join-Path $Root "scripts\validate-mod-05-migrations.py") }
Run-Step "MOD-05 staging" { powershell -File (Join-Path $Root "scripts\run-mod-05-staging-migrate.ps1") }
Run-Step "MOD-05 prod runbook" { & $Py (Join-Path $Root "scripts\validate-mod-05-prod-runbook.py") }
Run-Step "MOD-06 cap prep" { & $Py (Join-Path $Root "scripts\validate-mod-06-cap-prep.py") }
Run-Step "MOD-06 chuhaiji" { & $Py (Join-Path $Root "scripts\validate-mod-06-chuhaiji-app.py") }
Run-Step "MOD-06 android aab prep" { & $Py (Join-Path $Root "scripts\validate-mod-06-android-aab.py") }
Run-Step "MOD-08 blockers" { & $Py (Join-Path $Root "scripts\validate-mod-08-blockers.py") }
Run-Step "MOD-08 owner readiness" { & $Py (Join-Path $Root "scripts\validate-mod-08-owner-readiness.py") }
Run-Step "PAT-02 handoff" { & $Py (Join-Path $Root "scripts\validate-pat-02-handoff.py") }
Run-Step "PAT-02 bundle" { & $Py (Join-Path $Root "scripts\export-pat-02-handoff-bundle.py") }
Run-Step "COMP-06 bundle" { & $Py (Join-Path $Root "scripts\validate-comp-06-bundle.py") }
Run-Step "COMP-06 lawyer signoff" { & $Py (Join-Path $Root "scripts\validate-comp-06-lawyer-signoff.py") }

$fail = @($results | Where-Object { -not $_.ok }).Count
$stepList = @()
foreach ($s in $results) { $stepList += @{ step = $s.step; ok = $s.ok; exit = $s.exit } }
$payload = @{
  generated_at = (Get-Date).ToString("o")
  task = "R1-dev-gate"
  round = 15
  pass = ($fail -eq 0)
  fail_count = $fail
  step_count = $results.Count
  steps = $stepList
}
($payload | ConvertTo-Json -Depth 5) | Set-Content -Path $Report -Encoding UTF8

if ($fail -eq 0) {
  Write-Host "R1 dev gate: ALL PASS ($($results.Count) steps) -> $Report" -ForegroundColor Green
  exit 0
}
Write-Host "R1 dev gate: $fail step(s) failed -> $Report" -ForegroundColor Red
exit 1
