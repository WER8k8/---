Write-Output "=== Strix 环境检查 ==="
Write-Output ""

Write-Output "1. 检查 Docker..."
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Output "   Docker Desktop 路径存在"
} else {
    Write-Output "   Docker Desktop 路径不存在"
}

Write-Output ""
Write-Output "2. 检查 Docker CLI..."
try {
    docker --version
    Write-Output "   Docker CLI 可用"
} catch {
    Write-Output "   Docker CLI 不可用"
}

Write-Output ""
Write-Output "3. 检查 Docker 服务..."
Get-Service *docker* -ErrorAction SilentlyContinue | Select-Object Name, Status

Write-Output ""
Write-Output "4. 检查 WSL..."
wsl --list --verbose 2>&1 | Select-Object -First 5

Write-Output ""
Write-Output "5. 检查 Strix..."
$env:Path = "C:\Users\Administrator.WIN-36O2UQRI3U1\strix\.venv\Scripts;" + $env:Path
try {
    strix --version
    Write-Output "   Strix CLI 可用"
} catch {
    Write-Output "   Strix CLI 不可用: $_"
}