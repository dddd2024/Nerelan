$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$expectedBranch = "agent/frontend-v1-openhands-ui"
$expectedBase = "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507"
$remoteRef = "refs/remotes/origin/$expectedBranch"

$branch = (git branch --show-current).Trim()
if ($branch -ne $expectedBranch) {
    throw "Expected branch '$expectedBranch', observed '$branch'."
}

$status = git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}
if ($status) {
    throw "Working tree is not clean. Preserve local changes before verification.`n$status"
}

Write-Host "==> refresh remote branch identity" -ForegroundColor Cyan
& git fetch origin $expectedBranch
if ($LASTEXITCODE -ne 0) {
    throw "git fetch origin $expectedBranch failed."
}

$head = (git rev-parse HEAD).Trim()
$remoteHead = (git rev-parse $remoteRef).Trim()
if ($head -ne $remoteHead) {
    throw "Local HEAD '$head' does not match remote PR Head '$remoteHead'. Synchronize without discarding local work, then rerun."
}

$commands = @(
    @{ Name = "frontend tests"; Args = @("--prefix", "frontend", "test") },
    @{ Name = "frontend typecheck"; Args = @("--prefix", "frontend", "run", "typecheck") },
    @{ Name = "frontend lint"; Args = @("--prefix", "frontend", "run", "lint") },
    @{ Name = "frontend production build"; Args = @("--prefix", "frontend", "run", "build") },
    @{ Name = "frontend mock build"; Args = @("--prefix", "frontend", "run", "build:mock") }
)

$results = @()
foreach ($entry in $commands) {
    Write-Host "`n==> $($entry.Name)" -ForegroundColor Cyan
    & npm @($entry.Args)
    $exitCode = $LASTEXITCODE
    $results += [pscustomobject]@{
        Check = $entry.Name
        ExitCode = $exitCode
    }
    if ($exitCode -ne 0) {
        throw "$($entry.Name) failed with exit code $exitCode."
    }
}

Write-Host "`n==> diff check" -ForegroundColor Cyan
& git diff --check "$expectedBase..HEAD"
$diffExitCode = $LASTEXITCODE
$results += [pscustomobject]@{
    Check = "git diff --check"
    ExitCode = $diffExitCode
}
if ($diffExitCode -ne 0) {
    throw "git diff --check failed with exit code $diffExitCode."
}

$finalStatus = git status --short
if ($LASTEXITCODE -ne 0) {
    throw "Final git status failed."
}
if ($finalStatus) {
    throw "Verification changed tracked or untracked repository state.`n$finalStatus"
}

Write-Host "`nVerification summary" -ForegroundColor Green
Write-Host "Branch:      $branch"
Write-Host "Local Head:  $head"
Write-Host "Remote Head: $remoteHead"
$results | Format-Table -AutoSize

Write-Host "FRONTEND_V1_EXACT_HEAD_VERIFICATION_PASSED" -ForegroundColor Green
