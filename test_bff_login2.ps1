$body = '{"username":"admin","password":"admin123"}'
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/admin-bff/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "ERROR: $_"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody"
    }
}
