# COMP-02 品牌禁词抽检
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    python scripts/brand-guard-audit.py
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
