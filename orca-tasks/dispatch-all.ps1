$ErrorActionPreference = "Continue"
$base = "C:/Users/Administrator/Documents/上线网站开发完成/上线网站.worktrees/agents-install-vscode-cline-deploy-strix"
$tasks = @("t01","t02","t03","t04","t05","t06","t07","t08","t09","t10","t11","t12","t13")

foreach ($t in $tasks) {
    $file = "$base/orca-tasks/${t}.md"
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        Write-Host "[$t] Brief loaded: $((($content.Length)/1024))KB"
    }
}
Write-Host "Ready to dispatch via orca terminal send"
