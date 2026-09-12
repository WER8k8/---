$loginBody = @{username_or_email='admin';password='admin123'} | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/auth/login' -Method POST -Body $loginBody -ContentType 'application/json'
$token = $loginResp.data.access_token
$headers = @{Authorization="Bearer $token"}

$resp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/hermes/ops/command-center?refresh=true' -Method Get -Headers $headers

Write-Host "=== integrations.mem0 ==="
$resp.data.integrations.mem0 | ConvertTo-Json

Write-Host "`n=== integrations.posthog ==="
$resp.data.integrations.posthog | ConvertTo-Json

Write-Host "`n=== integrations.n8n ==="
$resp.data.integrations.n8n | ConvertTo-Json

Write-Host "`n=== integrations.deerflow_sidecar ==="
$resp.data.integrations.deerflow_sidecar | ConvertTo-Json