from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.audit_codex_skills import audit_skills


def _write_skill(
    root: Path,
    name: str,
    body: str,
    *,
    scope: str = "generic_workflow",
    status: str = "active",
) -> None:
    skill_dir = root / ".codex-skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Test skill.",
                "version: 2",
                f"status: {status}",
                f"scope: {scope}",
                "owner: project_state",
                'last_reviewed: "2026-05-24"',
                "---",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )


def _write_registry(root: Path, entries: dict[str, dict[str, object]]) -> None:
    registry_dir = root / ".codex-skills"
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.joinpath("registry.json").write_text(
        json.dumps({"schema_version": 1, "skills": entries}, indent=2),
        encoding="utf-8",
    )


def _minimal_entry(
    name: str,
    *,
    scope: str = "generic_workflow",
    status: str = "active",
    path: str | None = None,
) -> dict[str, object]:
    return {
        "path": path or f".codex-skills/{name}/SKILL.md",
        "status": status,
        "scope": scope,
        "version": 2,
    }


def _powershell() -> str:
    shell = shutil.which("powershell") or shutil.which("pwsh")
    if not shell:
        pytest.skip("PowerShell is not available")
    return shell


def _run_sync(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    shell = _powershell()
    command = [shell]
    if Path(shell).name.lower() == "powershell.exe":
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(["-File", str(repo_root / "tools" / "sync_codex_skills.ps1")])
    command.extend(args)
    return subprocess.run(
        command,
        cwd=cwd or repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_sync_fixture(root: Path) -> Path:
    _write_skill(root, "active-skill", "Active body.")
    _write_skill(root, "deprecated-skill", "Deprecated body.", status="deprecated")
    _write_skill(root, "archived-skill", "Archived body.", status="archived")
    _write_registry(
        root,
        {
            "active-skill": _minimal_entry("active-skill"),
            "deprecated-skill": _minimal_entry("deprecated-skill", status="deprecated"),
            "archived-skill": _minimal_entry("archived-skill", status="archived"),
        },
    )
    return root / ".codex-skills"


def test_current_repo_skill_audit_passes() -> None:
    result = audit_skills(Path(__file__).resolve().parents[1])

    assert result["status"] == "passed"
    assert result["skills_checked"] >= 2
    assert result["errors"] == []


def test_missing_registry_path_fails(tmp_path: Path) -> None:
    _write_registry(tmp_path, {"missing-skill": _minimal_entry("missing-skill")})

    result = audit_skills(tmp_path)

    assert result["status"] == "failed"
    assert any("registered path does not exist" in error for error in result["errors"])


def test_default_project_progress_log_read_fails(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "bad-progress",
        "Start every iteration by reading the tail of PROJECT_PROGRESS_LOG.txt.",
    )
    _write_registry(tmp_path, {"bad-progress": _minimal_entry("bad-progress")})

    result = audit_skills(tmp_path)

    assert result["status"] == "failed"
    assert any("PROJECT_PROGRESS_LOG" in error for error in result["errors"])


def test_default_newest_harness_run_read_fails(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "bad-harness",
        "Inspect the newest solve_reports/harness_runs/* directory before planning.",
    )
    _write_registry(tmp_path, {"bad-harness": _minimal_entry("bad-harness")})

    result = audit_skills(tmp_path)

    assert result["status"] == "failed"
    assert any("solve_reports" in error for error in result["errors"])


def test_sample_profile_dynamic_facts_fail(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "bad-sample",
        "\n".join(
            [
                "Current candidate is 78d540b49c59077041414141414141.",
                "Latest run is samplereverse_exact1_borderline_escape_20260423.",
                "Read solve_reports\\tool_artifacts\\sample\\result.json first.",
            ]
        ),
        scope="sample_profile",
    )
    _write_registry(tmp_path, {"bad-sample": _minimal_entry("bad-sample", scope="sample_profile")})

    result = audit_skills(tmp_path)

    assert result["status"] == "failed"
    assert any("long hex" in error for error in result["errors"])
    assert any("dated run name" in error for error in result["errors"])
    assert any("direct solve_reports artifact path" in error for error in result["errors"])


def test_negative_guardrail_phrasing_is_allowed(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        "guardrail",
        "\n".join(
            [
                "Do not scan full solve_reports/ by default.",
                "Read PROJECT_PROGRESS_LOG.txt only when compact state is missing.",
                "Do not inspect the newest solve_reports/harness_runs/* directory merely because it exists.",
            ]
        ),
    )
    _write_registry(tmp_path, {"guardrail": _minimal_entry("guardrail")})

    result = audit_skills(tmp_path)

    assert result["status"] == "passed"
    assert result["errors"] == []


def test_sync_list_and_dry_run_do_not_create_destination(tmp_path: Path) -> None:
    source_root = _write_sync_fixture(tmp_path)
    destination = tmp_path / "dest"

    listed = _run_sync("-SourceRoot", str(source_root), "-DestinationRoot", str(destination), "-List")

    assert listed.returncode == 0, listed.stderr
    assert "active-skill" in listed.stdout
    assert "deprecated-skill" not in listed.stdout
    assert "archived-skill" not in listed.stdout
    assert not destination.exists()

    dry_run = _run_sync(
        "-SourceRoot",
        str(source_root),
        "-DestinationRoot",
        str(destination),
        "-DryRun",
        "-SkillName",
        "active-skill",
    )

    assert dry_run.returncode == 0, dry_run.stderr
    assert "Would sync skill active-skill" in dry_run.stdout
    assert not destination.exists()


def test_sync_default_copies_only_active_and_preserves_unknown_local_skill(tmp_path: Path) -> None:
    source_root = _write_sync_fixture(tmp_path)
    destination = tmp_path / "dest"
    unknown = destination / "unknown-local-skill"
    unknown.mkdir(parents=True)
    unknown.joinpath("SKILL.md").write_text("local only\n", encoding="utf-8")

    synced = _run_sync("-SourceRoot", str(source_root), "-DestinationRoot", str(destination))

    assert synced.returncode == 0, synced.stderr
    assert (destination / "active-skill" / "SKILL.md").exists()
    assert not (destination / "deprecated-skill").exists()
    assert not (destination / "archived-skill").exists()
    assert (unknown / "SKILL.md").exists()


def test_sync_include_deprecated_and_skill_name_filter(tmp_path: Path) -> None:
    source_root = _write_sync_fixture(tmp_path)
    destination = tmp_path / "dest"

    synced = _run_sync(
        "-SourceRoot",
        str(source_root),
        "-DestinationRoot",
        str(destination),
        "-IncludeDeprecated",
        "-SkillName",
        "deprecated-skill",
    )

    assert synced.returncode == 0, synced.stderr
    assert not (destination / "active-skill").exists()
    assert (destination / "deprecated-skill" / "SKILL.md").exists()
    assert not (destination / "archived-skill").exists()


def test_sync_missing_skill_name_fails(tmp_path: Path) -> None:
    source_root = _write_sync_fixture(tmp_path)
    destination = tmp_path / "dest"

    synced = _run_sync(
        "-SourceRoot",
        str(source_root),
        "-DestinationRoot",
        str(destination),
        "-SkillName",
        "missing-skill",
    )

    assert synced.returncode != 0
    assert "missing-skill" in synced.stderr
    assert not destination.exists()


def test_sync_check_uses_audit_and_does_not_create_destination(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    destination = tmp_path / "dest"

    checked = _run_sync(
        "-SourceRoot",
        str(repo_root / ".codex-skills"),
        "-DestinationRoot",
        str(destination),
        "-Check",
    )

    assert checked.returncode == 0, checked.stderr
    assert '"status": "passed"' in checked.stdout
    assert not destination.exists()
