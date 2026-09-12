cd C:\Users\Administrator.WIN-36O2UQRI3U1\strix
Write-Output "=== 恢复文件 ==="
git checkout HEAD -- strix/tools/reporting/tool.py
Write-Output ""
Write-Output "=== 验证文件 ==="
Test-Path "C:\Users\Administrator.WIN-36O2UQRI3U1\strix\strix\tools\reporting\tool.py"
Write-Output ""
Write-Output "=== 立即运行 strix ==="
$env:Path = "C:\Users\Administrator.WIN-36O2UQRI3U1\strix\.venv\Scripts;" + $env:Path
strix --version