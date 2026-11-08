<#
.SYNOPSIS
  Start Magpie and the Nerelan host at every logon, so an unattended window survives a shutdown.

.DESCRIPTION
  Creates one shortcut in the current user's Startup folder that runs
  Start-NerelanAtLogon.ps1 without a console window. No scheduled task, service, registry
  key or admin right is involved. A machine that boots but stays at the sign-in screen does
  not start anything until someone signs in. Remove it with -Uninstall.

.EXAMPLE
  .\scripts\windows\Install-HostAutostart.ps1 -EnvFile F:\nerelan-run\run.env.json
.EXAMPLE
  .\scripts\windows\Install-HostAutostart.ps1 -Uninstall
#>
param(
  [string]$RepoDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$MagpiePath = "F:\magpie\magpie.exe",
  [string]$EnvFile = "",
  [switch]$NoBrowser,
  [switch]$Uninstall,
  # Tests point this at a scratch folder instead of the real Startup folder.
  [string]$StartupDir = [Environment]::GetFolderPath("Startup")
)
$ErrorActionPreference = "Stop"

$link = Join-Path $StartupDir "Nerelan host.lnk"
if ($Uninstall) {
  if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link }
  Write-Output "Removed: $link"
  return
}

$RepoDir = (Resolve-Path -LiteralPath $RepoDir).Path
$entry = Join-Path $RepoDir "scripts\windows\Start-NerelanAtLogon.ps1"
if (-not (Test-Path -LiteralPath $entry)) { throw "missing $entry" }
if ($EnvFile) { $EnvFile = (Resolve-Path -LiteralPath $EnvFile).Path }

$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$entry`" -RepoDir `"$RepoDir`" -MagpiePath `"$MagpiePath`""
if ($EnvFile) { $arguments += " -EnvFile `"$EnvFile`"" }
if ($NoBrowser) { $arguments += " -NoBrowser" }

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($link)
$shortcut.TargetPath = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $RepoDir
$shortcut.WindowStyle = 7  # minimized; the script itself hides its window
$shortcut.Description = "Start Magpie and the Nerelan host at logon"
$shortcut.Save()
Write-Output "Installed: $link"
Write-Output "Log:       $(Join-Path $env:LOCALAPPDATA 'Nerelan\autostart.log')"
