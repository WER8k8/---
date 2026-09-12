# Start NVIDIA->Cursor local proxy
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"
$script = Join-Path $PSScriptRoot "nvidia-cursor-proxy.py"

if (-not (Test-Path $py)) {
    throw "backend venv not found"
}

Write-Host "Proxy: http://127.0.0.1:8765/v1"
Write-Host "Cursor Base URL -> http://127.0.0.1:8765/v1"
Write-Host "Model: gpt-4o (Mistral 675B) | gpt-4o-mini (DeepSeek Flash)"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $py $script
