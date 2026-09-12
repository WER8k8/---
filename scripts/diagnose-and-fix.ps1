# Nuxt Dev Server Diagnostic Tool
param(
    [string]$TargetUrl = "http://localhost:5173",
    [string]$HostName = "localhost",
    [int]$Port = 5173,
    [switch]$AutoFix,
    [switch]$FullReset
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Nuxt Dev Server Diagnostic Tool" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Target: $TargetUrl" -ForegroundColor Blue
Write-Host "[INFO] Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Blue

$rootCauses = @()
$fixesApplied = @()

# STEP 1: DNS Resolution
Write-Host ""
Write-Host "--- STEP 1: Network Connectivity ---" -ForegroundColor Yellow
Write-Host "  Testing DNS resolution... " -NoNewline
try {
    $dnsResult = [System.Net.Dns]::GetHostAddresses($HostName)
    $ip = $dnsResult[0].ToString()
    Write-Host "OK - Resolved to $ip" -ForegroundColor Green
} catch {
    Write-Host "FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $rootCauses += "DNS resolution failed"
}

# STEP 2: Port Check
Write-Host ""
Write-Host "--- STEP 2: Port Availability ---" -ForegroundColor Yellow
Write-Host "  Checking port $Port... " -NoNewline
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if ($connections) {
    Write-Host "IN USE" -ForegroundColor Green
    $pids = @()
    foreach ($conn in $connections) {
        try {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "    PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor White
                $pids += $proc.Id
            }
        } catch {}
    }
    $nodeOnPort = $connections | Where-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName -eq "node" }
    if ($nodeOnPort) {
        Write-Host "    Nuxt server is running on port $Port" -ForegroundColor Green
    } else {
        Write-Host "    Non-Node process is using port $Port" -ForegroundColor Yellow
        $rootCauses += "Port $Port occupied by non-Nuxt process"
    }
} else {
    Write-Host "NOT LISTENING" -ForegroundColor Red
    $rootCauses += "Port $Port is not listening - server not running"
}

# STEP 3: Firewall Check
Write-Host ""
Write-Host "--- STEP 3: Firewall Status ---" -ForegroundColor Yellow
try {
    $firewall = Get-NetFirewallProfile
    $enabled = ($firewall | Where-Object { $_.Enabled }).Name -join ", "
    Write-Host "  Firewall profiles enabled: $enabled" -ForegroundColor White
} catch {
    Write-Host "  Cannot check firewall status" -ForegroundColor Yellow
}

# STEP 4: HTTP Test
Write-Host ""
Write-Host "--- STEP 4: HTTP Service Test ---" -ForegroundColor Yellow
Write-Host "  Testing connection to $TargetUrl... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri $TargetUrl -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "OK - Status $($response.StatusCode)" -ForegroundColor Green
} catch {
    $statusCode = "N/A"
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
    }
    Write-Host "FAILED - Status: $statusCode" -ForegroundColor Red
    $rootCauses += "HTTP service unreachable"
}

# STEP 5: Node.js Processes
Write-Host ""
Write-Host "--- STEP 5: Node.js Processes ---" -ForegroundColor Yellow
Write-Host "  Scanning Node.js processes... " -NoNewline
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    Write-Host "Found $($nodeProcs.Count)" -ForegroundColor Green
    foreach ($proc in $nodeProcs) {
        $memMB = [math]::Round($proc.WorkingSet64/1MB, 1)
        Write-Host "    PID $($proc.Id) - Memory: ${memMB}MB" -ForegroundColor White
    }
} else {
    Write-Host "None found" -ForegroundColor Yellow
}

# STEP 6: DNS Cache
Write-Host ""
Write-Host "--- STEP 6: DNS Cache ---" -ForegroundColor Yellow
Write-Host "  Checking DNS cache... " -NoNewline
$dnsCache = Get-DnsClientCache -Name $HostName -ErrorAction SilentlyContinue
if ($dnsCache) {
    Write-Host "Has entries" -ForegroundColor Yellow
    $rootCauses += "Stale DNS cache may exist"
} else {
    Write-Host "Clean" -ForegroundColor Green
}

# SUMMARY
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Diagnostic Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($rootCauses.Count -gt 0) {
    Write-Host ""
    Write-Host "ROOT CAUSES:" -ForegroundColor Red
    foreach ($cause in $rootCauses) {
        Write-Host "  * $cause" -ForegroundColor Red
    }
}

# AUTO-FIX
if ($AutoFix -or $FullReset) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Auto-Fix Mode" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan

    if ($FullReset) {
        Write-Host ""
        Write-Host "[Fix] Flushing DNS cache..." -ForegroundColor Yellow
        try {
            ipconfig /flushdns | Out-Null
            Write-Host "  DNS cache flushed" -ForegroundColor Green
            $fixesApplied += "DNS cache flushed"
        } catch {}

        Write-Host ""
        Write-Host "[Fix] Terminating Node.js processes..." -ForegroundColor Yellow
        $nodes = Get-Process -Name "node" -ErrorAction SilentlyContinue
        if ($nodes) {
            foreach ($n in $nodes) {
                try {
                    Stop-Process -Id $n.Id -Force
                    Write-Host "  Stopped PID $($n.Id)" -ForegroundColor Green
                    $fixesApplied += "Stopped PID $($n.Id)"
                } catch {}
            }
        }
    }
}

# FINAL RECOMMENDATIONS
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Recommendations" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($rootCauses.Count -eq 0) {
    Write-Host "[OK] No issues detected - server should be accessible" -ForegroundColor Green
} else {
    Write-Host "[ACTION] Run the following commands:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  cd frontend" -ForegroundColor Cyan
    Write-Host "  npx nuxt dev --port 5173" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use Full Reset mode:" -ForegroundColor Gray
    Write-Host "  .\diagnose-and-fix.ps1 -FullReset" -ForegroundColor Gray
}

if ($fixesApplied.Count -gt 0) {
    Write-Host ""
    Write-Host "Fixes applied:" -ForegroundColor Green
    foreach ($fix in $fixesApplied) {
        Write-Host "  + $fix" -ForegroundColor Green
    }
}

Write-Host ""
