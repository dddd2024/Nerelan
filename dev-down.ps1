<#
.SYNOPSIS
  Stop the dev-up children recorded by the most recent dev-up run.

.DESCRIPTION
  Reads .platform_v1_runtime/devup_pids.json and stops only the exact child
  process trees created by the matching dev-up invocation. It verifies each
  recorded PID against its expected executable identity before terminating.

  Only the exact owned PID tree is stopped. No image-wide or name-wide kill
  is ever performed. For cmd.exe-wrapped children (npm.cmd -> cmd.exe -> node)
  taskkill /PID /T terminates the entire recorded tree.

  Per-child outcome is recorded truthfully:
    stopped                - process was stopped by this invocation
    already_exited         - PID was not present when checked
    refused_identity_mismatch - process identity did not match record
    stop_failed            - stop was attempted but did not succeed

.NOTES
  Missing or already-exited PIDs are ignored cleanly. Runtime metadata
  belongs only to this script; nothing else in .platform_v1_runtime/ is
  removed. No credentials or secrets are read or written.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoDir = ""
)

$ErrorActionPreference = "Stop"

function Resolve-RepoDir([string]$candidate) {
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    return (Get-Location).Path
  }
  $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
  if ($resolved) { return $resolved.Path }
  return $candidate
}

$repoDir = Resolve-RepoDir $RepoDir
$runtimeDir = Join-Path $repoDir ".platform_v1_runtime"
$pidFile = Join-Path $runtimeDir "devup_pids.json"

function Compare-ProcessStartTime([string]$recordedStartTimeStr, [datetime]$actualStartTime) {
  if ([string]::IsNullOrWhiteSpace($recordedStartTimeStr)) {
    return $false
  }
  $recorded = $null
  try {
    $parsed = [datetime]::MinValue
    if (-not [datetime]::TryParse($recordedStartTimeStr, [ref]$parsed)) {
      return $false
    }
    $recorded = $parsed
    if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
      $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
    }
    $recordedUtc = $recorded.ToUniversalTime()
  } catch {
    return $false
  }
  try {
    $actualUtc = $actualStartTime.ToUniversalTime()
  } catch {
    return $false
  }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}

if (-not (Test-Path -LiteralPath $pidFile)) {
  Write-Output "dev-down: no dev-up PID record at ${pidFile}; nothing to stop"
  exit 0
}

$json = Get-Content -LiteralPath $pidFile -Raw -Encoding UTF8
$state = $null
try { $state = $json | ConvertFrom-Json -ErrorAction Stop } catch {
  Write-Warning "dev-down: could not parse ${pidFile}: $($_.Exception.Message)"
  exit 0
}

if (-not $state -or -not $state.children) {
  Write-Output "dev-down: no children recorded; nothing to stop"
  exit 0
}

function Try-Stop-Child([object]$child) {
  $name = $child.name
  $expectedPid = $child.pid
  $expectedExe = if ($child.expected_exe) { $child.expected_exe } else { $null }
  $wrapped = if ($child.PSObject.Properties.Name -contains "wrapped") { $child.wrapped } else { $false }
  $recordedStartTime = if ($child.PSObject.Properties.Name -contains "start_time") { $child.start_time } else { $null }

  $result = [ordered]@{
    name = $name
    pid = $expectedPid
    expected_exe = $expectedExe
    outcome = $null
  }

  if (-not $expectedPid) {
    $result.outcome = "already_exited"
    return $result
  }

  $proc = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
  if (-not $proc) {
    $result.outcome = "already_exited"
    Write-Output "dev-down: ${name} (pid ${expectedPid}) already exited"
    return $result
  }

  $actualExe = $null
  try {
    $actualExe = [System.IO.Path]::GetFileName($proc.MainModule.FileName)
  } catch {
    $result.outcome = "refused_identity_mismatch"
    Write-Warning "dev-down: ${name} pid ${expectedPid}: cannot read process info; refusing"
    return $result
  }

  $identityOk = $false
  if ($wrapped -and $actualExe -eq "cmd.exe") {
    $identityOk = $true
  } elseif ($expectedExe -and $actualExe -eq $expectedExe) {
    $identityOk = $true
  } elseif (-not $expectedExe -and $name -eq "model-control" -and $actualExe -eq "python.exe") {
    $identityOk = $true
  } elseif (-not $expectedExe -and $name -eq "task-api" -and $actualExe -eq "python.exe") {
    $identityOk = $true
  } elseif (-not $expectedExe -and $name -eq "frontend-vite" -and ($actualExe -eq "node.exe" -or $actualExe -eq "npm.exe" -or $actualExe -eq "npm.cmd")) {
    $identityOk = $true
  }

  if (-not $identityOk) {
    $result.outcome = "refused_identity_mismatch"
    Write-Warning "dev-down: ${name} pid ${expectedPid} is ${actualExe}; refusing to kill"
    return $result
  }

  if (-not (Compare-ProcessStartTime $recordedStartTime $proc.StartTime)) {
    $result.outcome = "refused_identity_mismatch"
    Write-Warning "dev-down: ${name} pid ${expectedPid}: start_time identity mismatch or unreadable (recorded=${recordedStartTime} current=$($proc.StartTime.ToString("o"))); refusing to kill"
    return $result
  }

  try {
    if ($wrapped) {
      $ki = Start-Process "taskkill" -ArgumentList "/PID ${expectedPid} /T /F" -Wait -NoNewWindow -PassThru -ErrorAction SilentlyContinue
      Start-Sleep -Milliseconds 500
      $stillHere = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
      if (-not $stillHere) {
        $result.outcome = "stopped"
        Write-Output "dev-down: stopped ${name} (pid ${expectedPid}) and children"
      } else {
        $result.outcome = "stop_failed"
        Write-Warning "dev-down: ${name} (pid ${expectedPid}) still running after taskkill"
      }
    } else {
      $proc.WaitForExit(3000)
      if (-not $proc.HasExited) {
        $proc.Kill()
        $proc.WaitForExit(5000) | Out-Null
      }
      $result.outcome = "stopped"
      Write-Output "dev-down: stopped ${name} (pid ${expectedPid})"
    }
  } catch {
    $result.outcome = "stop_failed"
    Write-Warning "dev-down: could not stop ${name} (pid ${expectedPid}): $($_.Exception.Message)"
  }

  return $result
}

$stopResults = [System.Collections.Generic.List[object]]::new()
foreach ($child in $state.children) {
  $result = Try-Stop-Child $child
  $stopResults.Add($result)
}

$updatedChildren = foreach ($r in $stopResults) {
  [ordered]@{
    name = $r.name
    pid = $r.pid
    expected_exe = $r.expected_exe
    outcome = $r.outcome
  }
}

$shutdownState = [ordered]@{
  stopped_at = (Get-Date -Format o)
  repo_dir = $state.repo_dir
  source_dir = $state.source_dir
  children = $updatedChildren
}

$shutdownState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pidFile -Encoding UTF8
Write-Output "dev-down: done"