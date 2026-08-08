<#
.SYNOPSIS
  Start the reverse-agent Platform V1 one-command development stack.

.DESCRIPTION
  Starts, health-checks, and reports three loopback services:
    - Frontend        : http://127.0.0.1:4173
    - Task API        : http://127.0.0.1:8766
    - Model Control   : http://127.0.0.1:8765

  dev-up does NOT install packages, does NOT print secrets, and does NOT
  invoke any model. It only starts the existing local service entry points.

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
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$FrontendPort = 4173
$TaskApiPort = 8766
$ModelControlPort = 8765

$FrontendUrl = "http://127.0.0.1:${FrontendPort}"
$TaskApiUrl = "http://127.0.0.1:${TaskApiPort}"
$ModelControlUrl = "http://127.0.0.1:${ModelControlPort}"

$script:startedChildren = New-Object System.Collections.Generic.List[object]

function Resolve-InputPath([string]$candidate) {
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    return (Get-Location).Path
  }
  $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
  if ($resolved) { return $resolved.Path }
  return $candidate
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
  $errLog = Join-Path (Join-Path (Get-Location).Path ".platform_v1_runtime") "devup.fail.log"
  try { New-Item -ItemType Directory -Path (Split-Path $errLog) -Force | Out-Null } catch {}
  Add-Content -LiteralPath $errLog -Value "[FAIL] ${msg}" -Encoding UTF8 -ErrorAction SilentlyContinue
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
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.WorkingDirectory = $cwd
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true

  foreach ($kv in $env.GetEnumerator()) {
    $psi.Environment[$kv.Key] = $kv.Value
  }

  $wrapped = $false
  $expectedExe = [System.IO.Path]::GetFileName($cmd)
  if ($cmd -match '\.ps1$') {
    $pwsh = Get-Command "powershell.exe" -ErrorAction SilentlyContinue
    $pwshPath = if ($pwsh) { $pwsh.Source } else { "powershell.exe" }
    $psi.FileName = $pwshPath
    $psi.Arguments = "-NoProfile -NonInteractive -NoLogo -File `"$cmd`" $argString"
    $expectedExe = [System.IO.Path]::GetFileName($pwshPath)
  } elseif ($cmd -match '\.cmd$|\.bat$') {
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c `"$cmd`" $argString"
    $wrapped = $true
    $expectedExe = "cmd.exe"
  } else {
    $psi.FileName = $cmd
    $psi.Arguments = $argString
  }

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
    expected_exe = $expectedExe
    start_time = $proc.StartTime.ToString("o")
    cmd = $cmd
    serviceArgs = $argString
    wrapped = $wrapped
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

# RepoDir is the trusted service host: frontend/node_modules and runtime.
# SourceDir is the repository exposed to OpenCode via REVERSE_AGENT_REPO_DIR.
# Blank/absent SourceDir deterministically falls back to resolved RepoDir (V3-F2).
$repoDir = Resolve-InputPath $RepoDir
if ([string]::IsNullOrWhiteSpace($SourceDir)) {
  $sourceDir = $repoDir
} else {
  $sourceDir = Resolve-InputPath $SourceDir
}

$runtimeDir = Join-Path $repoDir ".platform_v1_runtime"
$pidFile = Join-Path $runtimeDir "devup_pids.json"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

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

$modelProc = Start-ServiceProcess `
  -name "model-control" `
  -cmd $py -serviceArgs @("-m", "reverse_agent.model_access.service") `
  -env $modelControlEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 1500

if (-not $modelProc.HasExited) {
  if (-not (Wait-ServiceReady -url "$ModelControlUrl/api/model-profiles")) {
    Fail-Closed "Model Control did not become healthy at ${ModelControlUrl}"
  }
} else {
  Fail-Closed "Model Control exited before health check"
}

$taskProc = Start-ServiceProcess `
  -name "task-api" `
  -cmd $py -serviceArgs @("-m", "reverse_agent.platform_v1.task_service") `
  -env $taskApiEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 1500

if (-not $taskProc.HasExited) {
  if (-not (Wait-ServiceReady -url "${TaskApiUrl}/api/tasks")) {
    Fail-Closed "Task API did not become healthy at ${TaskApiUrl}"
  }
} else {
  Fail-Closed "Task API exited before health check"
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
  "model-control" = $ModelControlUrl
  "task-api" = $TaskApiUrl
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
    open_code_model = $OpenCodeModel
  }
}

$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pidFile -Encoding UTF8

Write-Output "Model Control: ${ModelControlUrl}"
Write-Output "Task API:      ${TaskApiUrl}"
Write-Output "Frontend:      ${FrontendUrl}"
Write-Output "Executor:      opencode"
Write-Output "Model:         ${OpenCodeModel}"
Write-Output "Runtime state: ${pidFile}"

if (-not $NoBrowser) {
  try { Start-Process $FrontendUrl } catch {}
}