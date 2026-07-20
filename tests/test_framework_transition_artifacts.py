from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "project_state"
GATES = STATE / "gates"


def _load(relative: str) -> dict:
    path = ROOT / relative
    assert path.is_file(), f"missing required artifact: {relative}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_required_transition_artifacts_and_schemas_parse() -> None:
    artifacts = [
        "project_state/gates/pr5_capability_inventory.json",
        "project_state/gates/pr5_migration_disposition.json",
        "project_state/gates/framework_authority_matrix.json",
        "project_state/gates/transition_baseline_recommendation.json",
        "project_state/gates/selective_migration_manifest.json",
        "project_state/context/framework_transition_packet.json",
        "project_state/roadmap/workstreams.json",
    ]
    schemas = [
        "project_state/schemas/pr5_capability_inventory.schema.json",
        "project_state/schemas/pr5_migration_disposition.schema.json",
        "project_state/schemas/framework_transition_packet.schema.json",
    ]
    for relative in artifacts:
        assert _load(relative)["schema_version"] == 1
    for relative in schemas:
        schema = _load(relative)
        assert schema["$schema"].endswith("2020-12/schema")
        assert schema["type"] == "object"
        assert schema["required"]


def test_inventory_ids_dispositions_and_changed_file_coverage() -> None:
    inventory = _load("project_state/gates/pr5_capability_inventory.json")
    disposition = _load("project_state/gates/pr5_migration_disposition.json")
    capabilities = inventory["capabilities"]
    ids = [record["capability_id"] for record in capabilities]
    assert len(ids) == len(set(ids))
    assert inventory["material_changed_file_count"] == len(inventory["material_changed_files"]) == 88

    covered = {path for record in capabilities for path in record["pr5_files"]}
    assert covered == set(inventory["material_changed_files"])

    allowed = {
        "KEEP_AS_IS", "KEEP_AND_ADAPT", "REPLACE_WITH_BMAD",
        "REPLACE_WITH_LANGGRAPH", "REPLACE_WITH_GITHUB",
        "MOVE_TO_TRUST_LAYER", "ARCHIVE_ONLY", "DROP",
    }
    records = disposition["records"]
    assert {record["capability_id"] for record in records} == set(ids)
    assert all(record["primary_disposition"] in allowed for record in records)
    assert all(isinstance(record["primary_disposition"], str) for record in records)


def test_inventory_references_are_current_main_or_pr5_evidence() -> None:
    inventory = _load("project_state/gates/pr5_capability_inventory.json")
    pr5_paths = set(inventory["material_changed_files"])
    for record in inventory["capabilities"]:
        for relative in record["main_files"]:
            assert (ROOT / relative).exists(), f"missing main reference: {relative}"
        for relative in record["pr5_files"]:
            assert relative in pr5_paths, f"unproven PR5 reference: {relative}"
        for relative in record["pr5_only_files"]:
            assert relative in pr5_paths or any(
                path.startswith(relative.rstrip("/") + "/") for path in pr5_paths
            ), f"unproven PR5-only reference: {relative}"


def test_authority_matrix_has_one_owner_and_one_runtime() -> None:
    matrix = _load("project_state/gates/framework_authority_matrix.json")
    required = {
        "product_discovery_and_prd", "architecture_and_story_definition",
        "engineering_work_item", "workflow_runtime_state", "checkpoint_and_resume",
        "branch_commit_pr_review", "ci_and_release_truth", "high_risk_authorization",
        "command_allowlist", "binary_observation", "claim_and_counterevidence",
        "validation_status", "audit_history",
    }
    classes = [entry["fact_class"] for entry in matrix["authorities"]]
    assert set(classes) == required
    assert len(classes) == len(set(classes))
    assert all(entry["primary_owner"] for entry in matrix["authorities"])
    assert matrix["single_primary_runtime"] == "LANGGRAPH"
    assert matrix["dual_primary_runtime_prohibited"] is True
    bmad_classes = {
        entry["fact_class"] for entry in matrix["authorities"]
        if entry["primary_owner"] == "BMAD"
    }
    assert bmad_classes <= {"product_discovery_and_prd", "architecture_and_story_definition"}


def test_baseline_and_selective_manifest_are_bounded() -> None:
    baseline = _load("project_state/gates/transition_baseline_recommendation.json")
    assert baseline["selection"] in {"CURRENT_MAIN", "PR5", "SELECTIVE_INTEGRATION_BASELINE"}
    assert baseline["selection"] == "SELECTIVE_INTEGRATION_BASELINE"
    assert baseline["first_implementation_round"]["decision_id"] == (
        "decision_20260720_selective_capability_integration_v1"
    )

    inventory = _load("project_state/gates/pr5_capability_inventory.json")
    known = {record["capability_id"] for record in inventory["capabilities"]}
    manifest = _load("project_state/gates/selective_migration_manifest.json")
    assert all(entry["capability_id"] in known for entry in manifest["entries"])
    assert {entry["action"] for entry in manifest["entries"]} <= {
        "KEEP", "ADAPT", "ARCHIVE", "DROP"
    }


def test_transition_workstreams_are_acyclic_and_only_disposition_is_active() -> None:
    registry = _load("project_state/roadmap/workstreams.json")
    transition = {
        item["workstream_id"]: item for item in registry["workstreams"]
        if item.get("family") == "framework_transition"
    }
    expected = {
        "legacy-control-plane-disposition", "selective-capability-integration",
        "bmad-planning-adapter", "langgraph-shadow-runtime", "github-truth-adapter",
        "trust-layer-schema-foundation", "web-workbench-transition",
    }
    assert set(transition) == expected
    active = [
        item["workstream_id"] for item in registry["workstreams"]
        if item["status"] == "ACTIVE_ROUND"
    ]
    assert active == ["legacy-control-plane-disposition"]

    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node: str) -> None:
        assert node not in visiting, f"cycle at {node}"
        if node in visited:
            return
        visiting.add(node)
        for dependency in transition[node].get("depends_on", []):
            assert dependency in transition
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for workstream_id in transition:
        visit(workstream_id)
    assert visited == expected


def test_pr5_is_frozen_and_v10_is_not_accepted_or_reopened() -> None:
    inventory = _load("project_state/gates/pr5_capability_inventory.json")
    disposition = _load("project_state/gates/pr5_migration_disposition.json")
    packet = _load("project_state/context/framework_transition_packet.json")
    expected_head = "6a2867467c90cf37929787be3ba6061fcbb81312"
    assert inventory["pr5_audited_head_sha"] == expected_head
    assert packet["frozen_pr5_head_sha"] == expected_head
    assert inventory["pr5_state"] == "FROZEN_MIGRATION_EVIDENCE"
    assert disposition["v10_audit_outcome"] == "REWORK_REQUIRED"
    assert disposition["legacy_micro_rework_authorized"] is False
    assert packet["prohibitions"]["framework_installation"] is True
    assert packet["prohibitions"]["legacy_micro_rework"] is True
    assert packet["prohibitions"]["dual_primary_runtime"] is True
