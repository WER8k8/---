# Hermes drive-chain manual-style E2E - product APIs only
$ErrorActionPreference = 'Continue'
$api = 'http://127.0.0.1:8001'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$rows = New-Object System.Collections.Generic.List[object]

function Invoke-Json($method, $url, $body, $headers) {
  $p = @{ Uri=$url; Method=$method; UseBasicParsing=$true; TimeoutSec=60 }
  if ($headers) { $p.Headers = $headers }
  if ($body) { $p.Body = $body; $p.ContentType = 'application/json' }
  return Invoke-WebRequest @p
}

function Record($id, $name, $ok, $ms, $detail) {
  $rows.Add([pscustomobject]@{ id=$id; name=$name; ok=$ok; ms=$ms; detail=$detail })
  $tag = if ($ok) { 'OK  ' } else { 'FAIL' }
  Write-Output ("{0} {1,-6} {2,-28} {3,5}ms  {4}" -f $tag, $id, $name, $ms, $detail)
}

Write-Output "======== HERMES DRIVE CHAIN E2E stamp=$stamp ========"

# login
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
  $lr = Invoke-RestMethod -Uri "$api/api/v1/auth/login" -Method Post -Body '{"username_or_email":"admin","password":"admin123"}' -ContentType 'application/json' -TimeoutSec 20
  $tok = $lr.data.access_token
  $sw.Stop()
  Record 'E2' 'login-admin' $true $sw.ElapsedMilliseconds 'tenant_admin/super ok'
} catch {
  $sw.Stop(); $tok = $null
  Record 'E2' 'login-admin' $false $sw.ElapsedMilliseconds $_.Exception.Message
}
$H = @{ Authorization = "Bearer $tok" }
$HJ = @{ Authorization = "Bearer $tok"; 'Content-Type'='application/json' }

# env
foreach ($item in @(
  @{id='E1'; name='api-health'; u="$api/api/v1/health"},
  @{id='E2b'; name='api-ready'; u="$api/api/v1/health/ready"},
  @{id='E3a'; name='admin-5173'; u='http://127.0.0.1:5173/'},
  @{id='E3b'; name='site-3000'; u='http://127.0.0.1:3000/'}
)) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  try { $null = Invoke-WebRequest $item.u -UseBasicParsing -TimeoutSec 10; $sw.Stop(); Record $item.id $item.name $true $sw.ElapsedMilliseconds '200' }
  catch { $sw.Stop(); Record $item.id $item.name $false $sw.ElapsedMilliseconds $_.Exception.Message }
}

function Test-Intent($id, $title, $intent, $payloadExtra) {
  $bodyObj = @{ intent = $intent; payload = $payloadExtra; channel = 'api'; auto_dispatch = $true; context = @{ plane='task'; source_test='hermes-e2e' } }
  $body = $bodyObj | ConvertTo-Json -Depth 6
  $sw = [Diagnostics.Stopwatch]::StartNew()
  try {
    $r = Invoke-Json POST "$api/api/v1/orchestration/tasks/from-intent" $body $HJ
    $sw.Stop()
    $j = $r.Content | ConvertFrom-Json
    $d = if ($j.data) { $j.data } else { $j }
    $src = $d.graph_source
    $plan = $d.plan_id
    $n = $d.node_count
    $disp = $d.dispatched
    $ok = ($src -eq 'L1_template' -or $src -eq 'L1_hybrid') -and $plan
    $detail = "src=$src nodes=$n disp=$disp plan=$plan"
    Record $id $title $ok $sw.ElapsedMilliseconds $detail
    # detail + latency
    if ($plan) {
      $sw2 = [Diagnostics.Stopwatch]::StartNew()
      try {
        $null = Invoke-Json GET "$api/api/v1/orchestration/hermes/tasks/$plan" $null $H
        $sw2.Stop()
        Record ($id+'d') ($title+'-detail') $true $sw2.ElapsedMilliseconds 'nodes ok'
      } catch {
        $sw2.Stop()
        Record ($id+'d') ($title+'-detail') $false $sw2.ElapsedMilliseconds $_.Exception.Message
      }
    }
  } catch {
    $sw.Stop()
    $resp = ''
    try {
      if ($_.Exception.Response) {
        $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $resp = $sr.ReadToEnd()
        if ($resp.Length -gt 140) { $resp = $resp.Substring(0,140) }
      }
    } catch {}
    Record $id $title $false $sw.ElapsedMilliseconds ($_.Exception.Message + ' ' + $resp)
  }
}

# golden paths
Test-Intent 'S1' 'GP-A fulfillment' 'fulfillment generate_pi order_fulfill' @{ message='drive e2e fulfillment'; product='EPS board'; name='E2E Buyer' }
Test-Intent 'S2' 'GP-B outreach' 'social_outreach whatsapp private domain outreach' @{ message='drive e2e outreach'; keywords=@('tiles') }

# other L1 scenarios (ASCII intents; template match uses keyword tokens)
Test-Intent 'S3' 'inquiry-convert' 'inquiry_reply inquiry convert followup' @{ message='reply inquiry'; email='buyer@example.com' }
Test-Intent 'S4' 'product-launch' 'product_launch publish product' @{ message='launch product'; product_name='Ceramic Tile A' }
Test-Intent 'S5' 'market-analysis' 'market_analysis research_analysis customs' @{ message='market analysis ceramics'; country='UAE' }
Test-Intent 'S6' 'lead-generation' 'lead_generation lead search prospect' @{ message='find leads tiles'; country='Germany' }
Test-Intent 'S7' 'browser-evidence' 'browser_evidence scrape webpage' @{ message='evidence capture'; url='https://example.com' }
Test-Intent 'S8' 'ubrain-assistant' 'ubrain assistant Q and A' @{ message='assistant: how to do B2B building materials leads?' }
Test-Intent 'S9' 'aeos-readiness' 'aeos_readiness aeos system check' @{ message='aeos readiness check' }
Test-Intent 'S10' 'billing-ops' 'billing_ops wallet balance check' @{ message='billing ops check' }
Test-Intent 'S11' 'risk-compliance' 'risk_compliance risk_scan sanctions screen' @{ message='sanctions screen buyer'; country='IR' }
Test-Intent 'S12' 'knowledge-seo' 'knowledge_seo content_acquisition seo' @{ message='content acquisition seo'; topic='insulation board' }
Test-Intent 'S13' 'tender-dealer' 'dealer_tender tender dealer' @{ message='dealer tender sample' }
Test-Intent 'S14' 'module-robot' 'module_robot module_batch business robot' @{ message='module robot smoke' }

# task center list
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
  $r = Invoke-Json GET "$api/api/v1/orchestration/hermes/tasks?limit=20" $null $H
  $sw.Stop()
  $j = $r.Content | ConvertFrom-Json; $d = if ($j.data) { $j.data } else { $j }
  Record 'S15' 'task-center-list' $true $sw.ElapsedMilliseconds ("total=" + $d.total)
} catch {
  $sw.Stop(); Record 'S15' 'task-center-list' $false $sw.ElapsedMilliseconds $_.Exception.Message
}

# work-mode
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
  $null = Invoke-Json GET "$api/api/v1/orchestration/golden-path/work-mode" $null $H
  $sw.Stop(); Record 'S16' 'work-mode' $true $sw.ElapsedMilliseconds 'ok'
} catch { $sw.Stop(); Record 'S16' 'work-mode' $false $sw.ElapsedMilliseconds $_.Exception.Message }

# tenant inquiry attribution regression
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
  $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  $null = Invoke-WebRequest "$api/api/v1/health" -WebSession $session -UseBasicParsing -TimeoutSec 8
  $csrf = $null
  foreach ($c in $session.Cookies.GetCookies($api)) { if ($c.Name -match 'csrf') { $csrf = $c.Value } }
  $hdr = @{}
  if ($csrf) { $hdr['X-CSRF-Token'] = $csrf }
  $b = @{ name='Drive Visitor '+$stamp; phone='+15550009999'; email=('drv-'+$stamp+'@ex.com'); product='EPS'; message='catalog please' } | ConvertTo-Json
  $null = Invoke-RestMethod "$api/api/v1/system/contact" -Method Post -Body $b -Headers $hdr -WebSession $session -ContentType 'application/json' -TimeoutSec 15
  $sw.Stop()
  Record 'R1' 'public-contact' $true $sw.ElapsedMilliseconds 'created'
} catch { $sw.Stop(); Record 'R1' 'public-contact' $false $sw.ElapsedMilliseconds $_.Exception.Message }

# summary
$fail = @($rows | Where-Object { -not $_.ok })
$okn = @($rows | Where-Object ok).Count
$taskRows = @($rows | Where-Object { $_.id -match '^S' -and $_.ok -and $_.id -notmatch 'd$' })
$maxMs = 0
$avg = 0
if ($taskRows.Count) {
  $ms = @($taskRows | ForEach-Object { [int]$_.ms })
  $maxMs = ($ms | Measure-Object -Maximum).Maximum
  $avg = [int]($ms | Measure-Object -Average).Average
}
Write-Output ("======== SUMMARY OK=" + $okn + " FAIL=" + $fail.Count + " task_avg_ms=" + $avg + " task_max_ms=" + $maxMs + " ========")
$fail | ForEach-Object { Write-Output ("FAIL " + $_.id + " " + $_.name + " " + $_.detail) }
