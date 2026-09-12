$env:Path = "C:\Users\Administrator.WIN-36O2UQRI3U1\strix\.venv\Scripts;" + $env:Path

Write-Output "=== 使用 Bandit 进行 Python 安全扫描 ==="
bandit -r backend -f json -o bandit_report.json -v 2>&1
Write-Output ""
Write-Output "=== Bandit 扫描完成 ==="

Write-Output ""
Write-Output "=== 使用 Ruff 进行安全扫描 ==="
ruff check backend --select=S --output-format=json > ruff_report.json 2>&1
Write-Output ""
Write-Output "=== Ruff 扫描完成 ==="

Write-Output ""
Write-Output "=== 显示 Bandit 报告摘要 ==="
Get-Content bandit_report.json | ConvertFrom-Json | Select-Object -ExpandProperty results | Select-Object severity, issue_text, filename, line_number | Format-Table -AutoSize