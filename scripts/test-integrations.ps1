$loginBody = @{username_or_email='admin';password='admin123'} | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/auth/login' -Method POST -Body $loginBody -ContentType 'application/json'
$token = $loginResp.data.access_token
$headers = @{Authorization="Bearer $token"}
$resp = Invoke-RestMethod -Uri 'http://localhost:8001/api/v1/hermes/ops/command-center?refresh=true' -Method Get -Headers $headers
$resp | ConvertTo-Json -Depth 3