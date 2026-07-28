from __future__ import annotations

import json
from pathlib import Path

from reverse_agent.mainline_landing import integration_baseline


REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_state(tmp_path: Path) -> tuple[Path, dict]:
    state_dir = tmp_path / "project_state"
    target = state_dir / "integration_baselines"
    target.mkdir(parents=True)
    source = (
        REPO_ROOT
        / "project_state"
        / "integration_baselines"
        / "architecture_spine_v1.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    return state_dir, payload


def test_committed_architecture_spine_baseline_passes() -> None:
    result = integration_baseline(
        state_dir=REPO_ROOT / "project_state",
        repo_root=REPO_ROOT,
    )
    assert result["gate_status"] == "PASSED"
    assert result["baseline_id"] == "architecture_spine_v1"
    assert result["merge_commit_sha"] == "38de9106d191d6b66d5f878354144817095e7bca"


def test_baseline_rejects_parent_identity_tampering(tmp_path: Path) -> None:
    state_dir, payload = _copy_state(tmp_path)
    payload["previous_main_sha"] = payload["subject_head_sha"]
    path = state_dir / "integration_baselines" / "architecture_spine_v1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = integration_baseline(state_dir=state_dir, repo_root=REPO_ROOT)
    assert result["gate_status"] == "BLOCKED"
    assert any("merge_parent_identity" in item for item in result["blocking_reasons"])


def test_baseline_rejects_wrong_required_run_set(tmp_path: Path) -> None:
    state_dir, payload = _copy_state(tmp_path)
    payload["successful_exact_head_runs"][0]["name"] = "Unknown"
    path = state_dir / "integration_baselines" / "architecture_spine_v1.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = integration_baseline(state_dir=state_dir, repo_root=REPO_ROOT)
    assert result["gate_status"] == "BLOCKED"
    assert any("required_run_names" in item for item in result["blocking_reasons"])


def test_baseline_rejects_missing_artifact(tmp_path: Path) -> None:
    result = integration_baseline(
        state_dir=tmp_path / "project_state",
        repo_root=REPO_ROOT,
    )
    assert result["gate_status"] == "BLOCKED"
    assert result["checks"] == []
