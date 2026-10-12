$ErrorActionPreference = "Stop"

# Creates a "Nerelan" desktop shortcut that starts (or reopens) Nerelan with no console window.
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$starter = Join-Path $projectDir "scripts\windows\Start-Nerelan.ps1"
$icon = Join-Path $projectDir "assets\windows\nerelan.ico"

if (!(Test-Path $starter)) {
    throw "Launcher not found: $starter"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Nerelan.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
# conhost --headless runs PowerShell without ever showing a console window.
$shortcut.TargetPath = Join-Path $env:SystemRoot "System32\conhost.exe"
$shortcut.Arguments = "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$starter`""
$shortcut.WorkingDirectory = $projectDir
$shortcut.IconLocation = if (Test-Path $icon) { "$icon,0" } else { "$env:SystemRoot\System32\shell32.dll,220" }
$shortcut.Description = "Nerelan multi-agent development platform"
$shortcut.Save()

Write-Output "Shortcut created: $shortcutPath"
