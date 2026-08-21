@echo off
setlocal
set "repoDir=%~dp0"
set "repoDir=%repoDir:~0,-1%"
cd /d "%repoDir%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%repoDir%\dev-up.ps1" -RepoDir "%repoDir%" -SourceDir "%repoDir%"
if errorlevel 1 pause
