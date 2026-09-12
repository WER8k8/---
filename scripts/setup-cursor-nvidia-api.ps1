# 将 NVIDIA NIM API 写入 Cursor 本地配置（需先完全退出 Cursor）
# 用法:
#   powershell -File scripts/setup-cursor-nvidia-api.ps1
#   powershell -File scripts/setup-cursor-nvidia-api.ps1 -ApiKey "nvapi-你的完整密钥"

param(
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonScript = Join-Path $PSScriptRoot "setup-cursor-nvidia-api.py"

$cursorProcs = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue
if ($cursorProcs) {
    Write-Host ""
    Write-Host "检测到 Cursor 正在运行（进程数: $($cursorProcs.Count)）。" -ForegroundColor Yellow
    Write-Host "请先完全退出 Cursor（文件 -> 退出，或托盘右键退出），否则配置会被内存状态覆盖。" -ForegroundColor Yellow
    Write-Host ""
    $answer = Read-Host "是否现在强制结束 Cursor 并继续配置? (y/N)"
    if ($answer -ne "y" -and $answer -ne "Y") {
        Write-Host "已取消。请手动退出 Cursor 后重新运行本脚本。" -ForegroundColor Cyan
        exit 1
    }
    $cursorProcs | Stop-Process -Force
    Start-Sleep -Seconds 2
}

if (-not (Test-Path $pythonScript)) {
    throw "找不到脚本: $pythonScript"
}

if ($ApiKey) {
    python $pythonScript $ApiKey
} else {
    python $pythonScript
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "下一步:" -ForegroundColor Green
Write-Host "1. 重新打开 Cursor"
Write-Host "2. Settings -> Models，确认 OpenAI Base URL 为 https://integrate.api.nvidia.com/v1"
Write-Host "3. 聊天框模型下拉选 meta/llama-3.1-70b-instruct（或其它已添加的 NVIDIA 模型）"
Write-Host "4. 普通 Ask 模式测试；Agent 模式仍可能走 Cursor 内置模型"
Write-Host ""
Write-Host "若你刚在 NVIDIA 生成了新 Key，请用 -ApiKey 参数传入完整 nvapi- 密钥。"
