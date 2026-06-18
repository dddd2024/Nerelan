"""Static/schema tests for the first local reverse static triage queue.

These tests validate a planning artifact only. They do not execute samples,
tools, solvers, harnesses, debuggers, IDA, Ghidra, or runtime probes.
"""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT / "project_state" / "local_reverse_first_static_triage_queue.json"
COVERAGE_PATH = ROOT / "project_state" / "local_reverse_training_coverage_matrix.json"
CONTRACT_PATH = ROOT / "project_state" / "local_reverse_static_type_tag_contract.json"

DECISION_ID = "decision_20260618_training_first_static_triage_queue_v1"
ROUND_ID = "round_20260618_training_first_static_triage_queue_v1"

REQUIRED_ITEM_FIELDS = {
    "queue_id",
    "type_id",
    "sample_id",
    "selection_source",
    "metadata_confidence",
    "coverage_status_before_triage",
    "why_selected",
    "required_static_evidence",
    "allowed_existing_routes",
    "forbidden_actions",
    "expected_next_artifacts",
    "promotion_rule",
    "stop_condition",
}

PRIMARY_SAMPLE_BEARING_TYPES = {
    "string_comparison",
    "xor",
    "shift_affine",
    "lookup_table",
    "rc4",
    "des",
    "hash_md5_sha",
    "simple_antidebug",
    "mixed_unknown",
}


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def queue() -> dict:
    return _load_json(QUEUE_PATH)


@pytest.fixture(scope="module")
def coverage() -> dict:
    return _load_json(COVERAGE_PATH)


@pytest.fixture(scope="module")
def contract() -> dict:
    return _load_json(CONTRACT_PATH)


def _coverage_sample_ids(coverage: dict) -> dict[str, set[str]]:
    return {
        row["type_id"]: set(row.get("sample_ids", []))
        for row in coverage["type_rows"]
    }


def test_queue_file_exists_and_binds_decision(queue: dict) -> None:
    assert QUEUE_PATH.exists()
    assert queue["schema_version"] == 1
    assert queue["decision_id"] == DECISION_ID
    assert queue["round_id"] == ROUND_ID
    assert queue["queue_policy"]["mainline"] == "training_dataset"
    assert queue["queue_policy"]["no_runtime_or_tool_execution_this_round"] is True
    assert queue["queue_policy"]["no_reverse_agent_source_changes_this_round"] is True


def test_queue_has_required_top_level_sections(queue: dict) -> None:
    for key in [
        "schema_version",
        "decision_id",
        "round_id",
        "based_on_artifacts",
        "queue_policy",
        "queued_items",
        "blocked_categories",
        "limitations",
    ]:
        assert key in queue


def test_each_queue_item_has_required_schema(queue: dict) -> None:
    assert queue["queued_items"]
    for item in queue["queued_items"]:
        assert REQUIRED_ITEM_FIELDS <= item.keys()
        assert isinstance(item["required_static_evidence"], list) and item["required_static_evidence"]
        assert isinstance(item["allowed_existing_routes"], list) and item["allowed_existing_routes"]
        assert isinstance(item["forbidden_actions"], list) and item["forbidden_actions"]
        assert isinstance(item["expected_next_artifacts"], list) and item["expected_next_artifacts"]
        assert "metadata" in item["metadata_confidence"]


def test_primary_sample_bearing_types_are_covered_once(queue: dict) -> None:
    items_by_type = {}
    for item in queue["queued_items"]:
        items_by_type.setdefault(item["type_id"], []).append(item)

    assert set(items_by_type) == PRIMARY_SAMPLE_BEARING_TYPES
    assert all(len(items) == 1 for items in items_by_type.values())
    assert "bit_operations" not in items_by_type


def test_selected_samples_come_from_coverage_matrix(queue: dict, coverage: dict) -> None:
    samples_by_row = _coverage_sample_ids(coverage)
    for item in queue["queued_items"]:
        row_type = item["selection_source"]["coverage_matrix_type_id"]
        assert item["sample_id"] in samples_by_row[row_type]


def test_blocked_no_sample_categories(queue: dict, coverage: dict) -> None:
    blocked = {item["type_id"]: item for item in queue["blocked_categories"]}
    assert set(blocked) == {"tea_xtea", "base64", "gui_validation"}
    for item in blocked.values():
        assert item["reason"] == "blocked_no_current_sample"
        assert item["sample_count"] == 0
        assert item["coverage_matrix_type_id"] in _coverage_sample_ids(coverage)


def test_no_name_only_or_metadata_only_upgrade_claims(queue: dict) -> None:
    forbidden_terms = [
        "static_verified",
        "runtime_validated",
        "solved",
        "ida_executed",
        "ghidra_executed",
        "sample_executed",
    ]
    policy_claims = set(queue["queue_policy"]["forbidden_claims"])
    assert set(forbidden_terms) <= policy_claims

    text = json.dumps(queue, ensure_ascii=False).lower()
    assert "all queued items remain metadata_only" in text
    assert "filename" in text
    assert "solver script naming alone never promotes confidence" in text


def test_hash_item_requires_bounded_domain(queue: dict) -> None:
    item = next(item for item in queue["queued_items"] if item["type_id"] == "hash_md5_sha")
    assert item["bounded_domain_required"] is True
    combined = " ".join(item["forbidden_actions"] + item["required_static_evidence"]).lower()
    assert "bounded" in combined
    assert "unbounded_bruteforce" in item["forbidden_actions"]


def test_lookup_table_item_records_support_gap(queue: dict) -> None:
    item = next(item for item in queue["queued_items"] if item["type_id"] == "lookup_table")
    assert item["queue_readiness"] == "needs_static_triage_field_support_or_manual_static_evidence"
    assert "claim_tool_ready_when_tool_evidence_available_is_false" in item["forbidden_actions"]


def test_bit_operations_is_secondary_only(queue: dict) -> None:
    secondary_mentions = [
        item for item in queue["queued_items"]
        if "bit_operations" in item.get("secondary_tags", [])
    ]
    assert secondary_mentions
    assert all(item["type_id"] != "bit_operations" for item in queue["queued_items"])
    assert queue["queue_policy"]["bit_operations_policy"] == "secondary_cross_cutting_tag_only_in_this_queue"


def test_required_static_evidence_aligns_with_contract(queue: dict, contract: dict) -> None:
    contract_tags = contract["tags"]
    for item in queue["queued_items"]:
        contract_requirements = " ".join(contract_tags[item["type_id"]]["evidence_requirements"]).lower()
        item_requirements = " ".join(item["required_static_evidence"]).lower()
        assert any(word in item_requirements for word in contract_requirements.split() if len(word) > 8)
        assert "filename" not in item["promotion_rule"].lower()


def test_limitations_confirm_no_execution_or_source_changes(queue: dict) -> None:
    limitations = " ".join(queue["limitations"]).lower()
    assert "no sample" in limitations
    assert "no sample, solver, harness, ida, ghidra, debugger" in limitations
    assert "reverse_agent" not in [path.split("/", 1)[0] for path in queue["based_on_artifacts"]]
