[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Tauri-only build bridge for the Nerelan desktop shell.
#
# The desktop build must address the local services by absolute loopback URL:
# the shell has no native /api proxy, so the relative fallback used by
# model-control-client would resolve against the tauri:// origin and fail.
# This bridge pins both base URLs for the existing frontend build and does not
# touch frontend/src.

$TaskApiBase = "http://127.0.0.1:8766"
$ModelControlBase = "http://127.0.0.1:8765/api"

$restoreTask = $env:VITE_TASK_API_BASE
$restoreModel = $env:VITE_MODEL_CONTROL_API_BASE

$env:VITE_TASK_API_BASE = $TaskApiBase
$env:VITE_MODEL_CONTROL_API_BASE = $ModelControlBase

Write-Output "tauri-desktop-build: VITE_TASK_API_BASE=${TaskApiBase}"
Write-Output "tauri-desktop-build: VITE_MODEL_CONTROL_API_BASE=${ModelControlBase}"

& npm run build
$buildExit = $LASTEXITCODE

if ($null -eq $restoreTask) {
  Remove-Item Env:\VITE_TASK_API_BASE -ErrorAction SilentlyContinue
} else {
  $env:VITE_TASK_API_BASE = $restoreTask
}
if ($null -eq $restoreModel) {
  Remove-Item Env:\VITE_MODEL_CONTROL_API_BASE -ErrorAction SilentlyContinue
} else {
  $env:VITE_MODEL_CONTROL_API_BASE = $restoreModel
}

exit $buildExit
