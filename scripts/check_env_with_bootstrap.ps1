$BackendDir = (Get-Location).Path + '\backend'
$DevEnvFile = Join-Path $BackendDir 'config\dev\.env'

Set-Location -LiteralPath $BackendDir
$env:PYTHONPATH = (Get-Location).Path

if (Test-Path -LiteralPath $DevEnvFile) {
  Write-Host "Loading env from: $DevEnvFile"
  Get-Content -LiteralPath $DevEnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
      $k = $matches[1].Trim()
      $v = $matches[2].Trim()
      if ($k) { 
        Set-Item -Path "Env:$k" -Value $v
        if ($k -match 'N8N|MEM0|POSTHOG|DEERFLOW') {
          Write-Host "  $k=$v"
        }
      }
    }
  }
}

Write-Host "`n=== Checking env vars ==="
Write-Host "N8N_WEBHOOK_SECRET: '$($env:N8N_WEBHOOK_SECRET)'"
Write-Host "MEM0_API_URL: '$($env:MEM0_API_URL)'"
Write-Host "POSTHOG_PROJECT_API_KEY: '$($env:POSTHOG_PROJECT_API_KEY)'"
Write-Host "DEERFLOW_SIDECAR_URL: '$($env:DEERFLOW_SIDECAR_URL)'"

Write-Host "`n=== Running Python check ==="
.\.venv\Scripts\python.exe ..\scripts\check_n8n_env_in_backend.py