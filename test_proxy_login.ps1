$body = '{"username":"admin","password":"admin123"}'
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:5173/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_"
    $_.Exception.Response.StatusCode.value__
}