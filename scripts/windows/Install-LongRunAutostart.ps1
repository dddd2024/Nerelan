<#
.SYNOPSIS
  Resume the real-account long run after a shutdown, without a console window.

.DESCRIPTION
  Writes a runner next to the run's data and a shortcut in the current user's
  Startup folder, so the same resumable command runs again at every logon until
  the deadline passes; then the run removes the shortcut itself. No scheduled
  task, service, registry key or admin right is involved.

  The run must reach a logon: a machine that boots but stays at the sign-in
  screen does not resume until someone signs in. Magpie must also be running for
  rounds to be served; until it is, rounds are recorded as held.

.EXAMPLE
  .\scripts\windows\Install-LongRunAutostart.ps1 -StartNow
.EXAMPLE
  .\scripts\windows\Install-LongRunAutostart.ps1 -Uninstall
#>
param(
  [string]$RuntimeDir = ".platform_v1_runtime\soak-24h",
  [double]$Minutes = 1440,
  [double]$IntervalSeconds = 300,
  [switch]$StartNow,
  [switch]$Uninstall,
  # Tests point this at a scratch folder instead of the real Startup folder.
  [string]$StartupDir = [Environment]::GetFolderPath("Startup")
)
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$link = Join-Path $StartupDir "Nerelan long run.lnk"

if ($Uninstall) {
  if (Test-Path $link) { Remove-Item $link }
  Write-Output "Removed: $link"
  return
}

$python = (Get-Command python -ErrorAction Stop).Source
$runtime = if ([IO.Path]::IsPathRooted($RuntimeDir)) { $RuntimeDir } else { Join-Path $projectDir $RuntimeDir }
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

$runner = Join-Path $runtime "resume.cmd"
$culture = [Globalization.CultureInfo]::InvariantCulture
@(
  "@echo off",
  "cd /d `"$projectDir`"",
  "set NERELAN_LONGRUN_AUTOSTART=$link",
  ("`"$python`" -u scripts\multi_account_live_acceptance.py --resumable" +
   " --soak-minutes $($Minutes.ToString($culture)) --soak-interval $($IntervalSeconds.ToString($culture))" +
   " --runtime-dir `"$runtime`" --evidence `"$runtime\evidence.json`" >> `"$runtime\run.log`" 2>&1")
) | Set-Content -Path $runner -Encoding ASCII

$conhost = Join-Path $env:SystemRoot "System32\conhost.exe"
$arguments = "--headless cmd.exe /c `"$runner`""
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($link)
$shortcut.TargetPath = $conhost
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $projectDir
$shortcut.Description = "Resume the Nerelan real-account long run"
$shortcut.Save()
Write-Output "Installed: $link"
Write-Output "Runner:    $runner"

if ($StartNow) {
  Start-Process -FilePath $conhost -ArgumentList $arguments -WorkingDirectory $projectDir -WindowStyle Hidden
  Write-Output "Started the run now."
}
