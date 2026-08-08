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

.EXAMPLE
  .\dev-up.ps1 -RepoDir F:\repo -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser

.NOTES
  Only writes runtime metadata under .platform_v1_runtime/.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoDir = "",
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

function Fail-Closed([string]$msg) {
  Write-Error "dev-up: ${msg}"
  exit 1
}

function Resolve-RepoDir([string]$candidate) {
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    return (Get-Location).Path
  }
  $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
  if ($resolved) { return $resolved.Path }
  return $candidate
}

function Find-Executable([string]$name) {
  $found = Get-Command -Name $name -CommandType Application, Filter, Function, Cmdlet -ErrorAction SilentlyContinue
  if ($found) { return $found.Source }
  $exts = @($env:PATHEXT -split ";")
  foreach ($dir in ($env:PATH -split ";")) {
    $full = Join-Path $dir "$name$ext"
    foreach ($ext in $exts) {
      $candidate = Join-Path $dir "$name$ext"
      if (Test-Path -LiteralPath $candidate) {
        return (Get-Item -LiteralPath $candidate).FullName
      }
    }
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

function New-ProcessArgs(
  [string]$cmd,
  [string[]]$args,
  [hashtable]$env,
  [string]$cwd
) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $cmd
  $psi.Arguments = ($args -join " ")
  $psi.WorkingDirectory = $cwd
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  foreach ($kv in $env.GetEnumerator()) {
    $psi.Environment[$kv.Key] = $kv.Value
  }
  return $psi
}

function Start-ServiceProcess(
  [string]$name,
  [string]$cmd,
  [string[]]$args,
  [hashtable]$env,
  [string]$cwd,
  [string]$logDir
) {
  $psi = New-ProcessArgs -cmd $cmd -args $args -env $env -cwd $cwd
  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi
  $proc.EnableRaisingEvents = $true
  $null = $proc.Start()

  $logFile = Join-Path $logDir "${name}.log"
  $pid = $proc.Id

  Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived `
    -Action {
      param($sender, $e)
      if ($sender -and $sender.Handle -and $sender.Handle -ne [IntPtr]::Zero -and
          -not $sender.HasExited) {
        Add-Content -LiteralPath $logFile -Value $e.Data -ErrorAction SilentlyContinue
      }
    } | Out-Null

  Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived `
    -Action {
      param($sender, $e)
      if ($sender -and $sender.Handle -and $sender.Handle -ne [IntPtr]::Zero -and
          -not $sender.HasExited) {
        Add-Content -LiteralPath $logFile -Value $e.Data -ErrorAction SilentlyContinue
      }
    } | Out-Null

  $proc.BeginOutputReadLine()
  $proc.BeginErrorReadLine()
  return $proc
}

function Wait-ServiceReady(
  [string]$url,
  [int]$attempts = 40,
  [int]$intervalMs = 500
) {
  for ($i = 0; $i -lt $attempts; $i++) {
    try {
      $resp = Invoke-WebRequest -UseBasicParsing -Method Head -Uri $url -TimeoutSec 2 -ErrorAction SilentlyContinue
      if ($resp -and $resp.StatusCode -and
          ($resp.StatusCode -eq 200 -or $resp.StatusCode -eq 204 -or
           $resp.StatusCode -eq 301 -or $resp.StatusCode -eq 302 -or
           $resp.StatusCode -eq 400 -or $resp.StatusCode -eq 404 -or
           $resp.StatusCode -eq 405)) {
        return $true
      }
    } catch {}
    Start-Sleep -Milliseconds $intervalMs
  }
  return $false
}

$repoDir = Resolve-RepoDir $RepoDir
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

$nodeModules = Join-Path $repoDir "frontend\node_modules"
if (-not (Test-Path -LiteralPath $nodeModules)) {
  Fail-Closed "prerequisite missing: frontend/node_modules (run npm install manually before dev-up)"
}

foreach ($port in @($FrontendPort, $TaskApiPort, $ModelControlPort)) {
  if (Is-PortInUse $port) {
    $pid = Get-PortProcess $port
    $hint = ""
    if ($pid) { $hint = " (process ${pid})" }
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
  "REVERSE_AGENT_REPO_DIR" = $repoDir
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
  -cmd $py -args @("-m", "reverse_agent.model_access.service") `
  -env $modelControlEnv -cwd $repoDir -logDir $runtimeDir

$taskProc = Start-ServiceProcess `
  -name "task-api" `
  -cmd $py -args @("-m", "reverse_agent.platform_v1.task_service") `
  -env $taskApiEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 1500

if (-not $modelProc.HasExited) {
  if (-not (Wait-ServiceReady -url "$ModelControlUrl/api/model-profiles")) {
    $modelProc.Kill() | Out-Null
    Fail-Closed "Model Control did not become healthy at ${ModelControlUrl}"
  }
} else {
  Fail-Closed "Model Control exited before health check"
}

if (-not $taskProc.HasExited) {
  if (-not (Wait-ServiceReady -url "${TaskApiUrl}/api/tasks")) {
    $taskProc.Kill() | Out-Null
    $modelProc.Kill() | Out-Null
    Fail-Closed "Task API did not become healthy at ${TaskApiUrl}"
  }
} else {
  $modelProc.Kill() | Out-Null
  Fail-Closed "Task API exited before health check"
}

$frontendProc = Start-ServiceProcess `
  -name "frontend-vite" `
  -cmd $npm -args @("--prefix", "frontend", "run", "dev") `
  -env $frontendEnv -cwd $repoDir -logDir $runtimeDir

Start-Sleep -Milliseconds 1500

if (-not $frontendProc.HasExited) {
  if (-not (Wait-ServiceReady -url "$FrontendUrl/")) {
    $frontendProc.Kill() | Out-Null
    $taskProc.Kill() | Out-Null
    $modelProc.Kill() | Out-Null
    Fail-Closed "Frontend did not become healthy at ${FrontendUrl}"
  }
} else {
  $taskProc.Kill() | Out-Null
  $modelProc.Kill() | Out-Null
  Fail-Closed "Frontend exited before health check"
}

$record = [ordered]@{
  created_at = (Get-Date -Format o)
  repo_dir = $repoDir
  open_code_model = $OpenCodeModel
  children = @(
    [ordered]@{ name = "model-control"; pid = $modelProc.Id; cmd = "$py -m reverse_agent.model_access.service"; url = $ModelControlUrl },
    [ordered]@{ name = "task-api"; pid = $taskProc.Id; cmd = "$py -m reverse_agent.platform_v1.task_service"; url = $TaskApiUrl },
    [ordered]@{ name = "frontend-vite"; pid = $frontendProc.Id; cmd = "$npm --prefix frontend run dev"; url = $FrontendUrl }
  )
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
