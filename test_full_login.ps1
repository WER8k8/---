Write-Host "=== 1. 测试后端直接登录 ==="
try {
    $body = '{"username_or_email":"admin","password":"admin123"}'
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15
    Write-Host "Direct login: code=$($r.code)"
} catch {
    Write-Host "Direct login FAILED: $_"
}

Write-Host "`n=== 2. 测试 BFF 登录 ==="
try {
    $body2 = '{"username":"admin","password":"admin123"}'
    $r2 = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body2 -TimeoutSec 15
    Write-Host "BFF login: code=$($r2.code)"
} catch {
    Write-Host "BFF login FAILED: $_"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        Write-Host "Response body: $($reader.ReadToEnd())"
    }
}

Write-Host "`n=== 3. 测试前端代理登录 ==="
try {
    $body3 = '{"username":"admin","password":"admin123"}'
    $r3 = Invoke-RestMethod -Uri "http://127.0.0.1:5173/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body3 -TimeoutSec 15
    Write-Host "Proxy login: code=$($r3.code)"
} catch {
    Write-Host "Proxy login FAILED: $_"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        Write-Host "Response body: $($reader.ReadToEnd())"
    }
}
