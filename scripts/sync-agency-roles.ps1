# 全量同步 agency-orchestrator 角色库 + 官方 YAML 工作流到产品 data 目录
# 用法: powershell -File scripts/sync-agency-roles.ps1
# 可选: -Lang zh  （若 npm 包含 agency-agents-zh 则优先中文目录）

param(
    [ValidateSet("zh", "en", "auto")]
    [string]$Lang = "auto"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$DataRoot = Join-Path $Root "backend\app\data"
$RolesOut = Join-Path $DataRoot "agency_roles"
$WorkflowsOut = Join-Path $DataRoot "agency_workflows"
$ManifestPath = Join-Path $DataRoot "agency_manifest.json"
$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

Write-Host "Resolving agency-orchestrator package..."
$npxNull = npx -y agency-orchestrator --version 2>$null
$cacheDirs = Get-ChildItem "$env:LOCALAPPDATA\npm-cache\_npx" -Recurse -Directory -Filter "agency-orchestrator" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
$aoPkg = $cacheDirs | Select-Object -First 1
if (-not $aoPkg) {
    throw "agency-orchestrator not found. Run: npx -y agency-orchestrator roles"
}
$aoPath = $aoPkg.FullName
$version = (Get-Content (Join-Path $aoPath "package.json") -Raw | ConvertFrom-Json).version
Write-Host "Source: $aoPath (v$version)"

$agentsZh = Join-Path $aoPath "agency-agents-zh"
$agentsEn = Join-Path $aoPath "agency-agents"

# npm 包内通常只有 agency-agents；中文库需 ao init --lang zh 拉取
if (-not (Test-Path $agentsZh) -and ($Lang -eq "zh" -or $Lang -eq "auto")) {
    $staging = Join-Path $env:TEMP "youding-agency-agents-zh"
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    Write-Host "Downloading agency-agents-zh via ao init --lang zh ..."
    Push-Location $staging
    try {
        npx -y agency-orchestrator init --lang zh 2>&1 | Out-Null
        if (Test-Path (Join-Path $staging "agency-agents-zh")) {
            $agentsZh = Join-Path $staging "agency-agents-zh"
        }
    } finally {
        Pop-Location
    }
}

$agentsSrc = $agentsEn
if ($Lang -eq "zh" -and (Test-Path $agentsZh)) {
    $agentsSrc = $agentsZh
} elseif ($Lang -eq "auto" -and (Test-Path $agentsZh)) {
    $agentsSrc = $agentsZh
} elseif ($Lang -eq "en") {
    $agentsSrc = $agentsEn
}
Write-Host "Roles source: $agentsSrc"

$roleCategories = @(
    "academic", "design", "engineering", "finance", "game-development",
    "marketing", "paid-media", "product", "project-management", "sales",
    "spatial-computing", "specialized", "strategy", "support", "testing"
)

if (Test-Path $RolesOut) {
    Remove-Item $RolesOut -Recurse -Force
}
if (Test-Path $WorkflowsOut) {
    Remove-Item $WorkflowsOut -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $RolesOut | Out-Null
New-Item -ItemType Directory -Force -Path $WorkflowsOut | Out-Null

foreach ($cat in $roleCategories) {
    $srcCat = Join-Path $agentsSrc $cat
    if (-not (Test-Path $srcCat)) { continue }
    Copy-Item -Path $srcCat -Destination (Join-Path $RolesOut $cat) -Recurse -Force
}
$roleCount = (Get-ChildItem $RolesOut -Recurse -Filter *.md).Count

Copy-Item -Path (Join-Path $aoPath "workflows\*") -Destination $WorkflowsOut -Recurse -Force
$wfCount = (Get-ChildItem $WorkflowsOut -Recurse -Filter *.yaml).Count

# 产品定制 B2B GEO 工作流（优丁）
$b2bCandidates = @(
    (Join-Path $Root ".devstack\shangxian-website\workflows\geo-content-matrix-b2b.yaml"),
    (Join-Path $env:USERPROFILE ".devstack\shangxian-website\workflows\geo-content-matrix-b2b.yaml")
)
foreach ($b2b in $b2bCandidates) {
    if (Test-Path $b2b) {
        Copy-Item $b2b (Join-Path $WorkflowsOut "geo-content-matrix-b2b.yaml") -Force
        if (-not (Get-ChildItem $WorkflowsOut -Filter "geo-content-matrix-b2b.yaml")) { $wfCount++ }
        Write-Host "Added product workflow: geo-content-matrix-b2b.yaml"
        break
    }
}
$wfCount = (Get-ChildItem $WorkflowsOut -Recurse -Filter *.yaml).Count

$manifest = @{
    synced_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    source = "agency-orchestrator"
    package_version = $version
    package_path = $aoPath
    roles_dir = "agency_roles"
    workflows_dir = "agency_workflows"
    role_count = $roleCount
    workflow_count = $wfCount
    agents_source = Split-Path $agentsSrc -Leaf
    note = "Hermes Python DAG 消费；全量资产由 scripts/sync-agency-roles.ps1 刷新"
}
$json = $manifest | ConvertTo-Json -Depth 4 -Compress:$false
[System.IO.File]::WriteAllText($ManifestPath, $json, (New-Object System.Text.UTF8Encoding $false))

Write-Host "Normalizing role H1 titles from frontmatter..."
& $Py (Join-Path $Root "scripts\validate-agency-role-titles.py") --fix | Out-Host
Write-Host "Validating agency role titles..."
& $Py (Join-Path $Root "scripts\validate-agency-role-titles.py")
if ($LASTEXITCODE -ne 0) { throw "agency role title validation failed" }

Write-Host ""
Write-Host "Done: $roleCount roles -> $RolesOut"
Write-Host "Done: $wfCount workflows -> $WorkflowsOut"
Write-Host "Manifest: $ManifestPath"
