<#
.SYNOPSIS
  Stop the dev-up children recorded by the most recent dev-up run.

.DESCRIPTION
  Reads .platform_v1_runtime/devup_pids.json and stops only the exact child
  process trees created by the matching dev-up invocation. It verifies each
  recorded PID against its expected executable identity before terminating.

  Only the exact owned PID tree is stopped. No image-wide or name-wide kill
  is ever performed. For cmd.exe-wrapped children (npm.cmd -> cmd.exe -> node)
  a birth-bound Windows Job Object owns ordinary spawned descendants.
  Its active count, not root disappearance, proves completed shutdown.
  Legacy records without this binding return incomplete and retain identity.

  Per-child outcome is recorded truthfully:
    stopped                - process was stopped by this invocation
    already_exited         - root absent and owned job verified empty/stopped
    refused_identity_mismatch - process identity did not match record
    stop_failed            - stop was attempted but did not succeed

.NOTES
  A missing root alone cannot certify that its descendants exited. Runtime metadata
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

function Initialize-OwnedJobType {
  if ("NerelanOwnedJob" -as [type]) { return }
  Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
public sealed class NerelanJobLaunch {
  public Process Process; public string JobName; public int KeeperPid; public string KeeperStartTime;
}
public sealed class NerelanJobMember {
  public int pid; public string start_time; public string executable;
}
public static class NerelanOwnedJob {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  struct Startup {
    public int cb; public string reserved, desktop, title;
    public uint x,y,xSize,ySize,xChars,yChars,fill,flags;
    public ushort show,reservedSize; public IntPtr reservedBytes,input,output,error;
  }
  [StructLayout(LayoutKind.Sequential)]
  struct Info { public IntPtr process,thread; public uint pid,tid; }
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern bool CreateProcessW(string app,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref Startup startup,out Info info);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr CreateJobObjectW(IntPtr attributes,string name);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr OpenJobObjectW(uint access,bool inherit,string name);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
  [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int kind,IntPtr data,uint length,out uint returned);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool member);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetProcessTimes(IntPtr process,out long created,out long exit,out long kernel,out long user);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
  [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool DuplicateHandle(IntPtr sourceProcess,IntPtr sourceHandle,IntPtr targetProcess,out IntPtr targetHandle,uint access,bool inherit,uint options);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool QueryFullProcessImageNameW(IntPtr process,uint flags,StringBuilder name,ref uint size);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
  static long Birth(IntPtr process) {
    long c,e,k,u; if(!GetProcessTimes(process,out c,out e,out k,out u)) throw new Win32Exception(); return c;
  }
  public static NerelanJobLaunch Start(string app,string arguments,string cwd) {
    var si=new Startup(); si.cb=Marshal.SizeOf(typeof(Startup));
    Info pi; Info keeper=new Info(); IntPtr job=IntPtr.Zero; bool resumed=false;
    // CREATE_SUSPENDED | CREATE_NO_WINDOW, bInheritHandles=false. No breakaway.
    if(!CreateProcessW(app,new StringBuilder("\""+app+"\" "+arguments),IntPtr.Zero,IntPtr.Zero,false,0x08000004,IntPtr.Zero,cwd,ref si,out pi)) throw new Win32Exception();
    try {
      string name="Local\\Nerelan-devup-"+pi.pid+"-"+Birth(pi.process)+"-"+Guid.NewGuid().ToString("N");
      job=CreateJobObjectW(IntPtr.Zero,name); int error=Marshal.GetLastWin32Error();
      if(job==IntPtr.Zero || error==183) throw new Win32Exception(error);
      // No BREAKAWAY_OK or KILL_ON_JOB_CLOSE: the group survives the launcher.
      if(!AssignProcessToJobObject(job,pi.process)) throw new Win32Exception();
      // A dedicated member holds a duplicated job handle across launcher/root
      // exit. Ordinary children may disable handle inheritance. The keeper has
      // no stdio inheritance and is terminated by the same job, never by PID.
      string keeperApp=Environment.GetEnvironmentVariable("SystemRoot")+"\\System32\\WindowsPowerShell\\v1.0\\powershell.exe";
      var keeperCommand=new StringBuilder("\""+keeperApp+"\" -NoProfile -NonInteractive -Command \"while($true){Start-Sleep -Seconds 60}\"");
      if(!CreateProcessW(keeperApp,keeperCommand,IntPtr.Zero,IntPtr.Zero,false,0x08000004,IntPtr.Zero,cwd,ref si,out keeper)) throw new Win32Exception();
      if(!AssignProcessToJobObject(job,keeper.process)) throw new Win32Exception();
      IntPtr keeperHandle;
      if(!DuplicateHandle(GetCurrentProcess(),job,keeper.process,out keeperHandle,0,false,2)) throw new Win32Exception();
      if(ResumeThread(keeper.thread)==UInt32.MaxValue) throw new Win32Exception();
      var process=Process.GetProcessById((int)pi.pid); var held=process.Handle;
      if(ResumeThread(pi.thread)==UInt32.MaxValue) { process.Dispose(); throw new Win32Exception(); }
      resumed=true; return new NerelanJobLaunch { Process=process,JobName=name,KeeperPid=(int)keeper.pid,KeeperStartTime=DateTime.FromFileTimeUtc(Birth(keeper.process)).ToString("o") };
    } finally {
      bool stopped=true;
      if(!resumed) {
        stopped=TerminateProcess(pi.process,1);
        if(keeper.process!=IntPtr.Zero) stopped=TerminateProcess(keeper.process,1) && stopped;
      }
      if(keeper.thread!=IntPtr.Zero) CloseHandle(keeper.thread);
      if(keeper.process!=IntPtr.Zero) CloseHandle(keeper.process);
      if(job!=IntPtr.Zero) CloseHandle(job);
      CloseHandle(pi.thread); CloseHandle(pi.process);
      if(!stopped) throw new Win32Exception("Suspended fixture cleanup incomplete");
    }
  }
  public static IntPtr Open(string name) {
    IntPtr h=OpenJobObjectW(12,false,name);
    if(h==IntPtr.Zero && Marshal.GetLastWin32Error()!=2) throw new Win32Exception();
    return h;
  }
  public static bool Contains(IntPtr job,Process process) {
    bool member; if(!IsProcessInJob(process.Handle,job,out member)) throw new Win32Exception(); return member;
  }
  public static long Creation(Process process) { return Birth(process.Handle); }
  public static uint Active(IntPtr job) {
    IntPtr data=Marshal.AllocHGlobal(48);
    try {
      uint returned; if(!QueryInformationJobObject(job,1,data,48,out returned)) throw new Win32Exception();
      return (uint)Marshal.ReadInt32(data,40);
    } finally { Marshal.FreeHGlobal(data); }
  }
  public static NerelanJobMember[] Members(IntPtr job) {
    // Bounded evidence collection. A snapshot never authorizes termination.
    int length=8+4096*IntPtr.Size; IntPtr data=Marshal.AllocHGlobal(length);
    try {
      uint returned; if(!QueryInformationJobObject(job,3,data,(uint)length,out returned)) throw new Win32Exception();
      uint count=(uint)Marshal.ReadInt32(data,4);
      if(count>4096 || (uint)Marshal.ReadInt32(data)>count) throw new InvalidOperationException("Job membership exceeds evidence bound");
      var result=new List<NerelanJobMember>();
      for(int i=0;i<count;i++) {
        int pid=checked((int)Marshal.ReadIntPtr(data,8+i*IntPtr.Size).ToInt64());
        IntPtr process=OpenProcess(0x1000,false,pid);
        if(process==IntPtr.Zero) {
          if(Marshal.GetLastWin32Error()==87) continue;
          throw new Win32Exception();
        }
        try {
          bool member; if(!IsProcessInJob(process,job,out member)) throw new Win32Exception();
          if(!member) continue; // recycled PID is not a member, never a stop target
          uint size=32768; var exe=new StringBuilder((int)size);
          if(!QueryFullProcessImageNameW(process,0,exe,ref size) || size==0) throw new Win32Exception();
          result.Add(new NerelanJobMember {pid=pid,start_time=DateTime.FromFileTimeUtc(Birth(process)).ToString("o"),executable=exe.ToString()});
        } finally { CloseHandle(process); }
      }
      return result.ToArray();
    } finally { Marshal.FreeHGlobal(data); }
  }
  public static void Terminate(IntPtr job) { if(!TerminateJobObject(job,1)) throw new Win32Exception(); }
  public static void Close(IntPtr job) { if(job!=IntPtr.Zero) CloseHandle(job); }
}
'@
}

function Get-OwnedProcessTree([System.Diagnostics.Process]$root) {
  # Parent PID snapshots cannot certify process-instance ancestry.
  throw "Legacy PID snapshots do not establish owned-tree authority"
}

function Stop-OwnedJob([IntPtr]$job) { [NerelanOwnedJob]::Terminate($job) }
function Get-OwnedJobActiveCount([IntPtr]$job) { return [NerelanOwnedJob]::Active($job) }

function Invoke-OwnedTreeStop([System.Diagnostics.Process]$proc, [object]$child) {
  # Initialize before any side effect; failure always returns recoverable evidence.
  $diagnostic = [ordered]@{ stop_method = "windows_job"; completed = $false;
    job_name = $child.job_name; root_pid = $child.pid; root_start_time = $child.start_time;
    members_before = @(); active_remaining = $null; termination_requested = $false; error = $null }
  $job = [IntPtr]::Zero
  try {
    Initialize-OwnedJobType
    if (-not $child -or -not $child.job_name) { throw "Legacy tree has no birth-bound job; stop incomplete" }
    $recorded = if ($child.start_time -is [datetime]) { $child.start_time } else { [datetime]::Parse([string]$child.start_time, [cultureinfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind) }
    $birth = $recorded.ToUniversalTime().ToFileTimeUtc()
    $prefix = "Local\Nerelan-devup-$($child.pid)-${birth}-"
    if ($child.job_name -cnotmatch ('^' + [regex]::Escape($prefix) + '[0-9a-f]{32}$')) { throw "Job binding does not match recorded root identity" }
    if ($proc -and ($proc.Id -ne $child.pid -or [NerelanOwnedJob]::Creation($proc) -ne $birth)) { throw "Exact job root identity mismatch" }
    $job = [NerelanOwnedJob]::Open($child.job_name)
    if ($job -eq [IntPtr]::Zero) {
      if ($proc) { throw "Live root has no recorded job" }
      if (-not $child.stop_diagnostics -or -not $child.stop_diagnostics.completed) {
        throw "Job unavailable; root absence does not prove descendant exit"
      }
      $diagnostic.active_remaining = 0
      $diagnostic.completed = $true
      return $diagnostic
    }
    if ($proc -and -not [NerelanOwnedJob]::Contains($job, $proc)) { throw "Root is not in recorded job" }
    $diagnostic.members_before = @([NerelanOwnedJob]::Members($job))
    $diagnostic.active_remaining = Get-OwnedJobActiveCount $job
    Stop-OwnedJob $job
    $diagnostic.termination_requested = $true
    $deadline = [datetime]::UtcNow.AddSeconds(10)
    do {
      $diagnostic.active_remaining = Get-OwnedJobActiveCount $job
      if ($diagnostic.active_remaining -eq 0) { $diagnostic.completed = $true; break }
      Start-Sleep -Milliseconds 50
    } while ([datetime]::UtcNow -lt $deadline)
    if (-not $diagnostic.completed) { throw "Job members remain after termination" }
  } catch {
    $diagnostic.error = $_.Exception.Message
  } finally {
    if ($job -ne [IntPtr]::Zero) { [NerelanOwnedJob]::Close($job) }
  }
  return $diagnostic
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
    job_name = $child.job_name
    stop_diagnostics = $null
  }

  if (-not $expectedPid) {
    $result.outcome = "already_exited"
    return $result
  }

  $proc = Get-Process -Id $expectedPid -ErrorAction SilentlyContinue
  if (-not $proc -and $wrapped) {
    $result.stop_diagnostics = Invoke-OwnedTreeStop $null $child
    $result.outcome = if ($result.stop_diagnostics.completed) { "already_exited" } else { "stop_failed" }
    return $result
  }
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
      $result.stop_diagnostics = Invoke-OwnedTreeStop $proc $child
      if ($result.stop_diagnostics.completed) {
        $result.outcome = "stopped"
        Write-Host "dev-down: stopped ${name} (pid ${expectedPid}) and job members"
      } else {
        $result.outcome = "stop_failed"
        Write-Warning "dev-down: ${name} stop incomplete: $($result.stop_diagnostics.error)"
      }
    } else {
      $proc.WaitForExit(3000) | Out-Null
      if (-not $proc.HasExited) {
        $proc.Kill()
        if (-not $proc.WaitForExit(5000)) { throw "Verified process did not exit" }
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
    job_name = $r.job_name
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
