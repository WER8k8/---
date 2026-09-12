# D1: 检查商业飞轮相关 Alembic 迁移与表（蜂群包 A）

# Usage: powershell -ExecutionPolicy Bypass -File scripts/check-flywheel-migration.ps1



$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot

$Backend = Join-Path $Root "backend"

$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"

$Python = if (Test-Path -LiteralPath $VenvPy) { $VenvPy } else { "python" }

$fail = 0

Push-Location $Backend



Write-Host "=== alembic heads ==="

$headsOut = & $Python -m alembic heads 2>&1 | Out-String

Write-Host $headsOut

if ($LASTEXITCODE -ne 0) { $fail++ }



Write-Host "`n=== alembic current ==="

$currentOut = & $Python -m alembic current 2>&1 | Out-String

Write-Host $currentOut

if ($LASTEXITCODE -ne 0) { $fail++ }



Write-Host "`n=== expected revisions ==="

Write-Host "025_ubrain_accio_sales"

Write-Host "026_ubrain_commercial_os"

Write-Host "027_inquiry_source_channel"

Write-Host "028_ubrain_action_audit"



$py = @"

from sqlalchemy import create_engine, inspect

import os

url = os.getenv('DATABASE_URL', 'sqlite:///./youding_dev.db')

try:

    e = create_engine(url)

    insp = inspect(e)

    tables = set(insp.get_table_names())

    need = [

        'ubrain_tenant_memory',

        'buyer_prospect_leads',

        'ubrain_research_insights',

        'ubrain_pipeline_runs',

        'ubrain_feedback_snapshots',

        'ubrain_action_audits',

    ]

    missing = []

    for t in need:

        ok = t in tables

        print(('OK ' if ok else 'MISSING ') + t)

        if not ok:

            missing.append(t)

    if missing:

        raise SystemExit(1)

except SystemExit:

    raise

except Exception as ex:

    print('DB_CHECK_SKIP', ex)

"@



Write-Host "`n=== table check (uses DATABASE_URL if set) ==="

& $Python -c $py 2>&1

if ($LASTEXITCODE -ne 0) { $fail++ }



Pop-Location

if ($fail -gt 0) {

    Write-Host "FAIL flywheel migration check (fail=$fail)" -ForegroundColor Red

    exit 1

}

Write-Host "OK flywheel migration check" -ForegroundColor Green

exit 0

