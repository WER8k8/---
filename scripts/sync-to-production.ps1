# Sync dev repo changes to production folder (C:\Users\97907\Desktop\上线网站)
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-production.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/sync-to-production.ps1 -Paths "frontend/admin/src/views/system-health"

param(
    [string]$Destination = "C:\Users\97907\Desktop\上线网站",
    [string]$Paths = ""
)

$Source = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PathList = @()
if ($Paths -and $Paths.Trim()) {
    $PathList = $Paths -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}
$excludeDirs = @(
    '.git','.vscode',
    '.pytest_cache','.uploads','.vs',
    '.ao-output','.artifacts','node_modules','.venv','venv','__pycache__',
    '.nuxt','.output','dist','build','coverage','.htmlcov',
    'backup_auto_20260505_133809','claude-desktop-zh-localization',
    'geo_analysis','geo_cache','knowledge_base','memory','prompt_lib',
    'results','screenshots','smart_agent_workflow','tests','tools',
    'mcp-server','uploads','v1.10.0','workflows','ai-engine'
)

function Sync-Tree {
    param([string]$From, [string]$To)
    if (-not (Test-Path $From)) { Write-Warning "Skip missing: $From"; return }
    New-Item -ItemType Directory -Force -Path (Split-Path $To -Parent) | Out-Null
    robocopy $From $To /E /IS /IT /NFL /NDL /NJH /NJS /nc /ns /np /XD $excludeDirs | Out-Null
}

if ($PathList.Count -eq 0) {
    & (Join-Path $PSScriptRoot "export-production-bundle.ps1") -Destination $Destination
    exit 0
}

Write-Host "Incremental sync to $Destination"
foreach ($rel in $PathList) {
    $from = Join-Path $Source $rel
    $to = Join-Path $Destination $rel
    if (Test-Path $from -PathType Leaf) {
        New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
        Copy-Item -Force $from $to
        Write-Host "  file: $rel"
    } else {
        Sync-Tree -From $from -To $to
        Write-Host "  dir:  $rel"
    }
}

Get-ChildItem -Path $Destination -Recurse -Include '.env','.env.prod','.env.local' -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Sync done: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
