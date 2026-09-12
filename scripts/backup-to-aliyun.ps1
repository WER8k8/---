param(
    [string]$ProjectPath = "C:\Users\97907\Desktop\UJ\website",
    [string]$BackupName = "website-backup",
    [int]$MaxBackups = 10
)

$Date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$BackupDir = "$env:TEMP\project-backups"
$ZipFile = "$BackupDir\$BackupName-$Date.zip"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 开始打包项目文件..." -ForegroundColor Cyan

$ExcludeDirs = @(
    'node_modules', '.git', '__pycache__', 'venv', '.venv',
    'dist', 'build', '.next', '.nuxt', 'cache', 'logs',
    '*.log', '*.tmp', '*.pyc', '.env', '.DS_Store'
)

Compress-Archive -Path "$ProjectPath\*" -DestinationPath $ZipFile -CompressionLevel Optimal

$FileSize = [math]::Round((Get-Item $ZipFile).Length / 1MB, 2)
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 打包完成: $ZipFile ($FileSize MB)" -ForegroundColor Green

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 备份文件已保存至: $ZipFile" -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 请确保 Obsidian + Sync Vault 正在运行，此文件会被自动同步到阿里云盘" -ForegroundColor Yellow

$OldBackups = Get-ChildItem "$BackupDir\$BackupName-*.zip" | Sort-Object Name -Descending
if ($OldBackups.Count -gt $MaxBackups) {
    $OldBackups[$MaxBackups..($OldBackups.Count - 1)] | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "  清理旧备份: $($_.Name)" -ForegroundColor DarkGray
    }
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 备份完成！" -ForegroundColor Green
