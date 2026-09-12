# 克隆开源论坛参考仓到 _ref/（gitignore，仅供审计，不进送检包）
# 用法: powershell -File scripts/clone-forum-ref-repos.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RefDir = Join-Path $Root "_ref"
New-Item -ItemType Directory -Force -Path $RefDir | Out-Null

$repos = @(
    @{ Name = "answer"; Url = "https://github.com/apache/answer.git" },
    @{ Name = "flarum"; Url = "https://github.com/flarum/flarum.git" },
    @{ Name = "nodebb"; Url = "https://github.com/NodeBB/NodeBB.git" }
)

foreach ($r in $repos) {
    $dest = Join-Path $RefDir $r.Name
    if (Test-Path (Join-Path $dest ".git")) {
        Write-Host "SKIP $($r.Name) (exists)"
        continue
    }
    Write-Host "CLONE $($r.Name) ..."
    git clone --depth 1 $r.Url $dest
}

Write-Host "Done. Audit: docs/open-source-audit/16-forum-community-sidecar.md"
