<#
.SYNOPSIS
  Logon entry for unattended runs: start Magpie if it is not running, then the Nerelan host.

.DESCRIPTION
  Run by the Startup shortcut that Install-HostAutostart.ps1 creates. Starts Magpie when
  nothing listens on its gateway port and waits for it, then runs dev-up.ps1, which reuses
  a healthy stack or starts one. An ACTIVE window and its Goals are in the host database, so
  the coordinator resumes them; nothing here activates or extends a window.

  Optional -EnvFile is an Owner-written JSON object of REVERSE_AGENT_* settings applied to
  the host's environment (for example REVERSE_AGENT_MULTI_ACCOUNT_ENABLED). Names that look
  like credentials are refused; secrets stay in the vault. When -EnvFile is omitted, the
  script reads run.env.json from the task database directory (REVERSE_AGENT_TASK_DB_DIR, or
  the default host-owned store under %LOCALAPPDATA%\Nerelan\platform-v1) if present, so a
  reboot needs no hand-written environment file in a separate folder. An explicit -EnvFile
  keeps priority. Path values are normalized to forward slashes; a backslash path crashed
  host startup once. Output goes to %LOCALAPPDATA%\Nerelan\autostart.log.
#>
param(
  [string]$RepoDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
  [string]$MagpiePath = "F:\magpie\magpie.exe",
  [int]$MagpiePort = 3425,
  [int]$MagpieWaitSeconds = 180,
  [string]$EnvFile = "",
  [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"

$logDir = Join-Path $env:LOCALAPPDATA "Nerelan"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "autostart.log"
function Log([string]$message) {
  Add-Content -Path $log -Value ("{0:u} {1}" -f (Get-Date).ToUniversalTime(), $message) -Encoding UTF8
}
function Test-Listening([int]$port) {
  return [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

try {
  Log "logon start: repo=$RepoDir"
  if (Test-Listening $MagpiePort) {
    Log "magpie already listening on $MagpiePort"
  } elseif (Test-Path -LiteralPath $MagpiePath) {
    Start-Process -FilePath $MagpiePath -WorkingDirectory (Split-Path -Parent $MagpiePath) | Out-Null
    $deadline = (Get-Date).AddSeconds($MagpieWaitSeconds)
    while (-not (Test-Listening $MagpiePort) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 2 }
    if (Test-Listening $MagpiePort) { Log "magpie started" } else {
      # The host still starts: rounds without Magpie are held, not failed.
      Log "magpie not listening after ${MagpieWaitSeconds}s; starting the host anyway"
    }
  } else {
    Log "magpie not found at $MagpiePath; starting the host without it"
  }

  if (-not $EnvFile) {
    $taskDbDir = $env:REVERSE_AGENT_TASK_DB_DIR
    if ([string]::IsNullOrWhiteSpace($taskDbDir)) {
      $taskDbDir = Join-Path $env:LOCALAPPDATA "Nerelan\platform-v1"
    }
    $candidate = Join-Path $taskDbDir "run.env.json"
    if (Test-Path -LiteralPath $candidate) { $EnvFile = $candidate }
  }
  if ($EnvFile) {
    $settings = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $applied = 0
    foreach ($property in $settings.PSObject.Properties) {
      $name = [string]$property.Name
      if ($name -notmatch '^REVERSE_AGENT_[A-Z0-9_]+$' -or $name -match 'KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL') {
        throw "refusing environment name from ${EnvFile}: $name"
      }
      $value = [string]$property.Value
      if ($name -like '*_DIR' -or $name -like '*_PATH' -or $name -like '*_EXE' -or $name -like '*_FILE') {
        $value = $value -replace '\\', '/'
      }
      [Environment]::SetEnvironmentVariable($name, $value, "Process")
      $applied++
    }
    Log "applied $applied settings from $EnvFile"
  }

  $devUp = Join-Path $RepoDir "dev-up.ps1"
  $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$devUp`"", "-RepoDir", "`"$RepoDir`"")
  if ($NoBrowser) { $arguments += "-NoBrowser" }
  $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logDir "autostart-devup.log") `
    -RedirectStandardError (Join-Path $logDir "autostart-devup.err.log")
  $null = $process.Handle
  $process.WaitForExit()
  Log "dev-up exited with $($process.ExitCode)"
  exit $process.ExitCode
} catch {
  Log "failed: $($_.Exception.Message)"
  exit 1
}
