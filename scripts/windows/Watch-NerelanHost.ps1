<#
.SYNOPSIS
  Restart the Nerelan host when it has died on its own; never after a deliberate stop.

.DESCRIPTION
  Run every few minutes by the scheduled task Install-HostWatchdog.ps1 creates. On
  2026-11-18 the host process ended between two observations with no log line and no
  crash report, and an ACTIVE continuous window then did nothing until a person noticed.
  The logon shortcut only starts the host at sign-in, so nothing brought it back.

  The watchdog restarts the stack through Start-NerelanAtLogon.ps1 only when all hold:
    - the Task API health endpoint does not answer ready (checked three times, 10 s apart);
    - the dev-up record exists and has no ``stopped_at``: dev-down writes ``stopped_at``,
      so a deliberate stop or a redeploy in progress is left alone;
    - no dev-up.ps1 or Start-NerelanAtLogon.ps1 is running (a start is already under way);
    - the last watchdog restart is at least -MinRestartMinutes old (no restart loop).
  Every decision that is not "healthy" is logged to %LOCALAPPDATA%\Nerelan\autostart.log.
  -DryRun prints the decision and changes nothing.
#>
param(
  [string]$RepoDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$MagpiePath = "F:\magpie\magpie.exe",
  [string]$EnvFile = "",
  [string]$HealthUrl = "http://127.0.0.1:8766/api/health",
  [int]$HealthAttempts = 3,
  [int]$HealthIntervalSeconds = 10,
  [int]$MinRestartMinutes = 10,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"

$logDir = Join-Path $env:LOCALAPPDATA "Nerelan"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "autostart.log"
function Log([string]$message) {
  Add-Content -Path $log -Value ("{0:u} watchdog: {1}" -f (Get-Date).ToUniversalTime(), $message) -Encoding UTF8
}

function Test-HostReady {
  for ($i = 0; $i -lt $HealthAttempts; $i++) {
    try {
      $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5
      if ($response.ready -eq $true) { return $true }
    } catch { }
    if ($i -lt $HealthAttempts - 1) { Start-Sleep -Seconds $HealthIntervalSeconds }
  }
  return $false
}

function Test-StartInProgress {
  $self = $PID
  $starters = Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $self -and $_.CommandLine -and
                   ($_.CommandLine -match 'dev-up\.ps1' -or $_.CommandLine -match 'Start-NerelanAtLogon\.ps1') }
  return [bool]$starters
}

function Get-Decision {
  if (Test-HostReady) { return "healthy" }
  $runtimeDir = Join-Path $RepoDir ".platform_v1_runtime"
  $record = Join-Path $runtimeDir "devup_pids.json"
  if (-not (Test-Path -LiteralPath $record)) { return "no_record" }
  try {
    $state = Get-Content -LiteralPath $record -Raw -Encoding UTF8 | ConvertFrom-Json
  } catch {
    return "record_unreadable"
  }
  if ($state.PSObject.Properties.Name -contains "stopped_at" -and $state.stopped_at) { return "stopped_deliberately" }
  if (Test-StartInProgress) { return "start_in_progress" }
  $marker = Join-Path $runtimeDir "watchdog_last_restart.txt"
  if (Test-Path -LiteralPath $marker) {
    $last = [datetime]::Parse((Get-Content -LiteralPath $marker -Raw).Trim(), [cultureinfo]::InvariantCulture,
                              [System.Globalization.DateTimeStyles]::RoundtripKind)
    if (((Get-Date).ToUniversalTime() - $last.ToUniversalTime()).TotalMinutes -lt $MinRestartMinutes) {
      return "restart_cooling_down"
    }
  }
  return "restart"
}

try {
  $decision = Get-Decision
  if ($DryRun) { Write-Output $decision; return }
  if ($decision -eq "healthy") { return }
  if ($decision -ne "restart") { Log "host not ready; $decision, no action"; return }
  $marker = Join-Path (Join-Path $RepoDir ".platform_v1_runtime") "watchdog_last_restart.txt"
  Set-Content -LiteralPath $marker -Value ((Get-Date).ToUniversalTime().ToString("o")) -Encoding UTF8
  Log "host not ready and not stopped deliberately; restarting"
  $entry = Join-Path $PSScriptRoot "Start-NerelanAtLogon.ps1"
  $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$entry`"",
                 "-RepoDir", "`"$RepoDir`"", "-MagpiePath", "`"$MagpiePath`"")
  if ($EnvFile) { $arguments += @("-EnvFile", "`"$EnvFile`"") }
  $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -WindowStyle Hidden -PassThru
  $null = $process.Handle
  $process.WaitForExit()
  Log "restart finished with exit code $($process.ExitCode)"
} catch {
  Log "failed: $($_.Exception.Message)"
  exit 1
}
