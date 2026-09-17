# Export production bundle (website source only, no dev tools)
param(
    [string]$Destination = "C:\Users\97907\Desktop\上线网站"
)

$Source = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
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
$components = @('backend','frontend','seo-backend','seo-admin','docker','deploy','workers','charts')
$rootFiles = @(
    'docker-compose.yml','docker-compose.prod.yml','docker-compose.seo.yml',
    'Dockerfile','.env.example','.env.prod.example','DEPLOY.md','README.md',
    'deploy.ps1','deploy.sh','deploy.bat','POSTGRESQL_SETUP.md'
)
$deployScripts = @(
    'deploy-mvp-production.ps1','deploy.sh','check_env.py',
    'check_production_secrets.py','init_db.py','diagnose-and-fix.ps1',
    'check_users.py','backup-to-aliyun.ps1','export-production-bundle.ps1','sync-to-production.ps1','check-interactive-stubs.mjs'
)

Write-Host "Source: $Source"
Write-Host "Destination: $Destination"

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

foreach ($c in $components) {
    $from = Join-Path $Source $c
    $to = Join-Path $Destination $c
    if (Test-Path $from) {
        Write-Host "Copying $c ..."
        robocopy $from $to /E /IS /IT /NFL /NDL /NJH /NJS /nc /ns /np /XD $excludeDirs | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $rel (exit $LASTEXITCODE)" }
    }
}

foreach ($f in $rootFiles) {
    $from = Join-Path $Source $f
    if (Test-Path $from) { Copy-Item -Force $from (Join-Path $Destination $f) }
}

$scriptsDst = Join-Path $Destination 'scripts'
New-Item -ItemType Directory -Force -Path $scriptsDst | Out-Null
foreach ($s in $deployScripts) {
    $from = Join-Path $Source "scripts\$s"
    if (Test-Path $from) { Copy-Item -Force $from (Join-Path $scriptsDst $s) }
}

Get-ChildItem -Path $Destination -Recurse -Include '.env','.env.prod','.env.local' -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

$readmeSrc = Join-Path $Destination '上线说明.md'
if (-not (Test-Path $readmeSrc)) {
    Copy-Item -Force (Join-Path $Destination 'DEPLOY.md') $readmeSrc -ErrorAction SilentlyContinue
}

Write-Host "Done: $Destination"
