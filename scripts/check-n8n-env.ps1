$loginBody = @{username_or_email='admin';password='admin123'} | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/auth/login' -Method POST -Body $loginBody -ContentType 'application/json'
$token = $loginResp.data.access_token
$headers = @{Authorization="Bearer $token"}

$resp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/hermes/ops/command-center?refresh=true' -Method Get -Headers $headers

Write-Host "n8n configured: $($resp.data.integrations.n8n.configured)"
Write-Host "n8n webhook_path: $($resp.data.integrations.n8n.webhook_path)"

$envResp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/admin/system/env' -Method Get -Headers $headers -ErrorAction SilentlyContinue
if ($envResp) {
    Write-Host "`nEnv check response received"
}