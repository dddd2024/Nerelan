$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$expectedBranch = "agent/frontend-v1-openhands-ui"
$expectedBase = "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507"

$branch = (git branch --show-current).Trim()
if ($branch -ne $expectedBranch) {
    throw "Expected branch '$expectedBranch', observed '$branch'."
}

$head = (git rev-parse HEAD).Trim()
$status = git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}
if ($status) {
    throw "Working tree is not clean. Preserve local changes before verification.`n$status"
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

Write-Host "`nVerification summary" -ForegroundColor Green
Write-Host "Branch: $branch"
Write-Host "Head:   $head"
$results | Format-Table -AutoSize

Write-Host "FRONTEND_V1_EXACT_HEAD_VERIFICATION_PASSED" -ForegroundColor Green
