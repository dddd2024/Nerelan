from __future__ import annotations

import json
from pathlib import Path

from tools.audit_codex_skills import audit_skills


def _write_skill(root: Path, name: str, body: str, *, scope: str = "generic_workflow") -> None:
    skill_dir = root / ".codex-skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Test skill.",
                "version: 2",
                "status: active",
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


def _minimal_entry(name: str, *, scope: str = "generic_workflow", path: str | None = None) -> dict[str, object]:
    return {
        "path": path or f".codex-skills/{name}/SKILL.md",
        "status": "active",
        "scope": scope,
        "version": 2,
    }


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
