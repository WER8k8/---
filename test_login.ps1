$body = '{"username":"admin","password":"admin123"}'
$r = Invoke-RestMethod -Uri 'http://127.0.0.1:5173/api/v1/admin-bff/auth/login' -Method POST -ContentType 'application/json' -Body $body -TimeoutSec 15
Write-Host "code: $($r.code)"
Write-Host "accessToken length: $($r.data.accessToken.Length)"
