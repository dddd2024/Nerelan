param(
    [string]$SourceRoot,
    [string]$DestinationRoot,
    [string[]]$SkillName = @(),
    [switch]$List,
    [switch]$Check,
    [switch]$DryRun,
    [switch]$IncludeDeprecated
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
if (-not $SourceRoot) {
    $SourceRoot = Join-Path $repoRoot ".codex-skills"
}
if (-not $DestinationRoot) {
    $codexHome = $env:CODEX_HOME
    if (-not $codexHome) {
        $codexHome = Join-Path $env:USERPROFILE ".codex"
    }
    $DestinationRoot = Join-Path $codexHome "skills"
}

function Get-RepoRootForSource {
    param([string]$SourceRootPath)

    $sourceItem = Get-Item -LiteralPath $SourceRootPath
    if ($sourceItem.Name -eq ".codex-skills") {
        return $sourceItem.Parent.FullName
    }
    return $repoRoot
}

function Resolve-SkillPath {
    param(
        [string]$EntryPath,
        [string]$SourceRootPath,
        [string]$SourceRepoRoot
    )

    if ([System.IO.Path]::IsPathRooted($EntryPath)) {
        return $EntryPath
    }

    $candidates = @(
        (Join-Path $SourceRepoRoot $EntryPath),
        (Join-Path $repoRoot $EntryPath),
        (Join-Path $SourceRootPath $EntryPath)
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return (Join-Path $SourceRepoRoot $EntryPath)
}

function Get-LegacySkillCandidates {
    param([string]$SourceRootPath)

    Write-Warning "Skill registry not found; falling back to legacy directory scan."
    $dirs = Get-ChildItem -LiteralPath $SourceRootPath -Directory | Where-Object {
        Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md")
    }
    $candidates = @()
    foreach ($dir in $dirs) {
        $candidates += [pscustomobject]@{
            Name = $dir.Name
            Status = "active"
            Scope = ""
            Version = ""
            SkillPath = Join-Path $dir.FullName "SKILL.md"
            SourceDir = $dir.FullName
            RegistryPath = ""
        }
    }
    return $candidates
}

function Get-RegistrySkillCandidates {
    param(
        [string]$SourceRootPath,
        [switch]$IncludeDeprecatedSkills
    )

    $registryPath = Join-Path $SourceRootPath "registry.json"
    if (-not (Test-Path -LiteralPath $registryPath)) {
        return Get-LegacySkillCandidates -SourceRootPath $SourceRootPath
    }

    $sourceRepoRoot = Get-RepoRootForSource -SourceRootPath $SourceRootPath
    $registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
    if (-not $registry.skills) {
        throw "Skill registry missing skills object: $registryPath"
    }

    $candidates = @()
    $skillNames = $registry.skills.PSObject.Properties.Name | Sort-Object
    foreach ($name in $skillNames) {
        $entry = $registry.skills.$name
        $status = [string]$entry.status
        if ($status -eq "archived") {
            continue
        }
        if ($status -eq "deprecated" -and -not $IncludeDeprecatedSkills) {
            continue
        }
        if ($status -ne "active" -and $status -ne "deprecated") {
            continue
        }

        $entryPath = [string]$entry.path
        if (-not $entryPath) {
            throw "Skill registry entry missing path: $name"
        }
        $skillPath = Resolve-SkillPath -EntryPath $entryPath -SourceRootPath $SourceRootPath -SourceRepoRoot $sourceRepoRoot
        if (-not (Test-Path -LiteralPath $skillPath)) {
            throw "Registered skill path not found for $name`: $entryPath"
        }
        if ((Split-Path -Leaf $skillPath) -ne "SKILL.md") {
            throw "Registered skill path must point to SKILL.md for $name`: $entryPath"
        }

        $candidates += [pscustomobject]@{
            Name = $name
            Status = $status
            Scope = [string]$entry.scope
            Version = [string]$entry.version
            SkillPath = $skillPath
            SourceDir = Split-Path -Parent $skillPath
            RegistryPath = $entryPath
        }
    }
    return $candidates
}

function Select-SkillCandidates {
    param(
        [object[]]$Candidates,
        [string[]]$WantedNames
    )

    if ($WantedNames.Count -eq 0) {
        return $Candidates
    }

    $candidateByName = @{}
    foreach ($candidate in $Candidates) {
        $candidateByName[$candidate.Name] = $candidate
    }

    $missing = @()
    $selected = @()
    foreach ($name in $WantedNames) {
        if ($candidateByName.ContainsKey($name)) {
            $selected += $candidateByName[$name]
        } else {
            $missing += $name
        }
    }
    if ($missing.Count -gt 0) {
        throw "Requested skill not found or not eligible: $($missing -join ', ')"
    }
    return $selected
}

function Invoke-SkillAudit {
    param([string]$SourceRootPath)

    $registryPath = Join-Path $SourceRootPath "registry.json"
    if (-not (Test-Path -LiteralPath $registryPath)) {
        Write-Error "Skill registry not found for -Check: $registryPath"
        exit 1
    }

    $sourceRepoRoot = Get-RepoRootForSource -SourceRootPath $SourceRootPath
    $auditScript = Join-Path $repoRoot "tools\audit_codex_skills.py"
    & python $auditScript --repo-root $sourceRepoRoot
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path -LiteralPath $SourceRoot)) {
    throw "Skill source root not found: $SourceRoot"
}
$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path

if ($Check) {
    Invoke-SkillAudit -SourceRootPath $SourceRoot
}

$candidates = @(Get-RegistrySkillCandidates -SourceRootPath $SourceRoot -IncludeDeprecatedSkills:$IncludeDeprecated)
$candidates = @(Select-SkillCandidates -Candidates $candidates -WantedNames $SkillName)

if ($List) {
    foreach ($candidate in $candidates) {
        Write-Host ("{0}`tstatus={1}`tscope={2}`tversion={3}`tpath={4}" -f $candidate.Name, $candidate.Status, $candidate.Scope, $candidate.Version, $candidate.RegistryPath)
    }
    if ($candidates.Count -eq 0) {
        Write-Host "No skills matched."
    }
}

if ($DryRun) {
    foreach ($candidate in $candidates) {
        $dest = Join-Path $DestinationRoot $candidate.Name
        Write-Host "Would sync skill $($candidate.Name) -> $dest"
    }
    if ($candidates.Count -eq 0) {
        Write-Host "No skills matched."
    }
}

if ($List -or $DryRun -or $Check) {
    return
}

New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null

foreach ($candidate in $candidates) {
    $dest = Join-Path $DestinationRoot $candidate.Name
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Get-ChildItem -LiteralPath $candidate.SourceDir -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse -Force
    }
    Write-Host "Synced skill $($candidate.Name) -> $dest"
}

if ($candidates.Count -eq 0) {
    Write-Host "No skills matched."
}
