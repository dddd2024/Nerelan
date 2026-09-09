[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [int]$FrontendPort = 4173,
  [Parameter(Mandatory = $false)]
  [int]$WaitAttempts = 240,
  [Parameter(Mandatory = $false)]
  [int]$WaitIntervalMs = 500
)

$ErrorActionPreference = "Stop"

# Tauri-only lifecycle bridge for the Nerelan desktop shell.
#
# This is the single beforeDevCommand entry point of the Tauri development
# build. It does NOT start Vite itself: dev-up.ps1 remains the sole
# authoritative owner of the local stack (frontend 4173, task API 8766, model
# control 8765) including its fail-closed port-ownership refusal. This bridge
# only delegates to dev-up.ps1 and then waits for the frontend dev URL that
# tauri.conf.json devUrl points at.

if ($FrontendPort -lt 1 -or $FrontendPort -gt 65535) {
  Write-Error "tauri-dev-bridge: FrontendPort $FrontendPort is outside 1-65535"
  exit 2
}
if ($WaitAttempts -lt 1) {
  $WaitAttempts = 1
}
if ($WaitIntervalMs -lt 100) {
  $WaitIntervalMs = 100
}

$FrontendUrl = "http://127.0.0.1:${FrontendPort}"

$dir = $null
if ($PSScriptRoot -and (Test-Path -LiteralPath $PSScriptRoot)) {
  $dir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
}
$devUp = $null
while ($dir) {
  $candidate = Join-Path $dir "dev-up.ps1"
  if (Test-Path -LiteralPath $candidate) {
    $devUp = (Resolve-Path -LiteralPath $candidate).Path
    break
  }
  $parent = Split-Path -LiteralPath $dir -Parent
  if (-not $parent -or $parent -eq $dir) {
    break
  }
  $dir = $parent
}
if (-not $devUp) {
  Write-Error "tauri-dev-bridge: dev-up.ps1 not found above $($dir)"
  exit 3
}
$repoRoot = Split-Path -LiteralPath $devUp -Parent

$pwsh = $null
$found = Get-Command "powershell.exe" -CommandType Application -ErrorAction SilentlyContinue
if ($found) {
  $pwsh = $found.Source
}
if (-not $pwsh) {
  Write-Error "tauri-dev-bridge: powershell.exe not found on PATH"
  exit 4
}

Write-Output "tauri-dev-bridge: delegating local stack lifecycle to ${devUp}"
& $pwsh -NoProfile -NonInteractive -NoLogo -ExecutionPolicy Bypass -File $devUp -NoBrowser -RepoDir $repoRoot
$upExit = $LASTEXITCODE
if ($upExit -ne 0) {
  Write-Error "tauri-dev-bridge: dev-up.ps1 exited ${upExit}"
  exit $upExit
}

$ready = $false
for ($i = 0; $i -lt $WaitAttempts; $i++) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Method Get -Uri $FrontendUrl -TimeoutSec 2 -ErrorAction Stop
    $code = [int]$response.StatusCode
    if ($code -ge 200 -and $code -lt 500) {
      $ready = $true
      break
    }
  }
  catch {
    Start-Sleep -Milliseconds $WaitIntervalMs
  }
}
if (-not $ready) {
  $waitedSeconds = [double]($WaitAttempts * $WaitIntervalMs) / 1000.0
  Write-Error "tauri-dev-bridge: frontend did not become reachable at ${FrontendUrl} after ${waitedSeconds}s"
  exit 5
}

Write-Output "tauri-dev-bridge: frontend reachable at ${FrontendUrl}"
exit 0
