$envFile = Join-Path $PWD 'backend\config\dev\.env'

Write-Host "Loading from: $envFile"

Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -and $line[0] -ne '#' -and $line -match '=') {
        $parts = $line -split '=', 2
        $k = $parts[0].Trim()
        $v = $parts[1].Trim()
        if ($k) { 
            Set-Item -Path "Env:$k" -Value $v
            if ($k -match 'N8N|MEM0|POSTHOG|DEERFLOW') {
                Write-Host "SET: $k=$v"
            }
        }
    }
}

Write-Host ""
Write-Host "=== Final env vars ==="
Write-Host "N8N_WEBHOOK_SECRET: '$($env:N8N_WEBHOOK_SECRET)'"
Write-Host "MEM0_API_URL: '$($env:MEM0_API_URL)'"
Write-Host "POSTHOG_PROJECT_API_KEY: '$($env:POSTHOG_PROJECT_API_KEY)'"
Write-Host "DEERFLOW_SIDECAR_URL: '$($env:DEERFLOW_SIDECAR_URL)'"