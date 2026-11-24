<#
.SYNOPSIS
  Register a per-user scheduled task that runs Watch-NerelanHost.ps1 every few minutes.

.DESCRIPTION
  The logon shortcut (Install-HostAutostart.ps1) starts the host once at sign-in. This task
  brings it back when it dies on its own later; a deliberate dev-down is left alone (see
  Watch-NerelanHost.ps1). The task runs as the current user, only while that user is signed
  in, with no stored password and no elevation. Remove it with -Uninstall.

.EXAMPLE
  .\scripts\windows\Install-HostWatchdog.ps1 -EnvFile F:\nerelan-run-config\run.env.json
.EXAMPLE
  .\scripts\windows\Install-HostWatchdog.ps1 -Uninstall
#>
param(
  [string]$RepoDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$MagpiePath = "F:\magpie\magpie.exe",
  [string]$EnvFile = "",
  [int]$IntervalMinutes = 5,
  [string]$TaskName = "Nerelan host watchdog",
  [switch]$NoBrowser,
  [switch]$Uninstall
)
$ErrorActionPreference = "Stop"

if ($Uninstall) {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }
  Write-Output "Removed: $TaskName"
  return
}
if ($IntervalMinutes -lt 1) { throw "IntervalMinutes must be at least 1" }

$RepoDir = (Resolve-Path -LiteralPath $RepoDir).Path
$entry = Join-Path $RepoDir "scripts\windows\Watch-NerelanHost.ps1"
if (-not (Test-Path -LiteralPath $entry)) { throw "missing $entry" }
if ($EnvFile) { $EnvFile = (Resolve-Path -LiteralPath $EnvFile).Path }

$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$entry`" -RepoDir `"$RepoDir`" -MagpiePath `"$MagpiePath`""
if ($EnvFile) { $arguments += " -EnvFile `"$EnvFile`"" }
if ($NoBrowser) { $arguments += " -NoBrowser" }

# A task that starts powershell.exe directly opens a console window for a moment, even
# with -WindowStyle Hidden, and that window takes the foreground: every 5 minutes it threw
# the Owner out of full-screen games (2026-11-18). A headless console host never shows one.
$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot "System32\conhost.exe") `
  -Argument "--headless `"$powershell`" $arguments" -WorkingDirectory $RepoDir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
  -LogonType Interactive -RunLevel Limited
# No execution time limit: the scheduler must never end the run that restarted the host,
# since stopping a task can terminate the processes it started.
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal `
  -Settings $settings -Description "Restart the Nerelan host when it dies on its own" -Force | Out-Null
Write-Output "Installed: $TaskName (every $IntervalMinutes min)"
Write-Output "Log:       $(Join-Path $env:LOCALAPPDATA 'Nerelan\autostart.log')"
