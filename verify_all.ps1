Write-Host "=== 后端健康检查 ==="
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 5
    Write-Host "Health: $($r.status)"
} catch { Write-Host "Health FAILED: $_" }

Write-Host "`n=== BFF 登录测试 ==="
try {
    $body = '{"username":"admin","password":"admin123"}'
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15
    Write-Host "BFF Login: code=$($r.code), accessToken length=$($r.data.accessToken.Length)"
} catch { Write-Host "BFF Login FAILED: $_" }

Write-Host "`n=== 前端代理登录测试 ==="
try {
    $body = '{"username":"admin","password":"admin123"}'
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:5173/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15
    Write-Host "Proxy Login: code=$($r.code), accessToken length=$($r.data.accessToken.Length)"
} catch { Write-Host "Proxy Login FAILED: $_" }

Write-Host "`n=== BFF user-info 测试 (需要 token) ==="
try {
    $body = '{"username":"admin","password":"admin123"}'
    $login = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15
    $token = $login.data.accessToken
    $headers = @{ "Authorization" = "Bearer $token" }
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/user/info" -Headers $headers -TimeoutSec 15
    Write-Host "User Info: code=$($r.code), username=$($r.data.username)"
} catch { Write-Host "User Info FAILED: $_" }
