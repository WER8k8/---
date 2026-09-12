# Night unattended dev gate + morning handoff scaffold
# Usage: powershell -ExecutionPolicy Bypass -File scripts/night-autodev.ps1

param(
    [switch]$FullPytest,
    [switch]$SkipPytest
)

$ErrorActionPreference = "Stop"
# NativeCommandError from python stderr is non-fatal for gate script
$Root = Split-Path -Parent $PSScriptRoot
$Date = Get-Date -Format "yyyy-MM-dd"
$OutDir = Join-Path (Join-Path $Root ".ao-output") ("night-autodev-" + $Date)
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Write-Log($msg) {
    $line = "[" + (Get-Date -Format "HH:mm:ss") + "] " + $msg
    Add-Content -Path (Join-Path $OutDir "run.log") -Value $line
    Write-Host $line
}

Write-Log ("night-autodev start root=" + $Root)

$QueuePath = Join-Path $Root "docs\出海计\night-autodev-queue.yaml"
Copy-Item $QueuePath (Join-Path $OutDir "queue.snapshot.yaml") -Force -ErrorAction SilentlyContinue

$PyResults = @()
if (-not $SkipPytest) {
    Push-Location (Join-Path $Root "backend")
    $suites = @(
        "tests/unit/test_commercial_os_flywheel.py",
        "tests/unit/test_accio_sales.py"
    )
    if ($FullPytest) {
        $suites = @("tests/unit")
    }
    foreach ($s in $suites) {
        Write-Log ("pytest " + $s)
        $out = & python -m pytest $s -q --tb=line 2>&1 | Out-String
        $PyResults += ("### " + $s + "`n" + $out)
        if ($LASTEXITCODE -ne 0) {
            Write-Log ("pytest FAILED " + $s + " exit=" + $LASTEXITCODE)
        }
    }
    Pop-Location
}

$CheckScript = Join-Path $Root "scripts\check_mounted_routes.py"
if (Test-Path $CheckScript) {
    Write-Log "check_mounted_routes"
    Push-Location $Root
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $RouteCheck = cmd /c "python `"$CheckScript`" 2>&1"
    $rc = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    Pop-Location
    $PyResults += ("### check_mounted_routes (exit=" + $rc + ")`n" + $RouteCheck)
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$TemplatePath = Join-Path $PSScriptRoot "templates\night-agent-prompt.md"
$AgentPrompt = Get-Content $TemplatePath -Raw -Encoding UTF8
$AgentPrompt = $AgentPrompt.Replace("{{OUT_DIR}}", $OutDir)
$AgentPrompt = $AgentPrompt.Replace("{{QUEUE_PATH}}", $QueuePath)
$AgentPrompt = $AgentPrompt.Replace("{{STAMP}}", $Stamp)
$AgentPrompt | Set-Content -Path (Join-Path $OutDir "AGENT_PROMPT.md") -Encoding UTF8

$GateLines = @(
    ("# Night gate report - " + $Date),
    "",
    "## pytest",
    ($PyResults -join "`n`n"),
    "",
    "## artifacts",
    "- queue.snapshot.yaml",
    "- AGENT_PROMPT.md",
    "- workflows/night-autodev-flywheel.yaml",
    "",
    "## next",
    "1. Cursor Agent: paste AGENT_PROMPT.md",
    "2. Morning: read MORNING.md in this folder"
)
$GateLines | Set-Content -Path (Join-Path $OutDir "GATE_REPORT.md") -Encoding UTF8

Write-Log ("done out=" + $OutDir)
Write-Host ""
Write-Host ("Output: " + $OutDir)
Write-Host ("Agent prompt: " + (Join-Path $OutDir "AGENT_PROMPT.md"))
