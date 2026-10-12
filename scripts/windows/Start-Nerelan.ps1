<#
.SYNOPSIS
  Double-click entry for Nerelan on Windows: start (or reopen) the local stack without a console.

.DESCRIPTION
  Runs dev-up.ps1 from the repository root while a small "starting" window is shown, then
  closes it once the Nerelan client window is up. dev-up reuses a healthy stack and repairs a
  stale one (for example after the client window was closed), so a second double-click
  reopens Nerelan. Output goes to %LOCALAPPDATA%\Nerelan\launcher.log; on failure a message
  box points to that log instead of failing silently. On the first launch of a checkout whose
  frontend dependencies are missing, it installs them once from the lockfile (npm ci); no
  other packages are installed and no model is called.
#>
$ErrorActionPreference = "Stop"

$repoDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$devUp = Join-Path $repoDir "dev-up.ps1"
$logDir = Join-Path $env:LOCALAPPDATA "Nerelan"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "launcher.log"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Nerelan"
$form.FormBorderStyle = "FixedDialog"
$form.StartPosition = "CenterScreen"
$form.ClientSize = New-Object System.Drawing.Size(320, 96)
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true
$icon = Join-Path $repoDir "assets\windows\nerelan.ico"
if (Test-Path -LiteralPath $icon) { $form.Icon = New-Object System.Drawing.Icon($icon) }
$label = New-Object System.Windows.Forms.Label
$label.Text = "Nerelan 正在启动…"
$label.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 11)
$label.AutoSize = $true
$label.Location = New-Object System.Drawing.Point(24, 18)
$bar = New-Object System.Windows.Forms.ProgressBar
$bar.Style = "Marquee"
$bar.Location = New-Object System.Drawing.Point(24, 56)
$bar.Size = New-Object System.Drawing.Size(272, 14)
$form.Controls.AddRange(@($label, $bar))
$form.Show()

function Wait-Hidden([string]$file, [string[]]$arguments, [string]$workingDirectory) {
  $child = Start-Process -FilePath $file -WindowStyle Hidden -PassThru -WorkingDirectory $workingDirectory `
    -RedirectStandardOutput $log -RedirectStandardError "$log.err" -ArgumentList $arguments
  # Windows PowerShell 5.1 reports ExitCode as $null unless the process handle was opened.
  $null = $child.Handle
  while (-not $child.HasExited) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 100
  }
  return $child.ExitCode
}

$frontend = Join-Path $repoDir "frontend"
if (-not (Test-Path -LiteralPath (Join-Path $frontend "node_modules\.bin\vite.cmd"))) {
  $label.Text = "首次启动：正在安装前端依赖…"
  $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
  $installed = if ($npm) { Wait-Hidden "cmd.exe" @("/d", "/c", "`"$npm`" ci --no-audit --no-fund") $frontend } else { -1 }
  if ($installed -ne 0) {
    $form.Close()
    [System.Windows.Forms.MessageBox]::Show(
      "Nerelan 首次启动需要安装前端依赖，但安装失败（需要 Node.js 与网络）。`r`n`r`n完整日志：$log",
      "Nerelan", "OK", "Error") | Out-Null
    exit 1
  }
  $label.Text = "Nerelan 正在启动…"
}

$process = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput $log -RedirectStandardError "$log.err" `
  -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $devUp, "-RepoDir", $repoDir)
# Windows PowerShell 5.1 reports ExitCode as $null unless the process handle was opened.
$null = $process.Handle
while (-not $process.HasExited) {
  [System.Windows.Forms.Application]::DoEvents()
  Start-Sleep -Milliseconds 100
}
$form.Close()

if ($process.ExitCode -ne 0) {
  $tail = ""
  foreach ($file in @("$log.err", $log)) {
    if (Test-Path -LiteralPath $file) {
      $lines = Get-Content -LiteralPath $file -Tail 8 -Encoding UTF8 -ErrorAction SilentlyContinue
      if ($lines) { $tail = ($lines -join "`r`n"); break }
    }
  }
  [System.Windows.Forms.MessageBox]::Show(
    "Nerelan 启动失败（退出码 $($process.ExitCode)）。`r`n`r`n$tail`r`n`r`n完整日志：$log",
    "Nerelan", "OK", "Error") | Out-Null
  exit $process.ExitCode
}
