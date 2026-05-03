# MCP Configuration Manager - Production Version
# Author: Super Architecture Commander
# Version: 1.0.0

param(
    [string]$Action = "Status",
    [string]$ServerName,
    [string]$Config,
    [switch]$Force
)

$MCP_CONFIG_PATH = "$env:APPDATA\Lingma\SharedClientCache\mcp.json"
$BACKUP_DIR = "$env:APPDATA\Lingma\SharedClientCache\mcp-backups"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    switch ($Level) {
        "INFO"    { Write-Host "[$timestamp] [INFO] $Message" -ForegroundColor Cyan }
        "SUCCESS" { Write-Host "[$timestamp] [SUCCESS] $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "[$timestamp] [WARNING] $Message" -ForegroundColor Yellow }
        "ERROR"   { Write-Host "[$timestamp] [ERROR] $Message" -ForegroundColor Red }
    }
}

function Backup-Config {
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupFile = Join-Path $BACKUP_DIR "mcp-backup-$timestamp.json"
    Copy-Item $MCP_CONFIG_PATH $backupFile -Force
    Write-Log "Backup created: $backupFile" "INFO"
    
    # Keep only last 10 backups
    $backups = Get-ChildItem $BACKUP_DIR -Filter "mcp-backup-*.json" | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt 10) {
        $backups | Select-Object -Skip 10 | Remove-Item -Force
    }
}

function Read-Config {
    try {
        $config = Get-Content $MCP_CONFIG_PATH -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Log "Configuration loaded successfully" "SUCCESS"
        return $config
    } catch {
        Write-Log "Failed to load configuration: $_" "ERROR"
        return $null
    }
}

function Save-Config {
    param([object]$Config)
    try {
        Backup-Config
        $jsonOutput = $Config | ConvertTo-Json -Depth 20
        $jsonOutput | Set-Content $MCP_CONFIG_PATH -Encoding UTF8 -NoNewline
        Write-Log "Configuration saved successfully" "SUCCESS"
        return $true
    } catch {
        Write-Log "Failed to save configuration: $_" "ERROR"
        return $false
    }
}

function Add-Server {
    param([string]$Name, [string]$ConfigJson)
    Write-Log "Adding MCP Server: $Name" "INFO"
    
    $config = Read-Config
    if (-not $config) { return }
    
    if ($config.mcpServers.PSObject.Properties.Name -contains $Name) {
        if (-not $Force) {
            Write-Log "Server '$Name' already exists. Use -Force to overwrite." "WARNING"
            return
        }
        Write-Log "Overwriting existing server: $Name" "WARNING"
    }
    
    try {
        $newConfig = $ConfigJson | ConvertFrom-Json
    } catch {
        Write-Log "Invalid JSON configuration: $_" "ERROR"
        return
    }
    
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name $Name -Value $newConfig -Force
    
    if (Save-Config $config) {
        Write-Log "Server '$Name' added successfully" "SUCCESS"
    }
}

function Remove-Server {
    param([string]$Name)
    Write-Log "Removing MCP Server: $Name" "INFO"
    
    $config = Read-Config
    if (-not $config) { return }
    
    if (-not ($config.mcpServers.PSObject.Properties.Name -contains $Name)) {
        Write-Log "Server '$Name' does not exist" "WARNING"
        return
    }
    
    $config.mcpServers.PSObject.Properties.Remove($Name)
    
    if (Save-Config $config) {
        Write-Log "Server '$Name' removed successfully" "SUCCESS"
    }
}

function List-Servers {
    Write-Log "Listing MCP Servers..." "INFO"
    
    $config = Read-Config
    if (-not $config) { return }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  MCP Servers Configuration" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $servers = $config.mcpServers.PSObject.Properties.Name
    Write-Host "Total: $($servers.Count) servers" -ForegroundColor Yellow
    Write-Host ""
    
    $index = 1
    foreach ($serverName in $servers) {
        $server = $config.mcpServers.$serverName
        Write-Host "[$index] $serverName" -ForegroundColor Green
        
        if ($server.command) {
            Write-Host "    Type: Command" -ForegroundColor Gray
            Write-Host "    Command: $($server.command)" -ForegroundColor Gray
        }
        if ($server.url) {
            Write-Host "    Type: URL" -ForegroundColor Gray
            Write-Host "    URL: $($server.url)" -ForegroundColor Gray
        }
        if ($server.args) {
            Write-Host "    Args: $($server.args -join ' ')" -ForegroundColor Gray
        }
        if ($server.env) {
            $envVars = $server.env.PSObject.Properties.Name
            if ($envVars.Count -gt 0) {
                Write-Host "    Env: $($envVars -join ', ')" -ForegroundColor Gray
            }
        }
        Write-Host ""
        $index++
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Status {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  MCP Configuration Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Config File: $MCP_CONFIG_PATH" -ForegroundColor Yellow
    if (Test-Path $MCP_CONFIG_PATH) {
        Write-Host "Status: EXISTS" -ForegroundColor Green
        $fileInfo = Get-Item $MCP_CONFIG_PATH
        Write-Host "Size: $($fileInfo.Length) bytes" -ForegroundColor Gray
        Write-Host "Modified: $($fileInfo.LastWriteTime)" -ForegroundColor Gray
    } else {
        Write-Host "Status: NOT FOUND" -ForegroundColor Red
    }
    Write-Host ""
    
    Write-Host "Backup Directory: $BACKUP_DIR" -ForegroundColor Yellow
    if (Test-Path $BACKUP_DIR) {
        $backupCount = (Get-ChildItem $BACKUP_DIR -Filter "mcp-backup-*.json").Count
        Write-Host "Status: EXISTS ($backupCount backups)" -ForegroundColor Green
    } else {
        Write-Host "Status: NOT FOUND" -ForegroundColor Yellow
    }
    Write-Host ""
    
    $config = Read-Config
    if ($config) {
        $serverCount = $config.mcpServers.PSObject.Properties.Name.Count
        Write-Host "Configured Servers: $serverCount" -ForegroundColor Green
        Write-Host ""
        List-Servers
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Main execution
Write-Host ""
Write-Log "MCP Configuration Manager v1.0.0" "INFO"
Write-Log "Action: $Action" "INFO"

switch ($Action) {
    "Add" {
        if (-not $ServerName -or -not $Config) {
            Write-Log "Error: Add requires -ServerName and -Config parameters" "ERROR"
            exit 1
        }
        Add-Server -Name $ServerName -ConfigJson $Config
    }
    "Remove" {
        if (-not $ServerName) {
            Write-Log "Error: Remove requires -ServerName parameter" "ERROR"
            exit 1
        }
        Remove-Server -Name $ServerName
    }
    "List" {
        List-Servers
    }
    "Status" {
        Show-Status
    }
    "Backup" {
        Backup-Config
    }
    default {
        Write-Log "Unknown action: $Action" "ERROR"
        exit 1
    }
}

Write-Log "Operation completed" "SUCCESS"
Write-Host ""
