@echo off
chcp 65001 >nul
title YouDing Global OS - All Services Starter
echo ======================================================================
echo              YouDing Global Growth OS - One-Click Starter
echo ======================================================================

set "WORKTREE=C:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix"
cd /d "%WORKTREE%"

echo [1/3] Terminating any stale lock & port processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5174 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 "') do taskkill /F /PID %%a >nul 2>&1

echo [2/4] Executing database migrations...
pushd backend
py -3.12 -m alembic upgrade heads >nul 2>&1
popd

echo [3/4] Launching all 5 core stack services concurrently...
start "FastAPI-Backend:8000" /min cmd /c "cd backend && py -3.12 run.py --env dev --port 8000"
start "SEO-Backend:3001" /min cmd /c "cd seo-backend && node src/app.js"
start "Admin-Frontend:5174" /min cmd /c "cd frontend\admin && npm.cmd run dev -- --port 5174 --host 0.0.0.0"
start "SEO-Admin:5173" /min cmd /c "cd seo-admin && npm.cmd run dev -- --port 5173 --host 0.0.0.0"
set NUXT_IGNORE_LOCK=1
start "Portal-Frontend:3000" /min cmd /c "cd frontend && npm.cmd run dev"

echo [4/4] Probing ports and verifying health status...
timeout /t 6 >nul

echo ======================================================================
echo                      Services Status Verification
echo ======================================================================
powershell -NoProfile -Command ^
  "$ports = @(8000, 3000, 5174, 3001, 5173); ^
   $names = @{8000='FastAPI Backend'; 3000='Portal Web (Nuxt3)'; 5174='Admin Dashboard'; 3001='SEO Backend'; 5173='SEO Admin'}; ^
   $urls  = @{8000='http://127.0.0.1:8000/api/v1/health'; 3000='http://127.0.0.1:3000/'; 5174='http://127.0.0.1:5174/'; 3001='http://127.0.0.1:3001/'; 5173='http://127.0.0.1:5173/'}; ^
   foreach ($p in $ports) { ^
     $active = (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue); ^
     if ($active) { Write-Host ('  [ONLINE]  Port ' + $p + ' -> ' + $names[$p] + ': ' + $urls[$p]) -ForegroundColor Green } ^
     else { Write-Host ('  [WAITING] Port ' + $p + ' -> ' + $names[$p] + ' (Starting up...)') -ForegroundColor Yellow } ^
   }"
echo ======================================================================
echo All services have been dispatched. You can close this window now.
pause
