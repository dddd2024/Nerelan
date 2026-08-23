@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\dev-up.ps1" -RepoDir "%SCRIPT_DIR%" -SourceDir "%SCRIPT_DIR%"
if errorlevel 1 pause
