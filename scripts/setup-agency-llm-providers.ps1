# Hermes agency LLM — 本机/服务器探测与半自动安装
# 用法:
#   powershell -File scripts/setup-agency-llm-providers.ps1              # 探测
#   powershell -File scripts/setup-agency-llm-providers.ps1 -InstallCli # 仅 npm 全局 CLI（不含 OAuth）
#   powershell -File scripts/setup-agency-llm-providers.ps1 -StartOllama # 尝试启动 Ollama 并 pull 模型

param(
    [switch]$InstallCli,
    [switch]$StartOllama,
    [string]$OllamaModel = "llama3.1",
    [ValidateSet("dev", "server")]
    [string]$Target = "dev"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $Root "backend"

try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Console]::OutputEncoding
} catch { }

if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = "test-" + ("x" * 32) }
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "test-" + ("x" * 32) }

function Write-Plan {
    param([string]$TargetMode)
    Push-Location $Backend
    try {
        python -c "import json; from app.services.hermes.agency.provider_setup import build_setup_plan; print(json.dumps(build_setup_plan(target='$TargetMode'), ensure_ascii=False, indent=2))"
    } finally {
        Pop-Location
    }
}

Write-Host "=== 1. Provider 探测 ===" -ForegroundColor Cyan
Push-Location $Backend
python (Join-Path $Root "scripts\probe-agency-llm-providers.py")
Pop-Location

if ($InstallCli) {
    Write-Host "`n=== 2. 安装 npm 全局 CLI（不含浏览器登录） ===" -ForegroundColor Cyan
    $packages = @(
        "@google/gemini-cli",
        "@anthropic-ai/claude-code",
        "@github/copilot",
        "@openai/codex",
        "openclaw@latest"
    )
    foreach ($pkg in $packages) {
        Write-Host "npm install -g $pkg ..."
        npm install -g $pkg 2>&1 | Out-Null
    }
}

if ($StartOllama) {
    Write-Host "`n=== 3. Ollama ===" -ForegroundColor Cyan
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        try { ollama list 2>$null | Out-Null } catch { Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden }
        Start-Sleep -Seconds 3
        Write-Host "ollama pull $OllamaModel ..."
        ollama pull $OllamaModel
    } else {
        Write-Host "未找到 ollama，可安装: https://ollama.ai 或 docker compose -f deploy/production/agency-llm-compose.yml up -d"
    }
}

Write-Host "`n=== 4. 安装/部署计划（target=$Target） ===" -ForegroundColor Cyan
Write-Plan -TargetMode $Target

Write-Host "`n=== CLI 首次登录（需交互终端，云服务器请优先 API Key） ===" -ForegroundColor Yellow
Write-Host "  gemini -p hi          # Google 登录"
Write-Host "  claude                # Anthropic 登录"
Write-Host "  生产 .env: AI_DEEPSEEK_API_KEY + HERMES_AGENCY_PROVIDER_CHAIN=deepseek,ollama,openai"
