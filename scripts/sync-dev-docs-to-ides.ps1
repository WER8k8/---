# Sync dev progress + config index to IDE mirrors + desktop KB
# Source repo: 上线网站 (NOT website CodeBuddy)
# powershell -ExecutionPolicy Bypass -File scripts/sync-dev-docs-to-ides.ps1

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "[1/4] Refresh module-progress snapshot..."
python scripts/module_progress.py | Out-Null

$MirrorFiles = @(
    'docs\多IDE开发进度与配置索引.md',
    'docs\IDE-开发交接记录.md',
    'docs\module-progress-latest.txt',
    'docs\未完成开发任务表.md',
    'docs\进度看板.md',
    'docs\SOURCE-REPO.md'
)

$Targets = @(
    @{ Dir = '.lingma\rules'; Name = '开发进度与配置同步.md' },
    @{ Dir = '.trae'; Name = 'DEV_PROGRESS_SYNC.md' }
)

Write-Host "[2/4] Mirror to local IDE folders (under dev repo)..."
foreach ($t in $Targets) {
    $destDir = Join-Path $RepoRoot $t.Dir
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    }
    $body = @(
        '# 开发进度与配置（自动同步）',
        '',
        "> 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        '> 开发源码仓: Desktop/上线网站（CodeBuddy 轻量完整复制）',
        '> 请勿手改本文件；请改 docs/ 后重新运行 scripts/sync-dev-docs-to-ides.ps1',
        '',
        '完整索引见: docs/多IDE开发进度与配置索引.md',
        ''
    ) -join "`n"
    $idx = Join-Path $RepoRoot 'docs\多IDE开发进度与配置索引.md'
    if (Test-Path $idx) {
        $body += (Get-Content -Path $idx -Raw -Encoding UTF8)
    }
    $out = Join-Path $destDir $t.Name
    Set-Content -Path $out -Value $body -Encoding UTF8
    Write-Host "  -> $out"
}

Write-Host '[3/4] Copy key docs into .lingma/rules (snapshots)...'
$lingmaRules = Join-Path $RepoRoot '.lingma\rules'
if (-not (Test-Path $lingmaRules)) {
    New-Item -ItemType Directory -Force -Path $lingmaRules | Out-Null
}
foreach ($rel in $MirrorFiles) {
    $src = Join-Path $RepoRoot $rel
    if (Test-Path $src) {
        $base = Split-Path $rel -Leaf
        Copy-Item -Path $src -Destination (Join-Path $lingmaRules $base) -Force
    }
}

Write-Host '[4/4] Desktop knowledge base (出海计)...'
& (Join-Path $RepoRoot 'scripts\sync-to-chuhaiji-kb.ps1')

Write-Host 'Done. Dev source = 上线网站. CodeBuddy = archive only.'
