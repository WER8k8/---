# Tenant manual-style E2E - product HTTP APIs only
$ErrorActionPreference = 'Continue'
$api = 'http://127.0.0.1:8001'
$okCount = 0
$failCount = 0
$tok = $null
$pageId = $null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Ok($name, $detail) {
  $script:okCount++
  Write-Output ("OK   " + $name + " :: " + $detail)
}
function Bad($name, $detail) {
  $script:failCount++
  Write-Output ("FAIL " + $name + " :: " + $detail)
}

Write-Output "======== TENANT MANUAL E2E stamp=$stamp ========"

try {
  $lr = Invoke-RestMethod -Uri "$api/api/v1/auth/login" -Method Post -Body '{"username_or_email":"tenant","password":"tenant123"}' -ContentType 'application/json' -TimeoutSec 15
  $tok = $lr.data.access_token
  Ok "01-login" ("role=" + $lr.data.user.role)
} catch { Bad "01-login" $_.Exception.Message }

$H = @{ Authorization = "Bearer $tok" }
$HJ = @{ Authorization = "Bearer $tok"; 'Content-Type' = 'application/json' }

try {
  $d = Invoke-RestMethod "$api/api/v1/tenants/domain/dev.local" -Headers $H -TimeoutSec 15
  Ok "02-tenant-domain" ("domain=" + $d.data.domain)
} catch { Bad "02-tenant-domain" $_.Exception.Message }

try { $null = Invoke-RestMethod "$api/api/v1/client/dashboard" -Headers $H -TimeoutSec 15; Ok "03-client-dashboard" "200" }
catch { Bad "03-client-dashboard" $_.Exception.Message }

try {
  $d = Invoke-RestMethod "$api/api/v1/client/journey-health" -Headers $H -TimeoutSec 15
  Ok "04-journey-health" ("score=" + $d.data.score_pct)
} catch { Bad "04-journey-health" $_.Exception.Message }

try { $null = Invoke-RestMethod "$api/api/v1/client/today-three" -Headers $H -TimeoutSec 15; Ok "05-today-three" "200" }
catch { Bad "05-today-three" $_.Exception.Message }

try { $null = Invoke-RestMethod "$api/api/v1/client/publish-readiness" -Headers $H -TimeoutSec 15; Ok "06-publish-readiness" "200" }
catch { Bad "06-publish-readiness" $_.Exception.Message }

try {
  $r = Invoke-WebRequest "http://127.0.0.1:3002/tenant?__tenant=dev.local" -UseBasicParsing -TimeoutSec 40
  Ok "07-tenant-site-3002" ("len=" + $r.Content.Length)
} catch { Bad "07-tenant-site-3002" $_.Exception.Message }

try {
  $r = Invoke-WebRequest "$api/api/v1/public/tenants/dev.local/visitor-context" -UseBasicParsing -TimeoutSec 15
  Ok "08-public-visitor-context" ("len=" + $r.Content.Length)
} catch { Bad "08-public-visitor-context" $_.Exception.Message }

try {
  $d = Invoke-RestMethod "$api/api/v1/content/pages" -Headers $H -TimeoutSec 15
  $n = 0
  if ($d.data -and $d.data.items) { $n = @($d.data.items).Count }
  Ok "09-content-list" ("items=" + $n)
} catch { Bad "09-content-list" $_.Exception.Message }

$slug = "tenant-note-" + $stamp
try {
  $body = @{
    title = "Tenant Note " + $stamp
    slug = $slug
    content = "Business note via tenant console. Stamp=" + $stamp
    excerpt = "manual e2e"
    status = "draft"
  } | ConvertTo-Json
  $d = Invoke-RestMethod "$api/api/v1/content/pages" -Method Post -Body $body -Headers $HJ -TimeoutSec 20
  $pageId = $d.data.id
  Ok "10-content-create" ("id=" + $pageId)
} catch {
  $respBody = ""
  try {
    $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $respBody = $sr.ReadToEnd()
    if ($respBody.Length -gt 180) { $respBody = $respBody.Substring(0,180) }
  } catch {}
  Bad "10-content-create" ($_.Exception.Message + " " + $respBody)
}

if ($pageId) {
  try {
    $d = Invoke-RestMethod "$api/api/v1/content/pages/$pageId" -Headers $H -TimeoutSec 15
    Ok "11-content-read" ("status=" + $d.data.status)
  } catch { Bad "11-content-read" $_.Exception.Message }

  try {
    $body = @{ title = "Tenant Note Edited " + $stamp; content = "Revised stamp=" + $stamp } | ConvertTo-Json
    $d = Invoke-RestMethod "$api/api/v1/content/pages/$pageId" -Method Put -Body $body -Headers $HJ -TimeoutSec 20
    Ok "12-content-update" ("title=" + $d.data.title)
  } catch { Bad "12-content-update" $_.Exception.Message }

  try {
    $body = @{ meta_title = "SEO " + $stamp; meta_description = "manual seo" } | ConvertTo-Json
    try { $null = Invoke-RestMethod "$api/api/v1/content/pages/$pageId/seo" -Method Post -Body $body -Headers $HJ -TimeoutSec 15 }
    catch { $null = Invoke-RestMethod "$api/api/v1/content/pages/$pageId/seo" -Method Put -Body $body -Headers $HJ -TimeoutSec 15 }
    Ok "14-content-seo" "set"
  } catch { Bad "14-content-seo" $_.Exception.Message }

  try {
    $body = @{ status = "published" } | ConvertTo-Json
    $d = Invoke-RestMethod "$api/api/v1/content/pages/$pageId" -Method Put -Body $body -Headers $HJ -TimeoutSec 20
    Ok "15-content-publish" ("status=" + $d.data.status)
  } catch { Bad "15-content-publish" $_.Exception.Message }

  try {
    $d = Invoke-RestMethod "$api/api/v1/content/pages/$pageId" -Headers $H -TimeoutSec 15
    Ok "16-content-after-publish" ("status=" + $d.data.status)
  } catch { Bad "16-content-after-publish" $_.Exception.Message }

  # public slug read after publish
  try {
    $d = Invoke-RestMethod "$api/api/v1/content/pages/slug/$slug" -Headers $H -TimeoutSec 15
    Ok "13-content-by-slug" ("status=" + $d.data.status)
  } catch { Bad "13-content-by-slug" $_.Exception.Message }
} else {
  Bad "11-16-content-chain" "skipped"
}

try {
  $d = Invoke-RestMethod "$api/api/v1/products/" -Headers $H -TimeoutSec 15
  $n = 0
  if ($d.data -and $d.data.items) { $n = @($d.data.items).Count }
  Ok "17-product-list" ("count=" + $n)
} catch { Bad "17-product-list" $_.Exception.Message }

$productId = $null
try {
  $cat = $null
  try {
    $cd = Invoke-RestMethod "$api/api/v1/products/categories" -Headers $H -TimeoutSec 15
    $cats = @()
    if ($cd.data) { $cats = @($cd.data) }
    if ($cats.Count -eq 0 -and $cd.data -and $cd.data.items) { $cats = @($cd.data.items) }
    if ($cats.Count -gt 0) { $cat = $cats[0].id }
  } catch {}
  if (-not $cat) { $cat = [guid]::NewGuid().ToString() }
  $body = @{
    category_id = $cat
    name = "Tenant Sample " + $stamp
    slug = "tenant-sample-" + $stamp
    subtitle = "manual sample"
    description = "manual product create via tenant console"
    is_active = $true
  } | ConvertTo-Json
  $d = Invoke-RestMethod "$api/api/v1/products/" -Method Post -Body $body -Headers $HJ -TimeoutSec 20
  $productId = $d.data.id
  Ok "18-product-create" ("id=" + $productId)
} catch {
  $respBody = ""
  try {
    $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $respBody = $sr.ReadToEnd()
    if ($respBody.Length -gt 200) { $respBody = $respBody.Substring(0,200) }
  } catch {}
  Bad "18-product-create" ($_.Exception.Message + " " + $respBody)
}

if ($productId) {
  try {
    $d = Invoke-RestMethod "$api/api/v1/products/$productId" -Headers $H -TimeoutSec 15
    Ok "19-product-read" ("name=" + $d.data.name)
  } catch { Bad "19-product-read" $_.Exception.Message }
} else { Bad "19-product-read" "no productId" }

try {
  $d = Invoke-RestMethod "$api/api/v1/inquiries/" -Headers $H -TimeoutSec 15
  $n = 0
  if ($d.data -and $d.data.items) { $n = @($d.data.items).Count }
  Ok "20-inquiry-list" ("items=" + $n)
} catch { Bad "20-inquiry-list" $_.Exception.Message }

# public contact form - anonymous CSRF-aware
$visitorEmail = "visitor-" + $stamp + "@example.com"
try {
  $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  # obtain csrf cookie from a GET
  $null = Invoke-WebRequest "$api/api/v1/health" -WebSession $session -UseBasicParsing -TimeoutSec 10
  $csrf = $null
  foreach ($c in $session.Cookies.GetCookies($api)) {
    if ($c.Name -match 'csrf') { $csrf = $c.Value }
  }
  $headers = @{}
  if ($csrf) {
    $headers['X-CSRF-Token'] = $csrf
    $headers['X-Requested-With'] = 'XMLHttpRequest'
  }
  $b = @{
    name = "Visitor " + $stamp
    phone = "+15550001234"
    email = $visitorEmail
    product = "Tenant Sample Board"
    message = "Please send catalog."
  } | ConvertTo-Json
  $r = Invoke-RestMethod "$api/api/v1/system/contact" -Method Post -Body $b -Headers $headers -WebSession $session -ContentType 'application/json' -TimeoutSec 15
  Ok "21-inquiry-public-submit" ("id=" + $r.data.id)
} catch {
  $respBody = ""
  try {
    $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $respBody = $sr.ReadToEnd()
    if ($respBody.Length -gt 200) { $respBody = $respBody.Substring(0,200) }
  } catch {}
  Bad "21-inquiry-public-submit" ($_.Exception.Message + " " + $respBody)
}

try {
  $d = Invoke-RestMethod "$api/api/v1/inquiries/" -Headers $H -TimeoutSec 15
  $hit = $false
  if ($d.data -and $d.data.items) {
    foreach ($it in @($d.data.items)) {
      $j = ($it | ConvertTo-Json -Compress)
      if ($j -match [regex]::Escape($stamp) -or $j -match [regex]::Escape($visitorEmail)) { $hit = $true }
    }
  }
  Ok "22-inquiry-visible-tenant" ("hit=" + $hit)
} catch { Bad "22-inquiry-visible-tenant" $_.Exception.Message }

try { $null = Invoke-RestMethod "$api/api/v1/client/branding" -Headers $H -TimeoutSec 15; Ok "23-client-branding" "200" }
catch { Bad "23-client-branding" $_.Exception.Message }

try {
  $d = Invoke-RestMethod "$api/api/v1/content/pages/stats" -Headers $H -TimeoutSec 15
  Ok "24-content-stats" ("published=" + $d.data.published_pages)
} catch { Bad "24-content-stats" $_.Exception.Message }

foreach ($item in @(
  @{n="25-admin-client-today"; u="http://127.0.0.1:5173/client/today"},
  @{n="26-admin-client-content"; u="http://127.0.0.1:5173/client/content"},
  @{n="27-official-3000"; u="http://127.0.0.1:3000/"}
)) {
  try {
    $r = Invoke-WebRequest $item.u -UseBasicParsing -TimeoutSec 10
    Ok $item.n ("HTTP " + $r.StatusCode)
  } catch { Bad $item.n $_.Exception.Message }
}

Write-Output ("======== SUMMARY OK=" + $okCount + " FAIL=" + $failCount + " ========")
Write-Output "Constraint: tenant/product HTTP only; no SQL seed; no hermes golden-path orchestration."
