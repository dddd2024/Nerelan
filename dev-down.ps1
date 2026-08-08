<#
.SYNOPSIS
  Stop the dev-up children recorded by the most recent dev-up run.

.DESCRIPTION
  Reads .platform_v1_runtime/devup_pids.json and stops only those child
  processes. It never performs blanket kills of python/node/opencode.

.NOTES
  Missing or already-exited PIDs are ignored cleanly. Runtime metadata
  belongs only to this script; nothing else in .platform_v1_runtime/ is
  removed.
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

foreach ($child in $state.children) {
  $name = $child.name
  $expectedPid = $child.pid
  if (-not $expectedPid) { continue }
  $proc = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
  if (-not $proc) {
    Write-Output "dev-down: ${name} (pid ${expectedPid}) already exited"
    continue
  }
  $exeName = [System.IO.Path]::GetFileName($proc.MainModule.FileName)
  if ($name -eq "model-control" -and $exeName -ne "python.exe") {
    Write-Warning "dev-down: ${name} pid ${expectedPid} is not python.exe; refusing to kill"
    continue
  }
  if ($name -eq "task-api" -and $exeName -ne "python.exe") {
    Write-Warning "dev-down: ${name} pid ${expectedPid} is not python.exe; refusing to kill"
    continue
  }
  if ($name -eq "frontend-vite" -and -not ($exeName -eq "node.exe" -or $exeName -eq "npm.exe" -or $exeName -eq "npm.cmd")) {
    Write-Warning "dev-down: ${name} pid ${expectedPid} is ${exeName}; refusing to kill"
    continue
  }
  try {
    $proc.WaitForExit(3000)
    if (-not $proc.HasExited) {
      $proc.Kill()
      $proc.WaitForExit(5000) | Out-Null
    }
    Write-Output "dev-down: stopped ${name} (pid ${expectedPid})"
  } catch {
    Write-Warning "dev-down: could not stop ${name} (pid ${expectedPid}): $($_.Exception.Message)"
  }
}

$json = [ordered]@{
  stopped_at = (Get-Date -Format o)
  children = $state.children | ForEach-Object {
    [ordered]@{ name = $_.name; pid = $_.pid; stopped = $true }
  }
} | ConvertTo-Json -Depth 6
$json | Set-Content -LiteralPath $pidFile -Encoding UTF8

Write-Output "dev-down: done"
