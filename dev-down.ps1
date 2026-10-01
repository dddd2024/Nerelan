<#
.SYNOPSIS
  Stop the dev-up children recorded by the most recent dev-up run.

.DESCRIPTION
  Reads .platform_v1_runtime/devup_pids.json and stops only the exact child
  process trees created by the matching dev-up invocation. It verifies each
  recorded PID against its expected executable identity before terminating.

  Only the exact owned PID tree is stopped. No image-wide or name-wide kill
  is ever performed. For cmd.exe-wrapped children (npm.cmd -> cmd.exe -> node)
  taskkill /PID /T is attempted with captured diagnostics. Verified process
  handles stop the captured owned tree when taskkill cannot do so.

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
  [string]$RepoDir = "",
  [switch]$FunctionsOnly
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

function Compare-ProcessStartTime([object]$recordedStartTimeStr, [datetime]$actualStartTime) {
  if ([string]::IsNullOrWhiteSpace($recordedStartTimeStr)) {
    return $false
  }
  if ($recordedStartTimeStr -is [datetime]) { $recordedStartTimeStr = $recordedStartTimeStr.ToString("o") }
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

function Get-OwnedProcessTree([System.Diagnostics.Process]$root) {
  # Snapshot parent links without WMI. Keep handles open: a recycled PID must
  # never cause termination of the replacement process.
  if (-not ("NerelanProcessParents" -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class NerelanProcessParents {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  private struct Entry {
    public uint size, usage, pid; public UIntPtr heap;
    public uint module, threads, parent; public int priority; public uint flags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string exe;
  }
  [DllImport("kernel32.dll", SetLastError=true)]
  private static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint pid);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  private static extern bool Process32FirstW(IntPtr snapshot, ref Entry entry);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  private static extern bool Process32NextW(IntPtr snapshot, ref Entry entry);
  [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
  public static Dictionary<int,int> Snapshot() {
    IntPtr h=CreateToolhelp32Snapshot(2,0);
    if(h==new IntPtr(-1)) throw new System.ComponentModel.Win32Exception();
    try {
      var result=new Dictionary<int,int>(); var e=new Entry();
      e.size=(uint)Marshal.SizeOf(typeof(Entry));
      if(!Process32FirstW(h,ref e)) throw new System.ComponentModel.Win32Exception();
      do { result[(int)e.pid]=(int)e.parent; } while(Process32NextW(h,ref e));
      if(Marshal.GetLastWin32Error()!=18) throw new System.ComponentModel.Win32Exception();
      return result;
    } finally { CloseHandle(h); }
  }
}
'@
  }
  $null = $root.Handle
  $parents = [NerelanProcessParents]::Snapshot()
  $verified = @{ $root.Id = $root }
  $handles = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
  $handles.Add($root)
  try {
    $changed = $true
    while ($changed) {
      $changed = $false
      foreach ($childId in $parents.Keys) {
        if ($verified.ContainsKey($childId) -or -not $verified.ContainsKey($parents[$childId])) { continue }
        $parent = $verified[$parents[$childId]]
        if ($parent.HasExited) { throw "Parent exited before descendant identity could be verified" }
        $child = Get-Process -Id $childId -ErrorAction SilentlyContinue
        if (-not $child) { continue }
        try {
          $null = $child.Handle
          $childExe = $child.MainModule.FileName
          if ([string]::IsNullOrWhiteSpace($childExe)) { throw "Descendant executable identity is unreadable" }
          # Older children can refer to a recycled parent PID; refuse that edge.
          if ($child.StartTime.ToUniversalTime() -lt $parent.StartTime.ToUniversalTime()) { continue }
          $verified[$childId] = $child
          $handles.Add($child)
          $changed = $true
        } catch {
          $child.Dispose()
          throw
        }
      }
    }
    return ,$handles
  } catch {
    foreach ($owned in $handles) { $owned.Dispose() }
    throw
  }
}

function Invoke-OwnedTreeStop([System.Diagnostics.Process]$proc) {
  # Establish and retain the exact process handle before taskkill. The fallback
  # has the same caller privileges and only traverses verified descendant edges.
  $null = $proc.Handle
  $ownedTree = Get-OwnedProcessTree $proc
  $task = [System.Diagnostics.Process]::new()
  $task.StartInfo.FileName = Join-Path $env:SystemRoot "System32\taskkill.exe"
  $task.StartInfo.Arguments = "/PID $($proc.Id) /T /F"
  $task.StartInfo.UseShellExecute = $false
  $task.StartInfo.CreateNoWindow = $true
  $task.StartInfo.RedirectStandardOutput = $true
  $task.StartInfo.RedirectStandardError = $true
  try {
    $null = $task.Start()
    $outTask = $task.StandardOutput.ReadToEndAsync()
    $errTask = $task.StandardError.ReadToEndAsync()
    if (-not $task.WaitForExit(10000)) {
      $task.Kill()
      throw "taskkill timed out"
    }
    $diagnostic = [ordered]@{
      taskkill_exit_code = $task.ExitCode
      taskkill_stdout = $outTask.GetAwaiter().GetResult()
      taskkill_stderr = $errTask.GetAwaiter().GetResult()
      stop_method = "taskkill"
    }
    # Parents first prevents the captured creators from spawning new children.
    foreach ($owned in $ownedTree) {
      if (-not $owned.HasExited) {
        $diagnostic.stop_method = "verified_process_handles"
        $owned.Kill()
        if (-not $owned.WaitForExit(5000)) { throw "Verified process did not exit: $($owned.Id)" }
      }
    }
    return $diagnostic
  } finally {
    $task.Dispose()
    foreach ($owned in $ownedTree) { $owned.Dispose() }
  }
}


if ($FunctionsOnly) { return }

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
    start_time = $recordedStartTime
    wrapped = $wrapped
    stop_diagnostics = $null
  }

  if (-not $expectedPid) {
    $result.outcome = "already_exited"
    return $result
  }

  $proc = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
  if (-not $proc) {
    $result.outcome = "already_exited"
    Write-Host "dev-down: ${name} (pid ${expectedPid}) already exited"
    return $result
  }

  $actualExe = $null
  try {
    $null = $proc.Handle
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
      # taskkill failure is captured; fallback uses held exact process identities.
      $result.stop_diagnostics = Invoke-OwnedTreeStop $proc
      Start-Sleep -Milliseconds 500
      $stillHere = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
      if (-not $stillHere) {
        $result.outcome = "stopped"
        Write-Host "dev-down: stopped ${name} (pid ${expectedPid}) and children"
      } else {
        $result.outcome = "stop_failed"
        Write-Warning "dev-down: ${name} (pid ${expectedPid}) still running after taskkill"
      }
    } else {
      $proc.WaitForExit(3000) | Out-Null
      if (-not $proc.HasExited) {
        $proc.Kill()
        $proc.WaitForExit(5000) | Out-Null
      }
      $result.outcome = "stopped"
      Write-Host "dev-down: stopped ${name} (pid ${expectedPid})"
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
    start_time = $r.start_time
    wrapped = $r.wrapped
    stop_diagnostics = $r.stop_diagnostics
  }
}

$shutdownState = [ordered]@{
  stopped_at = (Get-Date -Format o)
  repo_dir = $state.repo_dir
  source_dir = $state.source_dir
  children = @($updatedChildren)
}

$shutdownState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $pidFile -Encoding UTF8
Write-Output "dev-down: done"
if (@($stopResults | Where-Object { $_.outcome -eq "stop_failed" -or $_.outcome -eq "refused_identity_mismatch" }).Count -gt 0) { exit 1 }
