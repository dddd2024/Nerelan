<#
.SYNOPSIS
  Start the reverse-agent Platform V2 one-command local stack.

.DESCRIPTION
  Starts, health-checks, and reports three loopback services:
    - Frontend        : http://127.0.0.1:4173
    - Task API        : http://127.0.0.1:8766
    - Model Control   : http://127.0.0.1:8765

  dev-up does NOT install packages, does NOT print secrets, and does NOT
  invoke any model. It only starts the existing local service entry points.

  dev-up is idempotent: repeated runs against the same RepoDir reuse a healthy
  recorded stack, repair a partial/unhealthy/config-drifted one by stopping
  only verified owned children, and fail closed when ports are held by
  unknown processes. The runtime directory always derives from the resolved
  RepoDir (blank RepoDir means the script directory), never from the caller's
  working directory or a previous runtime value.

  RepoDir  = trusted service host (frontend/node_modules, .platform_v1_runtime).
  SourceDir = repository exposed to OpenCode via REVERSE_AGENT_REPO_DIR.
  When SourceDir is omitted or blank it deterministically equals resolved RepoDir.

  Process-tree ownership: each child is recorded with its exact PID, expected
  executable, and start time. On failure dev-up cleans up only the exact PIDs
  started by that invocation. No image-wide or name-wide kill is ever used.

.EXAMPLE
  .\dev-up.ps1 -RepoDir F:\repo -SourceDir F:\source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser

.NOTES
  Only writes runtime metadata under .platform_v1_runtime/.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoDir = "",
  [Parameter(Mandatory = $false)]
  [string]$SourceDir = "",
  [Parameter(Mandatory = $false)]
  [string]$OpenCodeModel = "sensetime/sensenova-6.7-flash-lite",
  [Parameter(Mandatory = $false)]
  [int]$FrontendPort = 4173,
  [Parameter(Mandatory = $false)]
  [int]$TaskApiPort = 8766,
  [Parameter(Mandatory = $false)]
  [int]$ModelControlPort = 8765,
  [Parameter(Mandatory = $false)]
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$FrontendUrl = "http://127.0.0.1:${FrontendPort}"
$TaskApiUrl = "http://127.0.0.1:${TaskApiPort}"
$ModelControlUrl = "http://127.0.0.1:${ModelControlPort}"

$script:startedChildren = New-Object System.Collections.Generic.List[object]
$script:runtimeDir = ""

function Resolve-InputPath([string]$candidate) {
  $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
  if ($resolved) { return $resolved.Path }
  return $candidate
}

function Get-InvalidDirReason([string]$candidate, [string]$label) {
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    return "${label} is empty or whitespace: '${candidate}'"
  }
  # Fixed Windows-invalid path character set: control characters plus " < > * | ?.
  # [System.IO.Path]::GetInvalidPathChars() is platform-dependent (quotes and
  # pipes are legal on Linux), but dev-up is the Windows bootstrap and the
  # observed New-Item failure came from embedded quotes, so rejection must be
  # deterministic under both Windows powershell and pwsh.
  if ($candidate -match '[\x00-\x1F"<>*|?]') {
    return "${label} contains an invalid filesystem character: '${candidate}'"
  }
  $segments = @($candidate -split "[\\/]")
  if ($segments -contains ".platform_v1_runtime") {
    return "${label} must not point inside .platform_v1_runtime: '${candidate}'"
  }
  return $null
}

function Stop-Owned-Children {
  foreach ($child in $script:startedChildren) {
    try {
      $proc = Get-Process -Id $child.pid -ErrorAction SilentlyContinue
      if ($proc -and -not $proc.HasExited) {
        if ($child.wrapped) {
          $ki = Start-Process "taskkill" -ArgumentList "/PID $($child.pid) /T /F" -Wait -NoNewWindow -PassThru -ErrorAction SilentlyContinue
          if ($ki) { $ki.WaitForExit(5000) | Out-Null }
        } else {
          $proc.Kill()
          $proc.WaitForExit(5000) | Out-Null
        }
      }
    } catch {}
  }
  $script:startedChildren.Clear()
}

function Fail-Closed([string]$msg) {
  Stop-Owned-Children
  $logBase = if ($script:runtimeDir) { $script:runtimeDir } else { Join-Path $PSScriptRoot ".platform_v1_runtime" }
  try { New-Item -ItemType Directory -Path $logBase -Force | Out-Null } catch {}
  Add-Content -LiteralPath (Join-Path $logBase "devup.fail.log") -Value "[FAIL] ${msg}" -Encoding UTF8 -ErrorAction SilentlyContinue
  Write-Error "dev-up: ${msg}"
  exit 1
}

function Find-Executable([string]$name) {
  $exts = @($env:PATHEXT -split ";") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  $searchExts = @()
  foreach ($ext in $exts) {
    $e = if ($ext.StartsWith('.')) { $ext } else { ".$ext" }
    $searchExts += $e
  }
  $searchExts += @(".cmd", ".ps1", ".bat", ".exe", ".com", "")

  $candidates = @($env:PATH -split ";") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
  $candidates += @((Get-Location).Path)

  foreach ($dir in $candidates) {
    foreach ($ext in $searchExts) {
      $candidate = Join-Path $dir "${name}${ext}"
      if (Test-Path -LiteralPath $candidate) {
        return (Get-Item -LiteralPath $candidate).FullName
      }
    }
  }

  $found = Get-Command -Name $name -CommandType Application, Filter, Function, Cmdlet, ExternalScript -ErrorAction SilentlyContinue
  if ($found) {
    if ($found -is [array] -and $found.Length -gt 0) { $found = $found[0] }
    $source = $found.Source
    if ($source -match '\.(ps1|cmd|bat|exe|com)$') { return $source }
    foreach ($dir in $candidates) {
      foreach ($ext in $searchExts) {
        $candidate = Join-Path $dir "${name}${ext}"
        if (Test-Path -LiteralPath $candidate) {
          return (Get-Item -LiteralPath $candidate).FullName
        }
      }
    }
    return $source
  }
  return $null
}

function Is-PortInUse([int]$port) {
  try {
    $tcp = New-Object Net.Sockets.TcpClient
    $ar = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
    $wait = $ar.AsyncWaitHandle.WaitOne(700, $false)
    if (-not $wait) {
      try { $tcp.Close() } catch {}
      return $false
    }
    $tcp.EndConnect($ar) | Out-Null
    $tcp.Close()
    return $true
  } catch {
    return $false
  }
}

function Get-PortProcess([int]$port) {
  try {
    $netstat = netstat -ano 2>$null | Select-String ":${port}\s+LISTENING"
  } catch { return $null }
  if (-not $netstat) { return $null }
  $parts = $netstat.Line.Trim() -split "\s+"
  if ($parts.Length -ge 5) {
    try { return [int]$parts[4] } catch {}
  }
  return $null
}

function Start-ServiceProcess(
  [string]$name,
  [string]$cmd,
  [object[]]$serviceArgs,
  [hashtable]$env,
  [string]$cwd,
  [string]$logDir
) {
  $argString = ($serviceArgs -join " ")
  $logFile = Join-Path $logDir "${name}.log"

  if ($cmd -match '\.ps1$') {
    $pwsh = Get-Command "powershell.exe" -ErrorAction SilentlyContinue
    $pwshPath = if ($pwsh) { $pwsh.Source } else { "powershell.exe" }
    $inner = "`"$pwshPath`" -NoProfile -NonInteractive -NoLogo -File `"$cmd`" $argString"
  } else {
    $inner = "`"$cmd`" $argString"
  }

  # Service children must never inherit dev-up's stdio handles. The .NET
  # UseShellExecute=false path enables full handle inheritance, so a
  # long-lived child would keep the caller's stdout/stderr pipe write ends
  # open and block any orchestrator (pytest, CI) reading dev-up output until
  # EOF - even after dev-up itself exits or is killed. ShellExecute passes no
  # handles; per-child environment variables travel inside the wrapper as
  # `set` commands, and the wrapper redirects the real service's stdio into a
  # per-service log file so the service never blocks on an unread pipe.
  $setEnv = @()
  foreach ($kv in $env.GetEnumerator()) {
    $setEnv += "set `"$($kv.Key)=$($kv.Value)`""
  }
  $wrappedCommand = (@($setEnv) + @("$inner > `"${logFile}`" 2>&1")) -join " && "

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "cmd.exe"
  $psi.Arguments = "/s /c `"$wrappedCommand`""
  $psi.UseShellExecute = $true
  $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
  $psi.WorkingDirectory = $cwd

  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi
  try {
    $null = $proc.Start()
  } catch {
    Stop-Owned-Children
    Fail-Closed "service '${name}' (${cmd} ${argString}) failed to start: $($_.Exception.Message)"
  }

  Set-Content -LiteralPath (Join-Path $logDir "${name}.pid") -Value $proc.Id -Encoding UTF8 | Out-Null

  $script:startedChildren.Add([ordered]@{
    name = $name
    pid = $proc.Id
    expected_exe = "cmd.exe"
    start_time = $proc.StartTime.ToString("o")
    cmd = $cmd
    serviceArgs = $argString
    wrapped = $true
    handle = $proc
  })

  Write-Host "dev-up: ${name} started pid=$($proc.Id)"
  return $proc
}

function Wait-ServiceReady(
  [string]$url,
  [int]$attempts = 40,
  [int]$intervalMs = 500
) {
  for ($i = 0; $i -lt $attempts; $i++) {
    try {
      $resp = Invoke-WebRequest -UseBasicParsing -Method Get -Uri $url -TimeoutSec 2 -ErrorAction SilentlyContinue
      if ($resp -and $resp.StatusCode -and
          ($resp.StatusCode -eq 200 -or $resp.StatusCode -eq 204 -or
           $resp.StatusCode -eq 301 -or $resp.StatusCode -eq 302 -or
           $resp.StatusCode -eq 400 -or $resp.StatusCode -eq 404 -or
           $resp.StatusCode -eq 405 -or $resp.StatusCode -eq 406)) {
        return $true
      }
    } catch {}
    Start-Sleep -Milliseconds $intervalMs
  }
  return $false
}

function Write-StackSummary {
  Write-Output "Model Control: ${ModelControlUrl}"
  Write-Output "Task API:      ${TaskApiUrl}"
  Write-Output "Frontend:      ${FrontendUrl}"
  Write-Output "Executor:      opencode"
  Write-Output "Coordinator:   enabled (requires an owner-activated window)"
  Write-Output "Model:         ${OpenCodeModel}"
  Write-Output "Runtime state: ${pidFile}"
}

# RepoDir is the trusted service host: frontend/node_modules and runtime.
# SourceDir is the repository exposed to OpenCode via REVERSE_AGENT_REPO_DIR.
# Blank/absent SourceDir deterministically falls back to resolved RepoDir (V3-F2).
# Blank/absent RepoDir deterministically resolves to the script directory, never
# the caller's current working directory, so the runtime directory is identical
# across repeated executions (idempotency).
if ([string]::IsNullOrWhiteSpace($RepoDir)) {
  $repoDir = $PSScriptRoot
} else {
  $repoDir = Resolve-InputPath $RepoDir
}
if ([string]::IsNullOrWhiteSpace($SourceDir)) {
  $sourceDir = $repoDir
} else {
  $sourceDir = Resolve-InputPath $SourceDir
}

$runtimeDir = Join-Path $repoDir ".platform_v1_runtime"
$pidFile = Join-Path $runtimeDir "devup_pids.json"
$script:runtimeDir = $runtimeDir

$repoDirRejection = Get-InvalidDirReason -candidate $repoDir -label "RepoDir"
if ($repoDirRejection) { Fail-Closed $repoDirRejection }
$sourceDirRejection = Get-InvalidDirReason -candidate $sourceDir -label "SourceDir"
if ($sourceDirRejection) { Fail-Closed $sourceDirRejection }

foreach ($portParam in @($FrontendPort, $TaskApiPort, $ModelControlPort)) {
  if ($portParam -lt 1 -or $portParam -gt 65535) {
    Fail-Closed "port ${portParam} is outside the valid range 1-65535"
  }
}
if ($FrontendPort -eq $TaskApiPort -or $FrontendPort -eq $ModelControlPort -or $TaskApiPort -eq $ModelControlPort) {
  Fail-Closed "service ports must be distinct: ${FrontendPort}/${TaskApiPort}/${ModelControlPort}"
}

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

# Startup state reconciliation: a healthy recorded stack is reused; a partial,
# unhealthy or config-drifted one is repaired by stopping only verified owned
# children; unknown port occupants keep the fail-closed refusal below.
function Compare-ProcessStartTime([string]$recordedStartTimeStr, [datetime]$actualStartTime) {
  if ([string]::IsNullOrWhiteSpace($recordedStartTimeStr)) { return $false }
  $recorded = $null
  try {
    $parsed = [datetime]::MinValue
    if (-not [datetime]::TryParse($recordedStartTimeStr, [ref]$parsed)) { return $false }
    $recorded = $parsed
    if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
      $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
    }
    $recordedUtc = $recorded.ToUniversalTime()
  } catch { return $false }
  try { $actualUtc = $actualStartTime.ToUniversalTime() } catch { return $false }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}

function Test-RecordedChildOwned([object]$child) {
  if (-not $child -or -not $child.pid) { return $false }
  $proc = Get-Process -Id $child.pid -ErrorAction SilentlyContinue
  if (-not $proc) { return $false }
  $actualExe = $null
  try { $actualExe = [System.IO.Path]::GetFileName($proc.MainModule.FileName) } catch { return $false }
  $wrapped = if ($child.PSObject.Properties.Name -contains "wrapped") { [bool]$child.wrapped } else { $false }
  $expectedExe = if ($child.expected_exe) { [string]$child.expected_exe } else { $null }
  $identityOk = $false
  if ($wrapped -and $actualExe -eq "cmd.exe") {
    $identityOk = $true
  } elseif ($expectedExe -and $actualExe -eq $expectedExe) {
    $identityOk = $true
  }
  if (-not $identityOk) { return $false }
  $recordedStart = if ($child.PSObject.Properties.Name -contains "start_time") { [string]$child.start_time } else { $null }
  if (-not (Compare-ProcessStartTime $recordedStart $proc.StartTime)) { return $false }
  return $true
}

function Stop-VerifiedChild([object]$child) {
  try {
    $proc = Get-Process -Id $child.pid -ErrorAction SilentlyContinue
    if ($proc -and -not $proc.HasExited) {
      if ($child.wrapped) {
        $ki = Start-Process "taskkill" -ArgumentList "/PID $($child.pid) /T /F" -Wait -NoNewWindow -PassThru -ErrorAction SilentlyContinue
        if ($ki) { $ki.WaitForExit(5000) | Out-Null }
      } else {
        $proc.Kill()
        $proc.WaitForExit(5000) | Out-Null
      }
    }
  } catch {}
}

function Test-StackHealthy {
  if (-not (Wait-ServiceReady -url "$ModelControlUrl/api/model-profiles" -attempts 8 -intervalMs 250)) { return $false }
  if (-not (Wait-ServiceReady -url "${TaskApiUrl}/api/tasks" -attempts 8 -intervalMs 250)) { return $false }
  return (Wait-ServiceReady -url "$FrontendUrl/" -attempts 8 -intervalMs 250)
}

function Wait-PortsFreed {
  foreach ($portParam in @($FrontendPort, $TaskApiPort, $ModelControlPort)) {
    $freed = $false
    for ($i = 0; $i -lt 20; $i++) {
      if (-not (Is-PortInUse $portParam)) { $freed = $true; break }
      Start-Sleep -Milliseconds 250
    }
    if (-not $freed) { Fail-Closed "port ${portParam} did not free after stopping owned children" }
  }
}

$stackReused = $false
if (Test-Path -LiteralPath $pidFile) {
  $runtimeState = $null
  $rawRecord = $null
  try { $rawRecord = Get-Content -LiteralPath $pidFile -Raw -Encoding UTF8 -ErrorAction SilentlyContinue } catch { $rawRecord = $null }
  if ([string]::IsNullOrWhiteSpace($rawRecord)) {
    Write-Warning "dev-up: invalid runtime state at ${pidFile} (empty record); starting fresh"
  } else {
    try { $runtimeState = $rawRecord | ConvertFrom-Json -ErrorAction Stop } catch {
      Write-Warning "dev-up: invalid runtime state at ${pidFile} (unparseable record); starting fresh"
    }
  }
  if ($runtimeState -and $runtimeState.children) {
    $recordedRepoDir = [string]$runtimeState.repo_dir
    if (-not ($recordedRepoDir.TrimEnd('\') -ieq ([string]$repoDir).TrimEnd('\'))) {
      if (@($runtimeState.children | Where-Object { Test-RecordedChildOwned $_ }).Count -gt 0) {
        Write-Warning "dev-up: runtime record at ${pidFile} belongs to a different repo_dir; refusing to reuse or stop its children"
      }
    } else {
      $ownedChildren = @($runtimeState.children | Where-Object { Test-RecordedChildOwned $_ })
      $configMatches = (([string]$runtimeState.source_dir).TrimEnd('\') -ieq ([string]$sourceDir).TrimEnd('\')) -and
        ([string]$runtimeState.open_code_model -eq [string]$OpenCodeModel)
      if ($ownedChildren.Count -gt 0 -and $configMatches -and (Test-StackHealthy)) {
        $stackReused = $true
        $ownedList = ($ownedChildren | ForEach-Object { "$($_.name) (pid $($_.pid))" }) -join ", "
        Write-Output "dev-up: stack already running and healthy; reusing recorded runtime: ${ownedList}"
      } elseif ($ownedChildren.Count -gt 0) {
        foreach ($child in $ownedChildren) {
          Write-Output "dev-up: repair: stopping recorded child $($child.name) (pid $($child.pid))"
          Stop-VerifiedChild $child
        }
        Wait-PortsFreed
      }
    }
  }
}

if ($stackReused) {
  Write-StackSummary
  if (-not $NoBrowser) {
    try { Start-Process $FrontendUrl } catch {}
  }
  exit 0
}

$py = Find-Executable "python"
if (-not $py) { Fail-Closed "prerequisite missing: python (not installed)" }

$node = Find-Executable "node"
if (-not $node) { Fail-Closed "prerequisite missing: node (not installed)" }

$npm = Find-Executable "npm"
if (-not $npm) { Fail-Closed "prerequisite missing: npm (not installed)" }

$opencode = Find-Executable "opencode"
if (-not $opencode) { Fail-Closed "prerequisite missing: opencode (not installed)" }
Write-Output "dev-up: startup repo=${repoDir} source=${sourceDir}"
Write-Output "dev-up: py=$py npm=$npm opencode=$opencode"

$nodeModules = Join-Path $repoDir "frontend\node_modules"
if (-not (Test-Path -LiteralPath $nodeModules)) {
  Fail-Closed "prerequisite missing: frontend/node_modules (run npm install manually before dev-up)"
}

foreach ($port in @($FrontendPort, $TaskApiPort, $ModelControlPort)) {
  if (Is-PortInUse $port) {
    $portProc = Get-PortProcess $port
    $hint = ""
    if ($portProc) { $hint = " (process ${portProc})" }
    Fail-Closed "port ${port} is already occupied by an unknown process${hint}; refusing to interfere"
  }
}

$modelControlEnv = [ordered]@{
  "REVERSE_AGENT_MODEL_CONTROL_HOST" = "127.0.0.1"
  "REVERSE_AGENT_MODEL_CONTROL_PORT" = [string]$ModelControlPort
  "REVERSE_AGENT_MODEL_CONTROL_ORIGIN" = $FrontendUrl
}

$taskApiEnv = [ordered]@{
  "REVERSE_AGENT_TASK_SERVICE_HOST" = "127.0.0.1"
  "REVERSE_AGENT_TASK_SERVICE_PORT" = [string]$TaskApiPort
  "REVERSE_AGENT_TASK_SERVICE_ORIGIN" = $FrontendUrl
  "REVERSE_AGENT_REPO_DIR" = $sourceDir
  "REVERSE_AGENT_OPENCODE_MODEL" = $OpenCodeModel
}

$frontendEnv = [ordered]@{
  "VITE_TASK_API_BASE" = $TaskApiUrl
  "VITE_MODEL_CONTROL_API_BASE" = "http://127.0.0.1:${ModelControlPort}/api"
  "VITE_PORT" = [string]$FrontendPort
  "VITE_INLINE_CONFIG" = "server.port=${FrontendPort};server.host=127.0.0.1;server.strictPort=true"
}

$combinedTrustedHostEnv = [ordered]@{
  "REVERSE_AGENT_MODEL_CONTROL_HOST" = "127.0.0.1"
  "REVERSE_AGENT_MODEL_CONTROL_PORT" = [string]$ModelControlPort
  "REVERSE_AGENT_MODEL_CONTROL_ORIGIN" = $FrontendUrl
  "REVERSE_AGENT_TASK_SERVICE_HOST" = "127.0.0.1"
  "REVERSE_AGENT_TASK_SERVICE_PORT" = [string]$TaskApiPort
  "REVERSE_AGENT_TASK_SERVICE_ORIGIN" = $FrontendUrl
  "REVERSE_AGENT_REPO_DIR" = $sourceDir
  "REVERSE_AGENT_OPENCODE_MODEL" = $OpenCodeModel
  "REVERSE_AGENT_AUTONOMOUS" = "1"
}

$combinedProc = Start-ServiceProcess `
  -name "combined-trusted-host" `
  -cmd $py -serviceArgs @("-m", "reverse_agent.platform_v1.trusted_host") `
  -env $combinedTrustedHostEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 2000

if (-not $combinedProc.HasExited) {
  $mcHealthy = Wait-ServiceReady -url "$ModelControlUrl/api/model-profiles"
  $taskHealthy = Wait-ServiceReady -url "${TaskApiUrl}/api/tasks"
  if (-not $mcHealthy) {
    Fail-Closed "Model Control did not become healthy at ${ModelControlUrl}"
  }
  if (-not $taskHealthy) {
    Fail-Closed "Task API did not become healthy at ${TaskApiUrl}"
  }
} else {
  Fail-Closed "Combined trusted host exited before health check"
}

$frontendProc = Start-ServiceProcess `
  -name "frontend-vite" `
  -cmd $npm -serviceArgs @("--prefix", "frontend", "run", "dev") `
  -env $frontendEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 1500

if (-not $frontendProc.HasExited) {
  if (-not (Wait-ServiceReady -url "$FrontendUrl/")) {
    Fail-Closed "Frontend did not become healthy at ${FrontendUrl}"
  }
} else {
  Fail-Closed "Frontend exited before health check"
}

$urlMap = [ordered]@{
  "combined-trusted-host" = $ModelControlUrl
  "frontend-vite" = $FrontendUrl
}

$persistentChildren = foreach ($child in $script:startedChildren) {
  [ordered]@{
    name = $child.name
    pid = $child.pid
    expected_exe = $child.expected_exe
    start_time = $child.start_time
    cmd = $child.cmd
    service_args = $child.serviceArgs
    wrapped = $child.wrapped
    url = $urlMap[$child.name]
  }
}

$record = [ordered]@{
  created_at = (Get-Date -Format o)
  repo_dir = $repoDir
  source_dir = $sourceDir
  open_code_model = $OpenCodeModel
  children = $persistentChildren
  metadata = [ordered]@{
    frontend_url = $FrontendUrl
    task_api_url = $TaskApiUrl
    model_control_url = $ModelControlUrl
    executor = "opencode"
    unattended_coordinator = "enabled"
    open_code_model = $OpenCodeModel
  }
}

$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pidFile -Encoding UTF8

Write-StackSummary

if (-not $NoBrowser) {
  try { Start-Process $FrontendUrl } catch {}
}
