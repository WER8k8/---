$envFile = Join-Path $PWD 'backend\config\dev\.env'

Write-Host "Loading from: $envFile"
Write-Host "File exists: $(Test-Path $envFile)"

$lines = Get-Content -LiteralPath $envFile -Encoding UTF8

for ($i = 215; $i -le 225; $i++) {
    $line = $lines[$i]
    $lineNum = $i + 1
    Write-Host "Line ${lineNum}:"
    Write-Host "  Raw: '$line'"
    Write-Host "  Length: $($line.Length)"
    
    if ($line -match '^\s*([^#][^=]+)=(.*)$') {
        Write-Host "  MATCH: k='$($matches[1])', v='$($matches[2])'"
        if ($matches[1].Trim() -match 'N8N|MEM0|POSTHOG|DEERFLOW') {
            Write-Host "  >>> SET ENV: $($matches[1].Trim())=$($matches[2].Trim())"
            Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    } else {
        Write-Host "  NO MATCH"
    }
}

Write-Host ""
Write-Host "=== Final env vars ==="
Write-Host "N8N_WEBHOOK_SECRET: '$($env:N8N_WEBHOOK_SECRET)'"
Write-Host "MEM0_API_URL: '$($env:MEM0_API_URL)'"
Write-Host "POSTHOG_PROJECT_API_KEY: '$($env:POSTHOG_PROJECT_API_KEY)'"
Write-Host "DEERFLOW_SIDECAR_URL: '$($env:DEERFLOW_SIDECAR_URL)'"