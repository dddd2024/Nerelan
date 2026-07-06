import json
from pathlib import Path

from reverse_agent.round_compaction import (
    build_round_compaction_bundle,
    build_round_compaction_dry_run,
    build_round_compaction_plan,
    validate_round_compaction_bundle,
)


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    previous_round = "round_prev"
    (state_dir / "rounds" / previous_round).mkdir(parents=True)
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "decision_20260705_governance_operations_bundle_big_step_v1",
  "round_id": "round_20260705_governance_operations_bundle_big_step_v1",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "follows_last_accepted_round_id": "{previous_round}",
  "supersedes_unexecuted_decision_id": "decision_cleanup_apply_review_bundle_v1"
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "rounds" / previous_round / "round_manifest.json").write_text(
        json.dumps({"round_id": previous_round}),
        encoding="utf-8",
    )


def test_round_compaction_plan_is_bounded_and_dry_run_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    plan = build_round_compaction_plan(state_dir=state_dir)
    dry_run, manifest = build_round_compaction_dry_run(state_dir=state_dir, plan=plan)
    bundle = build_round_compaction_bundle(state_dir=state_dir)

    assert plan["recursive_rounds_scan"] is False
    assert plan["compaction_apply_allowed"] is False
    assert dry_run["archive_written"] is False
    assert dry_run["files_deleted"] == []
    assert manifest["real_manifest_written"] is False
    assert manifest["compaction_apply_allowed"] is False
    assert bundle["gate_status"] == "PASSED"
    assert validate_round_compaction_bundle(bundle) == []
