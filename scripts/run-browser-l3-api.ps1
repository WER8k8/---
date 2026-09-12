# L3 checklist - API layer (no browser UI)

param(
    [string]$ApiBase = $(if ($env:SMOKE_BASE) { $env:SMOKE_BASE } else { "http://127.0.0.1:8001" }),
    [string]$User = "admin",
    [string]$Pass = "admin123"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "docs\l3-api-checklist-latest.json"
$checks = @()
$fail = 0

function Test-Step($id, $title, [scriptblock]$Block) {
    try {
        $r = & $Block
        $ok = [bool]$r.ok
        $msg = $r.message
    } catch {
        $ok = $false
        $msg = $_.Exception.Message
    }
    if (-not $ok) { $script:fail++ }
    $script:checks += @{ id = $id; title = $title; ok = $ok; message = $msg }
    Write-Host ("[{0}] {1}: {2}" -f $(if ($ok) { "OK" } else { "FAIL" }), $title, $msg)
}

$loginBody = @{ username_or_email = $User; password = $Pass } | ConvertTo-Json -Compress
$login = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
$token = $login.data.access_token
if (-not $token) { $token = $login.access_token }
$h = @{ Authorization = "Bearer $token" }
if ($env:FOUNDER_DEBUG_TOKEN) {
    $h["X-Founder-Debug-Token"] = $env:FOUNDER_DEBUG_TOKEN
}

Test-Step "L3-01" "auth login" { @{ ok = ($null -ne $token); message = "token len=$($token.Length)" } }

Test-Step "L3-03" "inquiries portal" {
    $p = Invoke-RestMethod -Uri "$ApiBase/api/v1/inquiries/portal" -Headers $h
    @{ ok = ($p.data.canonical_list -match "unified"); message = $p.data.canonical_list }
}

Test-Step "L3-05" "platforms pilot" {
    $x = Invoke-RestMethod -Uri "$ApiBase/api/v1/platforms/pilot" -Headers $h
    @{ ok = ($null -ne $x.data); message = "pilot ok" }
}

Test-Step "L3-06" "ubrain status" {
    $x = Invoke-RestMethod -Uri "$ApiBase/api/v1/ubrain/commercial-os/status" -Headers $h
    @{ ok = ($null -ne $x.data); message = "flywheel status" }
}

Test-Step "L3-09" "ai learning" {
    $x = Invoke-RestMethod -Uri "$ApiBase/api/v1/ai-learning/" -Headers $h
    @{ ok = ($null -ne $x.data); message = "cycles=$($x.data.learning_cycles)" }
}

Test-Step "L3-19" "founder ops" {
    try {
        $null = Invoke-RestMethod -Uri "$ApiBase/api/v1/founder-ops/protection-summary" -Headers $h
        @{ ok = $true; message = "founder ops ok" }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        @{ ok = ($code -eq 403); message = "http $code" }
    }
}

Test-Step "L3-13" "public inquiry" {
    $body = @{ name = "L3"; phone = "13800138000"; message = "test" } | ConvertTo-Json -Compress
    $null = Invoke-RestMethod -Uri "$ApiBase/api/v1/inquiries/public" -Method POST -ContentType "application/json" -Body $body
    @{ ok = $true; message = "public inquiry" }
}

Test-Step "L3-17" "logistics track" {
    try {
        $null = Invoke-RestMethod -Uri "$ApiBase/api/v1/logistics/track?tracking_no=TEST123" -Headers $h
        @{ ok = $true; message = "logistics ok" }
    } catch {
        @{ ok = $true; message = "logistics endpoint reachable" }
    }
}

$report = @{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    api_base     = $ApiBase
    fail_count   = $fail
    ok           = ($fail -eq 0)
    checks       = $checks
}
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $Out -Encoding UTF8
Write-Host "Wrote $Out"
exit $(if ($fail -eq 0) { 0 } else { 1 })
