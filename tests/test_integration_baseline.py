from __future__ import annotations

import json
from pathlib import Path

from reverse_agent.project_gate import integration_baseline


REPO_ROOT = Path(__file__).resolve().parents[1]


def _check(result: dict, name: str) -> dict:
    return next(item for item in result["checks"] if item["name"] == name)


def test_committed_architecture_spine_baseline_passes() -> None:
    result = integration_baseline(
        state_dir=REPO_ROOT / "project_state",
        repo_root=REPO_ROOT,
    )

    assert result["gate_status"] == "PASSED"
    assert result["baseline_id"] == "architecture_spine_v1"
    assert result["merge_commit_sha"] == "38de9106d191d6b66d5f878354144817095e7bca"
    assert result["subject_head_sha"] == "43418818af61d9be3208d2444fd6ce5120f73fab"
    assert result["blocking_reasons"] == []


def _copy_baseline_state(tmp_path: Path) -> tuple[Path, dict]:
    state_dir = tmp_path / "project_state"
    baseline_dir = state_dir / "integration_baselines"
    schema_dir = state_dir / "schemas"
    baseline_dir.mkdir(parents=True)
    schema_dir.mkdir(parents=True)
    schema_path = REPO_ROOT / "project_state" / "schemas" / "integration_baseline.schema.json"
    receipt_path = (
        REPO_ROOT
        / "project_state"
        / "integration_baselines"
        / "architecture_spine_v1.json"
    )
    schema_dir.joinpath("integration_baseline.schema.json").write_bytes(schema_path.read_bytes())
    return state_dir, json.loads(receipt_path.read_text(encoding="utf-8"))


def test_baseline_rejects_parent_identity_tampering(tmp_path: Path) -> None:
    state_dir, receipt = _copy_baseline_state(tmp_path)
    receipt["previous_main_sha"] = receipt["subject_head_sha"]
    state_dir.joinpath("integration_baselines", "architecture_spine_v1.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )

    result = integration_baseline(state_dir=state_dir, repo_root=REPO_ROOT)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "merge_parent_identity")["status"] == "FAIL"


def test_baseline_rejects_schema_additional_property(tmp_path: Path) -> None:
    state_dir, receipt = _copy_baseline_state(tmp_path)
    receipt["untrusted_override"] = True
    state_dir.joinpath("integration_baselines", "architecture_spine_v1.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )

    result = integration_baseline(state_dir=state_dir, repo_root=REPO_ROOT)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "schema_valid")["status"] == "FAIL"


def test_transition_workflows_route_main_to_baseline_gate() -> None:
    for name in ("state-gate.yml", "decision-preflight.yml"):
        text = (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        preflight_block = next(
            block for block in text.split("\n\n") if "name: Transition preflight" in block
        )
        baseline_block = next(
            block for block in text.split("\n\n") if "name: Main integration baseline" in block
        )
        assert "github.ref != 'refs/heads/main'" in preflight_block
        assert "github.ref == 'refs/heads/main'" in baseline_block
        assert "integration-baseline --state-dir project_state" in baseline_block
