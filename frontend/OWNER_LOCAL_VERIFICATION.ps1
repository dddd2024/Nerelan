$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$expectedBranch = "owner/model-access-frontend-closeout-v1"
$expectedBase = "68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d"
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
    throw "Local HEAD '$head' does not match remote Head '$remoteHead'. Synchronize and rerun."
}

$checks = @(
    @{ Name = "model access Python tests"; Command = "python"; Args = @("-m", "pytest", "tests/test_model_access.py", "-q") },
    @{ Name = "frontend tests"; Command = "npm"; Args = @("--prefix", "frontend", "test") },
    @{ Name = "frontend typecheck"; Command = "npm"; Args = @("--prefix", "frontend", "run", "typecheck") },
    @{ Name = "frontend lint"; Command = "npm"; Args = @("--prefix", "frontend", "run", "lint") },
    @{ Name = "frontend production build"; Command = "npm"; Args = @("--prefix", "frontend", "run", "build") },
    @{ Name = "frontend mock build"; Command = "npm"; Args = @("--prefix", "frontend", "run", "build:mock") }
)

$results = @()
foreach ($entry in $checks) {
    Write-Host "`n==> $($entry.Name)" -ForegroundColor Cyan
    & $entry.Command @($entry.Args)
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
    throw "Verification changed repository state.`n$finalStatus"
}

Write-Host "`nVerification summary" -ForegroundColor Green
Write-Host "Branch:      $branch"
Write-Host "Local Head:  $head"
Write-Host "Remote Head: $remoteHead"
$results | Format-Table -AutoSize

Write-Host "MODEL_ACCESS_EXACT_HEAD_VERIFICATION_PASSED" -ForegroundColor Green
