# SEC-04：依赖漏洞扫描归档
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run-security-audit.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "docs\security-audit-latest.md"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$lines = @(
    "# 依赖安全审计（自动生成）",
    "",
    "> 生成时间：$ts",
    "",
    "## Python（backend）",
    ""
)

Push-Location (Join-Path $Root "backend")
$pipOut = pip audit 2>&1 | Out-String
$lines += "```text"
$lines += $pipOut.TrimEnd()
$lines += "```"
Pop-Location

$lines += @("", "## Node（frontend/admin）", "")
Push-Location (Join-Path $Root "frontend\admin")
if (Test-Path "package-lock.json") {
    $npmOut = npm audit --json 2>&1 | Out-String
    $lines += "```json"
    $lines += $npmOut.TrimEnd()
    $lines += "```"
} else {
    $lines += "_无 package-lock.json，跳过 npm audit_"
}
Pop-Location

$lines += @(
    "",
    "## 说明",
    "",
    "- 高危项需评估是否可升级主版本",
    "- 生产部署前建议与 `run_production_preflight.py` 一并执行",
    ""
)

$lines -join "`n" | Set-Content -Path $Out -Encoding UTF8
Write-Host "Wrote $Out"
