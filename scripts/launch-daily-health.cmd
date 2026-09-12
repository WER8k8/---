@echo off
set "SCRIPT_DIR=%~dp0"
set "REPO=%SCRIPT_DIR%.."
cd /d "%REPO%" || exit /b 1
set "YOUDING_REPO_ROOT=%CD%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%ops-daily-health.ps1" -AutoStart
exit /b %ERRORLEVEL%
