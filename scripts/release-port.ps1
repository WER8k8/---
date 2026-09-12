# ============================================================
# Port Occupancy Detection and Release Script
# Function: Detect and release port 5173
# ============================================================

param(
    [int]$Port = 5173,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

function Write-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "       Port Occupancy Detection and Release Tool v1.0" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Get-PortProcesses {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

    if (-not $connections) {
        return @()
    }

    $processes = @()
    foreach ($conn in $connections) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            $processes += [PSCustomObject]@{
                PID         = $proc.Id
                ProcessName = $proc.ProcessName
                LocalPort   = $conn.LocalAddress + ":" + $conn.LocalPort
                State       = $conn.State
                Path        = $proc.Path
            }
        }
    }

    return $processes | Sort-Object PID -Unique
}

function Show-ProcessInfo {
    param($Processes)

    Write-Host "Processes occupying port $Port :" -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("  {0,-10} {1,-25} {2,-30}" -f "PID", "Process Name", "Path") -ForegroundColor White
    Write-Host ("  {0,-10} {1,-25} {2,-30}" -f "---", "-----------", "----") -ForegroundColor Gray

    foreach ($p in $Processes) {
        $shortPath = if ($p.Path) { (Split-Path $p.Path -Leaf) } else { "(none)" }
        Write-Host ("  {0,-10} {1,-25} {2,-30}" -f $p.PID, $p.ProcessName, $shortPath) -ForegroundColor White
    }
    Write-Host ""
}

function Stop-ProcessSafely {
    param(
        [int]$ProcessId,
        [string]$ProcessName
    )

    try {
        $proc = Get-Process -Id $ProcessId -ErrorAction Stop
        $procName = $proc.ProcessName

        Write-Host "  [TERMINATING] PID: $ProcessId | Process: $procName" -ForegroundColor Yellow

        Stop-Process -Id $ProcessId -Force -ErrorAction Stop

        Start-Sleep -Milliseconds 500
        $verify = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue

        if ($verify) {
            Write-Host "    [FAILED] Process still running..." -ForegroundColor Red
            return $false
        } else {
            Write-Host "    [SUCCESS] Process terminated" -ForegroundColor Green
            return $true
        }
    }
    catch [System.InvalidOperationException] {
        Write-Host "    [SKIPPED] Process already exited" -ForegroundColor Green
        return $true
    }
    catch {
        if ($_.Exception.Message -match "Access") {
            Write-Host "    [PERMISSION DENIED] Cannot terminate PID $ProcessId - Admin rights required" -ForegroundColor Red
        } else {
            Write-Host "    [ERROR] $($_.Exception.Message)" -ForegroundColor Red
        }
        return $false
    }
}

# ========== MAIN ==========
Write-Banner

Write-Host "Checking port $Port occupancy..." -ForegroundColor Gray

$processes = Get-PortProcesses -Port $Port

if ($processes.Count -eq 0) {
    Write-Host "[OK] Port $Port is not occupied" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "[FOUND] Port $Port is occupied by $($processes.Count) process(es)" -ForegroundColor Yellow
Write-Host ""

Show-ProcessInfo -Processes $processes

if ($DryRun) {
    Write-Host "[DryRun] Process info displayed only, no termination will be performed" -ForegroundColor Cyan
    exit 0
}

# Confirm operation
if (-not $Force) {
    Write-Host ""
    Write-Host "WARNING: The following processes will be forcefully terminated!" -ForegroundColor Red
    Write-Host "Press 'Y' to confirm, 'A' for all, 'N' to cancel: " -NoNewline -ForegroundColor Red
    $response = Read-Host

    if ($response -ne 'Y' -and $response -ne 'A') {
        Write-Host "[CANCELLED] Operation aborted" -ForegroundColor Gray
        exit 0
    }

    if ($response -eq 'A') {
        $Force = $true
    }
}

Write-Host ""
Write-Host "Starting process termination..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0
$skipCount = 0

foreach ($p in $processes) {
    $result = Stop-ProcessSafely -ProcessId $p.PID -ProcessName $p.ProcessName

    if ($result -eq $true) {
        $successCount++
    } elseif ($result -eq $false) {
        $failCount++
    } else {
        $skipCount++
    }
}

# Final verification
Write-Host ""
Write-Host "Verifying port $Port status..." -ForegroundColor Gray
Start-Sleep -Seconds 1
$remaining = Get-PortProcesses -Port $Port

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SUMMARY:" -ForegroundColor White
Write-Host "  Successfully terminated: $successCount" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "  Failed to terminate: $failCount" -ForegroundColor Red
}
if ($skipCount -gt 0) {
    Write-Host "  Skipped: $skipCount" -ForegroundColor Yellow
}
Write-Host ""

if ($remaining.Count -eq 0) {
    Write-Host "[COMPLETE] Port $Port has been released and is ready for use" -ForegroundColor Green
} else {
    Write-Host "[WARNING] $($remaining.Count) process(es) still occupying port $Port" -ForegroundColor Red
    Show-ProcessInfo -Processes $remaining

    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        Write-Host ""
        Write-Host "NOTE: Current session does not have administrator privileges." -ForegroundColor Yellow
        Write-Host "Suggestion: Run this script as Administrator" -ForegroundColor Yellow
        Write-Host "Method: Right-click PowerShell -> 'Run as administrator'" -ForegroundColor Yellow
    }
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
