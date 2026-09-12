$body = '{"username":"admin","password":"admin123"}'
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body
$response | ConvertTo-Json