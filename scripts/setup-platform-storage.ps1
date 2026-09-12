# 平台产品图存储 — 七牛 / R2 一次性开通向导（运维用）
# 用法:
#   powershell -File scripts/setup-platform-storage.ps1
#   powershell -File scripts/setup-platform-storage.ps1 -EnvFile backend\config\dev\.env
#   powershell -File scripts/setup-platform-storage.ps1 -EnvFile deploy\production\.env -SkipPrompt
#   powershell -File scripts/setup-platform-storage.ps1 -RemoteHost user@1.2.3.4 -RemoteEnvPath /opt/youding/.env.prod
#
# 说明: 七牛注册与实名认证必须人工完成；本脚本负责验密钥、写 .env、远程合并、上传探测。

param(
    [string]$EnvFile = "",
    [switch]$SkipPrompt,
    [switch]$QiniuOnly,
    [switch]$R2Only,
    [string]$RemoteHost = $env:DEPLOY_HOST,
    [string]$RemoteEnvPath = "/opt/youding/.env.prod"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $Root "backend"
$Probe = Join-Path $Root "scripts\probe-platform-storage.py"

try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Console]::OutputEncoding
} catch { }

if (-not $EnvFile) {
    $EnvFile = Join-Path $Backend "config\dev\.env"
}
$EnvFile = Join-Path $Root ($EnvFile -replace '/', '\')

function Read-SecureOrPlain {
    param([string]$Label, [string]$Default = "")
    if ($SkipPrompt -and $Default) { return $Default }
    if ($Default) {
        $ans = Read-Host "$Label [$Default]"
        if ([string]::IsNullOrWhiteSpace($ans)) { return $Default }
        return $ans.Trim()
    }
    return (Read-Host $Label).Trim()
}

function Set-EnvKey {
    param([string]$Path, [hashtable]$Pairs)
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $lines = @()
    if (Test-Path $Path) {
        $lines = Get-Content -Path $Path -Encoding UTF8
        $bak = "$Path.bak-$(Get-Date -Format yyyyMMddHHmmss)"
        Copy-Item -Force $Path $bak
        Write-Host "已备份: $bak" -ForegroundColor DarkGray
    }
    $keys = @($Pairs.Keys)
    $out = New-Object System.Collections.Generic.List[string]
    $seen = @{}
    foreach ($line in $lines) {
        $matched = $false
        foreach ($k in $keys) {
            if ($line -match "^\s*$([regex]::Escape($k))\s*=") {
                $out.Add("$k=$($Pairs[$k])")
                $seen[$k] = $true
                $matched = $true
                break
            }
        }
        if (-not $matched) { $out.Add($line) }
    }
    foreach ($k in $keys) {
        if (-not $seen[$k]) { $out.Add("$k=$($Pairs[$k])") }
    }
    $out | Set-Content -Path $Path -Encoding UTF8
}

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║  平台存储开通向导 · 七牛（国内）+ R2（海外）                  ║
║  客户开户无需注册七牛 — 仅平台运维执行一次                    ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "【人工步骤 — 无法自动化】" -ForegroundColor Yellow
Write-Host "  1. 打开 https://portal.qiniu.com/signup 注册（平台企业邮箱）"
Write-Host "  2. 完成实名认证: https://portal.qiniu.com/user/profile"
Write-Host "  3. 对象存储 → 新建 Bucket → 绑定 CDN 域名（HTTPS）"
Write-Host "  4. 密钥管理 → 创建 AK/SK: https://portal.qiniu.com/user/key"
Write-Host ""
Write-Host "详细图文: docs/PLATFORM-STORAGE-SETUP.md"
Write-Host ""

$qiniuPairs = @{}
$r2Pairs = @{}

if (-not $R2Only) {
    Write-Host "=== 七牛 QINIU_* ===" -ForegroundColor Cyan
    $qiniuPairs["QINIU_ACCESS_KEY"] = Read-SecureOrPlain "QINIU_ACCESS_KEY"
    $qiniuPairs["QINIU_SECRET_KEY"] = Read-SecureOrPlain "QINIU_SECRET_KEY"
    $qiniuPairs["QINIU_BUCKET"] = Read-SecureOrPlain "QINIU_BUCKET"
    $qiniuPairs["QINIU_PUBLIC_BASE_URL"] = Read-SecureOrPlain "QINIU_PUBLIC_BASE_URL (https://img.xxx.com)"
    $qiniuPairs["QINIU_UPLOAD_HOST"] = Read-SecureOrPlain "QINIU_UPLOAD_HOST" "https://upload.qiniup.com"
    $qiniuPairs["FILE_STORAGE_DEFAULT_REGION"] = Read-SecureOrPlain "FILE_STORAGE_DEFAULT_REGION" "cn"
}

if (-not $QiniuOnly) {
    Write-Host "`n=== Cloudflare R2 MEDIA_R2_*（可选，海外租户）===" -ForegroundColor Cyan
    $doR2 = if ($SkipPrompt) { $true } else { (Read-Host "是否现在配置 R2? (y/N)").Trim().ToLower() -eq "y" }
    if ($doR2) {
        $r2Pairs["MEDIA_R2_ACCOUNT_ID"] = Read-SecureOrPlain "MEDIA_R2_ACCOUNT_ID"
        $r2Pairs["MEDIA_R2_ACCESS_KEY_ID"] = Read-SecureOrPlain "MEDIA_R2_ACCESS_KEY_ID"
        $r2Pairs["MEDIA_R2_SECRET_ACCESS_KEY"] = Read-SecureOrPlain "MEDIA_R2_SECRET_ACCESS_KEY"
        $r2Pairs["MEDIA_R2_BUCKET"] = Read-SecureOrPlain "MEDIA_R2_BUCKET"
        $r2Pairs["MEDIA_R2_PUBLIC_BASE_URL"] = Read-SecureOrPlain "MEDIA_R2_PUBLIC_BASE_URL (可空)"
    }
}

Write-Host "`n=== 上传探测 ===" -ForegroundColor Cyan
$env:QINIU_ACCESS_KEY = $qiniuPairs["QINIU_ACCESS_KEY"]
$env:QINIU_SECRET_KEY = $qiniuPairs["QINIU_SECRET_KEY"]
$env:QINIU_BUCKET = $qiniuPairs["QINIU_BUCKET"]
$env:QINIU_PUBLIC_BASE_URL = $qiniuPairs["QINIU_PUBLIC_BASE_URL"]
$env:QINIU_UPLOAD_HOST = $qiniuPairs["QINIU_UPLOAD_HOST"]
$env:MEDIA_R2_ACCOUNT_ID = $r2Pairs["MEDIA_R2_ACCOUNT_ID"]
$env:MEDIA_R2_ACCESS_KEY_ID = $r2Pairs["MEDIA_R2_ACCESS_KEY_ID"]
$env:MEDIA_R2_SECRET_ACCESS_KEY = $r2Pairs["MEDIA_R2_SECRET_ACCESS_KEY"]
$env:MEDIA_R2_BUCKET = $r2Pairs["MEDIA_R2_BUCKET"]
$env:MEDIA_R2_PUBLIC_BASE_URL = $r2Pairs["MEDIA_R2_PUBLIC_BASE_URL"]

if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "setup-" + ("x" * 32) }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "setup-" + ("x" * 32) }

$target = if ($QiniuOnly) { "qiniu" } elseif ($R2Only) { "r2" } else { "all" }
Push-Location $Backend
python $Probe --target $target
$probeExit = $LASTEXITCODE
Pop-Location

if ($probeExit -ne 0) {
    Write-Host "`n探测未通过 — 未写入 .env。请核对密钥/Bucket/实名后再试。" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== 写入本地 env: $EnvFile ===" -ForegroundColor Cyan
$allPairs = @{}
foreach ($k in $qiniuPairs.Keys) { if ($qiniuPairs[$k]) { $allPairs[$k] = $qiniuPairs[$k] } }
foreach ($k in $r2Pairs.Keys) { if ($r2Pairs[$k]) { $allPairs[$k] = $r2Pairs[$k] } }
Set-EnvKey -Path $EnvFile -Pairs $allPairs
Write-Host "已更新 $EnvFile" -ForegroundColor Green

if ($RemoteHost) {
    Write-Host "`n=== 合并到远程 $RemoteHost`:$RemoteEnvPath ===" -ForegroundColor Cyan
    $tmp = Join-Path $env:TEMP "youding-storage-env-$(Get-Date -Format yyyyMMddHHmmss).snippet"
    @(
        "# appended by setup-platform-storage.ps1 $(Get-Date -Format o)"
    ) + ($allPairs.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) | Set-Content $tmp -Encoding UTF8
    scp $tmp "${RemoteHost}:/tmp/youding-storage-env.snippet"
    $remoteCmd = "ENV_FILE='$RemoteEnvPath'; touch `"`$ENV_FILE`"; cp `"`$ENV_FILE`" `"`${ENV_FILE}.bak-`$(date +%Y%m%d%H%M%S)`"; while IFS= read -r line; do key=`${line%%=*}; case `"`$key`" in QINIU_*|MEDIA_R2_*|FILE_STORAGE_DEFAULT_REGION) grep -v `"^`${key}=`" `"`$ENV_FILE`" > `"`${ENV_FILE}.tmp`" || true; mv `"`${ENV_FILE}.tmp`" `"`$ENV_FILE`";; esac; done < /tmp/youding-storage-env.snippet; cat /tmp/youding-storage-env.snippet >> `"`$ENV_FILE`"; rm -f /tmp/youding-storage-env.snippet; echo merged"
    ssh $RemoteHost $remoteCmd
    Remove-Item $tmp -ErrorAction SilentlyContinue
    Write-Host "远程 env 已合并。请 ssh 登录后重启 backend: docker compose restart backend" -ForegroundColor Green
}

Write-Host @"

完成。下一步:
  · 本地开发: 重启 backend (scripts/start-dev-admin.ps1)
  · 生产: 确认 .env.prod 已含 QINIU_* → 重启服务
  · 超管后台: 系统 → 存储开通 → 「验收当前配置」

"@ -ForegroundColor Green
