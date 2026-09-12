@echo off
REM ASCII-only launcher: no hardcoded Unicode paths (Task Scheduler + cmd.exe safe)
set "SCRIPT_DIR=%~dp0"
set "REPO=%SCRIPT_DIR%.."
cd /d "%REPO%" || exit /b 1
set "YOUDING_REPO_ROOT=%CD%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%ops-expert-daily-run.ps1" -Trigger scheduled -Quiet
exit /b %ERRORLEVEL%
