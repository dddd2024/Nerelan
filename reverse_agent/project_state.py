from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .function_semantics import FUNCTION_SEMANTIC_AUDIT_FILE_NAME
from .sidecar_health import classify_observation_delivery


IMPORTANT_ARTIFACTS = {
    "compare_aware_result": "samplereverse_compare_aware_result.json",
    "frontier_summary": "samplereverse_compare_aware_frontier_summary.json",
    "strata_summary": "samplereverse_compare_aware_strata_summary.json",
    "guided_pool_result": "samplereverse_compare_aware_guided_pool_result.json",
    "guided_pool_validation": "samplereverse_compare_aware_guided_pool_validation.json",
    "smt_result": "samplereverse_compare_aware_smt_result.json",
    "smt_validation": "samplereverse_compare_aware_smt_validation.json",
    "transform_trace_consistency": "transform_trace_consistency.json",
    "dynamic_compare_path_probe": "dynamic_compare_path_probe.json",
    "pre_rc4_material_probe": "pre_rc4_material_probe.json",
    "base64_rc4_static_point_discovery": "base64_rc4_static_point_discovery.json",
    "base64_rc4_breakpoint_probe": "base64_rc4_breakpoint_probe.json",
    "compare_stack_pivot_probe": "compare_stack_pivot_probe.json",
    "compare_handoff_probe": "compare_handoff_probe.json",
    "compare_handoff_slice_probe": "compare_handoff_slice_probe.json",
    "compare_handoff_return_site_probe": "compare_handoff_return_site_probe.json",
    "compare_producer_trace_probe": "compare_producer_trace_probe.json",
    "compare_producer_material_confirmation": "compare_producer_material_confirmation.json",
    "compare_pre_compare_handoff_target_probe": "compare_pre_compare_handoff_target_probe.json",
    "function_semantic_audit": FUNCTION_SEMANTIC_AUDIT_FILE_NAME,
    "material_hook_runtime_validation": "material_hook_runtime_validation.json",
    "post_handoff_branch_outcome_audit": "post_handoff_branch_outcome_audit.json",
    "post_handoff_exception_unwind_audit": "post_handoff_exception_unwind_audit.json",
    "compare_hook_path_reachability_audit": "compare_hook_path_reachability_audit.json",
    "compare_handoff_exit_classifier_audit": "compare_handoff_exit_classifier_audit.json",
    "compare_handoff_path_divergence_audit": "compare_handoff_path_divergence_audit.json",
    "compare_handoff_edge_operand_provenance_audit": "compare_handoff_edge_operand_provenance_audit.json",
    "compare_handoff_branch_operand_runtime_audit": "compare_handoff_branch_operand_runtime_audit.json",
    "compare_handoff_hook_surface_repair_audit": "compare_handoff_hook_surface_repair_audit.json",
    "compare_handoff_post_entry_step_runtime_audit": "compare_handoff_post_entry_step_runtime_audit.json",
    "compare_handoff_narrower_post_entry_breakpoint_audit": (
        "compare_handoff_narrower_post_entry_breakpoint_audit.json"
    ),
    "compare_lhs_producer_audit": "compare_lhs_producer_audit.json",
    "compare_lhs_upstream_writer_audit": "compare_lhs_upstream_writer_audit.json",
    "compare_callsite_reanchor_and_lhs_provenance_audit": (
        "compare_callsite_reanchor_and_lhs_provenance_audit.json"
    ),
    "compare_real_lhs_provenance_audit": "compare_real_lhs_provenance_audit.json",
    "compare_esi_source_window_audit": "compare_esi_source_window_audit.json",
    "compare_lhs_slot_writer_source_audit": "compare_lhs_slot_writer_source_audit.json",
    "compare_lhs_slot_writer_predecessor_audit": "compare_lhs_slot_writer_predecessor_audit.json",
    "profile_transform_hypothesis_matrix": "profile_transform_hypothesis_matrix.json",
    "h1_h3_boundary_validation": "h1_h3_boundary_validation.json",
    "exact2_basin_value_pool_result": "samplereverse_exact2_basin_value_pool_result.json",
    "exact2_basin_value_pool_validation": "samplereverse_exact2_basin_value_pool_validation.json",
    "pairscan_summary": "pairscan_summary.json",
    "bridge_search_result": "bridge_search_result.json",
    "bridge_validation": "bridge_validation.json",
    "checkpoint": "samplereverse_search_checkpoint.json",
    "summary": "summary.json",
    "run_manifest": "run_manifest.json",
}

LATEST_ARTIFACT_KEYS = tuple(IMPORTANT_ARTIFACTS.keys()) + (
    "compare_probe",
    "compare_probe_log",
)

RUNTIME_VALIDATION_KEYS = {
    "guided_pool_validation",
    "h1_h3_boundary_validation",
    "exact2_basin_value_pool_validation",
    "smt_validation",
    "bridge_validation",
    "compare_probe",
    "dynamic_compare_path_probe",
    "pre_rc4_material_probe",
    "base64_rc4_breakpoint_probe",
    "compare_stack_pivot_probe",
    "compare_handoff_probe",
    "compare_handoff_slice_probe",
    "compare_handoff_return_site_probe",
    "compare_producer_trace_probe",
    "compare_producer_material_confirmation",
    "compare_pre_compare_handoff_target_probe",
    "material_hook_runtime_validation",
    "post_handoff_branch_outcome_audit",
    "post_handoff_exception_unwind_audit",
    "compare_hook_path_reachability_audit",
    "compare_handoff_exit_classifier_audit",
    "compare_handoff_path_divergence_audit",
    "compare_handoff_edge_operand_provenance_audit",
    "compare_handoff_branch_operand_runtime_audit",
    "compare_handoff_hook_surface_repair_audit",
    "compare_handoff_post_entry_step_runtime_audit",
    "compare_handoff_narrower_post_entry_breakpoint_audit",
    "compare_lhs_producer_audit",
    "compare_lhs_upstream_writer_audit",
    "compare_callsite_reanchor_and_lhs_provenance_audit",
    "compare_real_lhs_provenance_audit",
    "compare_esi_source_window_audit",
    "compare_lhs_slot_writer_source_audit",
    "compare_lhs_slot_writer_predecessor_audit",
}

STATE_JSON_NAMES = (
    "artifact_index.json",
    "current_state.json",
    "negative_results.json",
    "model_gate.json",
    "task_packet.json",
)
STATE_MARKDOWN_NAMES = (
    "decision_packet.md",
    "codex_execution_report.md",
)
ARCHIVE_STATE_NAMES = (*STATE_JSON_NAMES, *STATE_MARKDOWN_NAMES)
ARCHIVE_MINIMAL_NAMES = STATE_MARKDOWN_NAMES
ARCHIVE_STATE_SNAPSHOT_NAMES = STATE_JSON_NAMES
ARCHIVE_OPTIONAL_NAMES = (*STATE_JSON_NAMES, "git_diff.patch")
ARCHIVE_MANIFEST_NAME = "round_manifest.json"
ARCHIVE_MINIMAL_ALLOWED_NAMES = (*ARCHIVE_MINIMAL_NAMES, "pytest_result.txt", ARCHIVE_MANIFEST_NAME)
ARCHIVE_REQUIRED_NAMES = ("codex_execution_report.md", "pytest_result.txt")
ARCHIVE_FORBIDDEN_NAMES = ("git_diff.patch", *ARCHIVE_STATE_SNAPSHOT_NAMES)
DEFAULT_STATE_DIR = Path("project_state")
DEFAULT_SAMPLE = "samplereverse"
DEFAULT_REPORTS_DIR = Path("solve_reports")
DEFAULT_PROGRESS_LOG = Path("PROJECT_PROGRESS_LOG.txt")
DEFAULT_PACK_NAME = "gpt_context_pack.zip"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA_VERSION = 2
DEFAULT_WORKFLOW_STATUS = "REPORT_AVAILABLE"
DEFAULT_CURRENT_OWNER = "web_gpt"
DEFAULT_REVIEW_STATUS = "PENDING_REVIEW"
STATE_SCOPE_SAMPLE = "sample_state"
TASK_SOURCE_DERIVED_FROM_SAMPLE_ARTIFACTS = "derived_from_sample_artifacts"
ACTIVE_DECISION_PACKET = "project_state/decision_packet.md"
EXECUTION_SCOPE_DECISION_PACKET_CONTROLS_CURRENT_ROUND = "decision_packet_controls_current_round"
STATE_PACKAGE_CLASSIFICATION_ORDER = (
    "authoritative",
    "advisory",
    "derived_cache",
    "archive",
    "heavy_history",
)
STATE_DIGEST_EXCLUDED_KEYS = {
    "generated_at",
    "round_id",
    "state_build_id",
    "state_digest",
}
DECISION_META_BLOCK_NAME = "decision_meta"
CODEX_REPORT_SUMMARY_BLOCK_NAME = "codex_report_summary"
PYTEST_RESULT_SUMMARY_BLOCK_NAME = "pytest_result_summary"
DECISION_STATUSES = {
    "TEMPLATE_ONLY",
    "DRAFT",
    "APPROVED",
    "SUPERSEDED",
    "UNKNOWN",
}
CODEX_REPORT_STATUSES = {
    "TEMPLATE_ONLY",
    "SUCCESS",
    "PARTIAL",
    "FAILED",
    "BLOCKED",
    "UNKNOWN",
}
CODEX_REPORT_ACCEPTANCE_RECOMMENDATIONS = {
    "ACCEPTED",
    "REWORK_REQUIRED",
    "BLOCKED",
    "NEEDS_REVIEW",
    "UNKNOWN",
}
PYTEST_RESULT_STATUSES = {"PASSED", "FAILED", "PARTIAL", "UNKNOWN"}
SKILL_PROFILE_RE = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9_-]*)@v(?P<version>\d+)(?P<draft>-draft)?$")

LEGACY_DECISION_PACKET_TEMPLATE = """# DECISION_PACKET

## Goal
本轮只做什么。

## Current Evidence
当前证据摘要。

## Do Not Do
禁止重复方向。

## Files To Inspect
Codex 优先审计的文件。

## Required Audit
Codex 执行前必须确认的内容。

## Implementation Scope
允许修改哪些文件。

## Tests
必须运行哪些测试。

## Stop Conditions
遇到什么情况必须停止并报告。
"""

LEGACY_CODEX_EXECUTION_REPORT_TEMPLATE = """# CODEX_EXECUTION_REPORT

## Summary
本轮做了什么。

## Files Changed
修改文件列表。

## Audit Result
审计发现。

## Implementation
实际实现内容。

## Tests
运行的测试命令和结果。

## Generated State Files
生成了哪些 project_state 文件。

## Problems / Uncertainty
仍然不确定的地方。

## Next Suggested Task
下一轮建议。
"""

DECISION_PACKET_TEMPLATE = """```json decision_meta
{
  "schema_version": 1,
  "decision_id": "",
  "round_id": "",
  "based_on_state_build_id": "",
  "based_on_state_digest": "",
  "status": "TEMPLATE_ONLY"
}
```

# DECISION_PACKET

## Goal
本轮只做什么。

## Current Evidence
当前证据摘要。

## Do Not Do
禁止重复方向。

## Files To Inspect
Codex 优先审计的文件。

## Required Audit
Codex 执行前必须确认的内容。

## Implementation Scope
允许修改哪些文件。

## Tests
必须运行哪些测试。

## Stop Conditions
遇到什么情况必须停止并报告。
"""

CODEX_EXECUTION_REPORT_TEMPLATE = """```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "",
  "round_id": "",
  "based_on_decision_id": "",
  "status": "TEMPLATE_ONLY",
  "acceptance_recommendation": "UNKNOWN",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "verified_artifacts": [],
  "next_suggested_task": ""
}
```

# CODEX_EXECUTION_REPORT

## Summary
本轮做了什么。

## Files Changed
修改文件列表。

## Audit Result
审计发现。

## Implementation
实际实现内容。

## Tests
运行的测试命令和结果。

## Generated State Files
生成了哪些 project_state 文件。

## Problems / Uncertainty
仍然不确定的地方。

## Next Suggested Task
下一轮建议。
"""

PROJECT_STATE_README = """# Project State

This directory is the lightweight collaboration interface between web GPT and Codex.

- `task_packet.json`, `current_state.json`, `artifact_index.json`, `negative_results.json`, and `model_gate.json` are compact state files generated by Codex.
- `decision_packet.md` is the handoff written by web GPT.
- `codex_execution_report.md` is the execution report written by Codex.
- `rounds/` stores archived snapshots for prior rounds.

Commit this directory to GitHub. Do not commit `solve_reports/`, local executable samples, `.env`, API keys, or large runtime logs.
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _path_for_json(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _read_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _derive_sidecar_observation_blocker(payload: dict[str, Any]) -> str:
    rows = _dict_rows(payload.get("candidate_execution_health"))
    if not rows:
        rows = _dict_rows(payload.get("candidate_results"))
    if not rows:
        return ""

    if any(_int_value(row.get("post_ui_observation_count")) > 0 for row in rows):
        return "arg0_ui_trigger_timing_fixed_observations_available"
    return classify_observation_delivery(rows)


def _derive_real_lhs_writer_blocker(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("lhs_writer_classification_blocker") or "").strip()
    sidecar_blocker = _derive_sidecar_observation_blocker(payload)
    if (
        explicit == "ui_trigger_executed_but_compare_arg_observation_missing"
        and sidecar_blocker
        and sidecar_blocker != explicit
    ):
        return sidecar_blocker
    if explicit and explicit != "arg0_ui_trigger_or_timeout_blocked":
        return explicit
    final_trace = _derive_arg0_final_data_writer_trace(payload)
    final_classification = str(final_trace.get("classification") or "").strip()
    final_blockers = {
        "final_writer_identified": "arg0_final_data_writer_identified",
        "pointer_chain_identified_writer_missing": "arg0_pointer_chain_identified_writer_missing",
        "final_writer_trace_schema_gap": "arg0_final_writer_trace_schema_gap",
        "writer_not_observed_in_bounded_window": "arg0_final_writer_not_observed_in_bounded_window",
        "runtime_blocked": "arg0_writer_trace_runtime_blocked",
    }
    if final_classification == "final_writer_trace_schema_gap" and sidecar_blocker:
        return sidecar_blocker
    if final_classification in final_blockers:
        return final_blockers[final_classification]
    if sidecar_blocker:
        return sidecar_blocker
    pointer_trace = _derive_arg0_pointer_origin_trace(payload)
    pointer_classification = str(pointer_trace.get("classification") or "").strip()
    if pointer_classification in {
        "carrier_identified",
        "carrier_identified_writer_missing",
        "source_slot_rejected",
        "source_slot_unstable",
        "schema_gap",
        "not_observed",
    }:
        return f"arg0_pointer_{pointer_classification}"
    raw_write_gap = payload.get("raw_write_gap_summary", {})
    raw_write_gap = raw_write_gap if isinstance(raw_write_gap, dict) else {}
    refined_gap = str(raw_write_gap.get("classification") or "").strip()
    if refined_gap:
        return refined_gap
    classification = str(payload.get("classification") or "").strip()
    if classification not in {"instrumentation_incomplete", "compare_lhs_runtime_backed_writer_missing"}:
        return ""
    summary = payload.get("last_writer_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    health = payload.get("write_monitor_health", {})
    if not isinstance(health, dict) or not health:
        health = summary.get("write_monitor_health", {})
    health = health if isinstance(health, dict) else {}
    try:
        runtime_backed_count = int(payload.get("runtime_backed_count", 0) or 0)
    except (TypeError, ValueError):
        runtime_backed_count = 0
    actual_compare = payload.get("actual_compare", {})
    actual_compare_ready = bool(summary.get("actual_compare_arg0_runtime_backed"))
    if not actual_compare_ready and isinstance(actual_compare, dict):
        actual_compare_ready = (
            str(actual_compare.get("entry_status") or "") == "confirmed"
            and str(actual_compare.get("lhs_side") or "") == "arg0"
        )
    if runtime_backed_count < 3 or not actual_compare_ready:
        return "runtime_compare_arg0_not_ready"
    try:
        observed_count = int(health.get("observed_candidate_count", 3) or 0)
    except (TypeError, ValueError):
        observed_count = 0
    if observed_count < 3:
        return "write_monitor_observation_incomplete"
    try:
        followed_thread_count = int(health.get("followed_thread_count", 0) or 0)
    except (TypeError, ValueError):
        followed_thread_count = 0
    if not bool(health.get("enabled")) or followed_thread_count <= 0:
        return "write_monitor_not_following_thread"
    try:
        raw_write_count = int(health.get("raw_write_count", 0) or 0)
    except (TypeError, ValueError):
        raw_write_count = 0
    if raw_write_count <= 0:
        return "no_raw_write_events_observed"
    try:
        intersecting_count = int(health.get("filtered_intersecting_write_count", 0) or 0)
        retained_count = int(summary.get("retained_write_count", 0) or 0)
    except (TypeError, ValueError):
        intersecting_count = 0
        retained_count = 0
    if intersecting_count <= 0 or retained_count <= 0:
        missing_reasons = summary.get("missing_candidate_reasons", [])
        if isinstance(missing_reasons, list) and missing_reasons:
            nearest_reasons = {
                str(nearest.get("bounded_failure_reason") or "").strip()
                for reason in missing_reasons
                if isinstance(reason, dict)
                for nearest in (
                    reason.get("nearest_non_intersecting_writes", [])
                    if isinstance(reason.get("nearest_non_intersecting_writes"), list)
                    else []
                )
                if isinstance(nearest, dict)
            }
            if nearest_reasons and nearest_reasons <= {"write_before_arg0_window", "write_after_arg0_window"}:
                return "arg0_pointer_origin_untracked"
        return "raw_writes_not_intersecting_arg0"
    writer_candidates = payload.get("last_writer_candidates", [])
    if not isinstance(writer_candidates, list) or not writer_candidates:
        return "intersecting_writer_present_but_dropped_by_aggregation"
    return ""


def _pointer_text_equal(left: Any, right: Any) -> bool:
    left_text = str(left or "").strip().lower()
    right_text = str(right or "").strip().lower()
    return bool(left_text and right_text and left_text not in {"0x0", "0"} and left_text == right_text)


def _observation_by_hook(observations: list[dict[str, Any]], hook_names: set[str]) -> dict[str, Any]:
    for observation in observations:
        if str(observation.get("hook_name", "")) in hook_names:
            return dict(observation)
    return {}


def _actual_arg0_from_result(result: dict[str, Any], fallback_value: str, fallback_preview: str) -> dict[str, Any]:
    observations = result.get("hook_observations", [])
    observations = [dict(item) for item in observations if isinstance(item, dict)] if isinstance(observations, list) else []
    for observation in observations:
        compare_args = observation.get("compare_args", {})
        args = compare_args.get("args", []) if isinstance(compare_args, dict) else []
        if not isinstance(args, list):
            continue
        for arg in args:
            if not isinstance(arg, dict):
                continue
            try:
                index = int(arg.get("index", -1))
            except (TypeError, ValueError):
                index = -1
            role = str(arg.get("role", "")).lower()
            if index == 0 or role == "arg0":
                return {
                    "value": str(arg.get("value", "") or fallback_value),
                    "preview_hex": str(arg.get("preview_hex", "") or fallback_preview),
                }
    return {"value": fallback_value, "preview_hex": fallback_preview}


def _matching_frame_slot(observation: dict[str, Any], pointer_value: str) -> dict[str, Any]:
    frame_slots = observation.get("frame_slots", [])
    frame_slots = [dict(item) for item in frame_slots if isinstance(item, dict)] if isinstance(frame_slots, list) else []
    target = str(pointer_value or "").strip().lower()
    if not target:
        return {}
    for slot in frame_slots:
        if str(slot.get("value", "")).strip().lower() == target:
            return slot
    return {}


def _derive_arg0_pointer_origin_trace(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = payload.get("arg0_pointer_origin_trace", {})
    if isinstance(explicit, dict) and explicit:
        return explicit
    actual_compare = payload.get("actual_compare", {})
    actual_compare = actual_compare if isinstance(actual_compare, dict) else {}
    values = actual_compare.get("arg0_value_by_candidate", {})
    values = values if isinstance(values, dict) else {}
    previews = actual_compare.get("arg0_preview_by_candidate", {})
    previews = previews if isinstance(previews, dict) else {}
    candidate_results = payload.get("candidate_results", [])
    candidate_results = (
        [dict(item) for item in candidate_results if isinstance(item, dict)]
        if isinstance(candidate_results, list)
        else []
    )
    last_writer_summary = payload.get("last_writer_summary", {})
    last_writer_summary = last_writer_summary if isinstance(last_writer_summary, dict) else {}
    last_writer_candidates = payload.get("last_writer_candidates", [])
    last_writer_candidates = last_writer_candidates if isinstance(last_writer_candidates, list) else []
    rows: list[dict[str, Any]] = []
    for result in candidate_results:
        candidate_hex = str(result.get("candidate_hex", "") or "")
        observations = result.get("hook_observations", [])
        observations = (
            [dict(item) for item in observations if isinstance(item, dict)]
            if isinstance(observations, list)
            else []
        )
        fallback_value = str(values.get(candidate_hex, "") or "")
        fallback_preview = str(previews.get(candidate_hex, "") or "")
        actual_arg0 = _actual_arg0_from_result(result, fallback_value, fallback_preview)
        actual_value = str(actual_arg0.get("value", "") or "")
        actual_preview = str(actual_arg0.get("preview_hex", "") or "")
        static_compare = _observation_by_hook(observations, {"static_compare_callsite"})
        pre_compare = _observation_by_hook(observations, {"pre_compare_lhs_push", "pre_compare_push_esi"})
        reload_source = _observation_by_hook(
            observations,
            {"initial_lhs_reload", "final_lhs_reload", "post_handoff_lhs_reload"},
        )
        carrier = pre_compare or static_compare
        carrier_value = str(carrier.get("esi_ptr", "") or "")
        carrier_equals_arg0 = _pointer_text_equal(carrier_value, actual_value)
        source_slot = _matching_frame_slot(reload_source or carrier, actual_value)
        reload_value = str(reload_source.get("esi_ptr") or source_slot.get("value") or "")
        reload_equals_arg0 = _pointer_text_equal(reload_value, actual_value)
        if carrier_equals_arg0:
            status = (
                "carrier_identified"
                if last_writer_candidates and bool(last_writer_summary.get("connects_to_actual_arg0"))
                else "carrier_identified_writer_missing"
            )
            gap_reason = "" if status == "carrier_identified" else "final_data_writer_not_observed_for_actual_arg0"
            carrier_relation = "pointer_carrier"
        elif actual_value and carrier_value:
            status = "source_slot_rejected"
            gap_reason = "observed_esi_does_not_equal_actual_arg0"
            carrier_relation = "rejected_pointer_carrier"
        elif actual_value:
            status = "schema_gap"
            gap_reason = "pre_compare_esi_or_callsite_esi_missing"
            carrier_relation = ""
        else:
            status = "not_observed"
            gap_reason = "actual_arg0_missing"
            carrier_relation = ""
        rows.append(
            {
                "candidate_hex": candidate_hex,
                "actual_arg0_at_compare": actual_value,
                "actual_arg0_preview_prefix": actual_preview[:24],
                "actual_compare_site": actual_compare.get("caller_module_offset", ""),
                "pre_compare_esi_value": carrier_value,
                "pre_compare_esi_hook": carrier.get("hook_name", ""),
                "pre_compare_esi_module_offset": carrier.get("module_offset", ""),
                "pre_compare_esi_equals_arg0": carrier_equals_arg0,
                "reload_site": reload_source.get("module_offset", ""),
                "reload_source_kind": "frame_slot" if source_slot else ("register_esi" if reload_value else ""),
                "reload_source_address": source_slot.get("address", ""),
                "reload_source_slot": source_slot.get("name", ""),
                "reload_source_value": reload_value,
                "reload_source_equals_arg0": reload_equals_arg0,
                "carrier_relation": carrier_relation,
                "pointer_origin_status": status,
                "pointer_origin_gap_reason": gap_reason,
            }
        )
    if not rows:
        return {}
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("pointer_origin_status", "") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
    row_count = len(rows)
    if status_counts.get("carrier_identified_writer_missing", 0) == row_count:
        classification = "carrier_identified_writer_missing"
    elif status_counts.get("carrier_identified", 0) == row_count:
        classification = "carrier_identified"
    elif any(status in status_counts for status in ("source_slot_rejected", "source_slot_unstable")):
        classification = "source_slot_rejected"
    elif status_counts.get("schema_gap", 0) == row_count:
        classification = "schema_gap"
    else:
        classification = "not_observed"
    return {
        "classification": classification,
        "candidate_count": row_count,
        "carrier_identified_count": sum(
            1
            for row in rows
            if str(row.get("pointer_origin_status")) in {"carrier_identified", "carrier_identified_writer_missing"}
        ),
        "carrier_candidate_dependent": len({str(value) for value in values.values() if str(value)}) > 1,
        "final_writer_status": (
            "identified"
            if last_writer_candidates and bool(last_writer_summary.get("connects_to_actual_arg0"))
            else "missing"
        ),
        "pointer_carrier_is_final_writer": False,
        "rows": rows,
        "recommended_next_hook_points": [
            "module+0x253a slot writer before [ebp-0x1170]",
            "module+0x2559 reload source into ESI",
            "module+0x258b push ESI before compare arg0",
        ],
    }


def _derive_arg0_final_data_writer_trace(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = payload.get("arg0_final_data_writer_trace", {})
    if isinstance(explicit, dict) and explicit:
        return explicit
    actual_compare = payload.get("actual_compare", {})
    actual_compare = actual_compare if isinstance(actual_compare, dict) else {}
    values = actual_compare.get("arg0_value_by_candidate", {})
    values = values if isinstance(values, dict) else {}
    previews = actual_compare.get("arg0_preview_by_candidate", {})
    previews = previews if isinstance(previews, dict) else {}
    candidate_results = payload.get("candidate_results", [])
    candidate_results = (
        [dict(item) for item in candidate_results if isinstance(item, dict)]
        if isinstance(candidate_results, list)
        else []
    )
    last_writer_summary = payload.get("last_writer_summary", {})
    last_writer_summary = last_writer_summary if isinstance(last_writer_summary, dict) else {}
    last_writer_candidates = payload.get("last_writer_candidates", [])
    last_writer_candidates = [dict(item) for item in last_writer_candidates if isinstance(item, dict)] if isinstance(last_writer_candidates, list) else []
    writers_by_candidate = {
        str(item.get("candidate_hex") or ""): item for item in last_writer_candidates if str(item.get("candidate_hex") or "")
    }
    missing_reasons = last_writer_summary.get("missing_candidate_reasons", [])
    missing_reasons = [dict(item) for item in missing_reasons if isinstance(item, dict)] if isinstance(missing_reasons, list) else []
    nearest_by_candidate: dict[str, dict[str, Any]] = {}
    for reason in missing_reasons:
        nearest = reason.get("nearest_non_intersecting_writes", [])
        if isinstance(nearest, list) and nearest and isinstance(nearest[0], dict):
            nearest_by_candidate[str(reason.get("candidate_hex") or "")] = dict(nearest[0])

    rows: list[dict[str, Any]] = []
    for result in candidate_results:
        candidate_hex = str(result.get("candidate_hex", "") or "")
        observations = result.get("hook_observations", [])
        observations = (
            [dict(item) for item in observations if isinstance(item, dict)]
            if isinstance(observations, list)
            else []
        )
        actual_arg0 = _actual_arg0_from_result(
            result,
            str(values.get(candidate_hex, "") or ""),
            str(previews.get(candidate_hex, "") or ""),
        )
        actual_value = str(actual_arg0.get("value", "") or "")
        actual_preview = str(actual_arg0.get("preview_hex", "") or "")
        actual_compare_row = _observation_by_hook(observations, {"static_compare_callsite"})
        pre_push = _observation_by_hook(observations, {"pre_compare_lhs_push", "pre_compare_push_esi"})
        reload_source = _observation_by_hook(
            observations,
            {"initial_lhs_reload", "final_lhs_reload", "post_handoff_lhs_reload"},
        )
        slot_writer = _observation_by_hook(observations, {"old_lhs_slot_store", "slot_writer"})
        source_slot = _matching_frame_slot(reload_source or pre_push or actual_compare_row, actual_value)
        reload_value = str(reload_source.get("esi_ptr") or source_slot.get("value") or "")
        slot_writer_value = str(slot_writer.get("eax_ptr") or "")
        if not slot_writer_value:
            slot_writer_value = str(_matching_frame_slot(slot_writer, actual_value).get("value") or "")
        pre_push_value = str(pre_push.get("esi_ptr") or "")
        writer = writers_by_candidate.get(candidate_hex, {})
        nearest = nearest_by_candidate.get(candidate_hex, {})
        if writer:
            status = "final_writer_identified"
            gap_reason = ""
        elif not actual_value or not actual_compare_row:
            status = "final_writer_trace_schema_gap"
            gap_reason = "actual_compare_arg0_missing"
        elif not pre_push or not reload_source or not slot_writer:
            status = "final_writer_trace_schema_gap"
            gap_reason = "bounded_pointer_chain_rows_missing"
        elif not (
            _pointer_text_equal(pre_push_value, actual_value)
            and _pointer_text_equal(reload_value, actual_value)
            and _pointer_text_equal(slot_writer_value, reload_value)
        ):
            status = "runtime_blocked"
            gap_reason = "pointer_chain_not_connected"
        elif nearest:
            status = "writer_not_observed_in_bounded_window"
            gap_reason = "raw_writes_observed_but_none_intersect_actual_arg0"
        else:
            status = "pointer_chain_identified_writer_missing"
            gap_reason = "final_data_writer_not_observed_for_actual_arg0"
        rows.append(
            {
                "candidate_hex": candidate_hex,
                "actual_arg0_at_compare": actual_value,
                "actual_arg0_preview_prefix": actual_preview[:24],
                "compare_site": actual_compare.get("caller_module_offset", ""),
                "actual_compare_site_observed": bool(actual_compare_row),
                "pre_push_esi_site": pre_push.get("module_offset", ""),
                "pre_push_esi_value": pre_push_value,
                "pre_push_esi_equals_arg0": _pointer_text_equal(pre_push_value, actual_value),
                "reload_site": reload_source.get("module_offset", ""),
                "reload_source_value": reload_value,
                "reload_source_equals_arg0": _pointer_text_equal(reload_value, actual_value),
                "slot_writer_site": slot_writer.get("module_offset", ""),
                "slot_writer_value": slot_writer_value,
                "slot_writer_equals_reload_source": _pointer_text_equal(slot_writer_value, reload_value),
                "nearest_write_site": writer.get("writer_module_offset") or nearest.get("module_offset", ""),
                "nearest_write_address": writer.get("write_address") or nearest.get("address", ""),
                "nearest_write_intersects_arg0": bool(writer),
                "final_writer_status": status,
                "final_writer_gap_reason": gap_reason,
            }
        )
    if not rows:
        return {}
    statuses = {str(row.get("final_writer_status") or "") for row in rows}
    if statuses == {"final_writer_identified"}:
        classification = "final_writer_identified"
    elif "runtime_blocked" in statuses:
        classification = "runtime_blocked"
    elif "final_writer_trace_schema_gap" in statuses:
        classification = "final_writer_trace_schema_gap"
    elif statuses == {"writer_not_observed_in_bounded_window"}:
        classification = "writer_not_observed_in_bounded_window"
    elif statuses <= {"pointer_chain_identified_writer_missing", "writer_not_observed_in_bounded_window"}:
        classification = "pointer_chain_identified_writer_missing"
    else:
        classification = "final_writer_trace_schema_gap"
    return {
        "classification": classification,
        "candidate_count": len(rows),
        "final_writer_status": classification,
        "pointer_carrier_is_final_writer": False,
        "pointer_write_is_final_data_writer": False,
        "candidate_dependent_pointer_chain": len({str(value) for value in values.values() if str(value)}) > 1,
        "rows": rows,
        "recommended_next_hook_points": [
            "module+0x253a slot writer before [ebp-0x1170]",
            "module+0x2559 reload source into ESI",
            "module+0x258b push ESI before compare arg0",
            "module+0x258c actual compare callsite",
        ]
        if classification != "final_writer_identified"
        else [],
    }


def _derive_raw_write_gap_summary(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = payload.get("raw_write_gap_summary", {})
    if isinstance(explicit, dict) and explicit:
        return explicit
    summary = payload.get("last_writer_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    reasons = summary.get("missing_candidate_reasons", [])
    reasons = [dict(item) for item in reasons if isinstance(item, dict)] if isinstance(reasons, list) else []
    actual_compare = payload.get("actual_compare", {})
    actual_compare = actual_compare if isinstance(actual_compare, dict) else {}
    values = actual_compare.get("arg0_value_by_candidate", {})
    previews = actual_compare.get("arg0_preview_by_candidate", {})
    values = values if isinstance(values, dict) else {}
    previews = previews if isinstance(previews, dict) else {}
    rows: list[dict[str, Any]] = []
    bounded_reasons: set[str] = set()
    for reason in reasons:
        candidate_hex = str(reason.get("candidate_hex") or "")
        nearest = reason.get("nearest_non_intersecting_writes", [])
        nearest = [dict(item) for item in nearest if isinstance(item, dict)] if isinstance(nearest, list) else []
        nearest_first = nearest[0] if nearest else {}
        bounded_reason = str(nearest_first.get("bounded_failure_reason") or "")
        if bounded_reason:
            bounded_reasons.add(bounded_reason)
        preview = str(previews.get(candidate_hex) or "")
        rows.append(
            {
                "candidate_hex": candidate_hex,
                "actual_arg0": str(values.get(candidate_hex) or ""),
                "actual_arg0_preview_prefix": preview[:24],
                "nearest_write_address": nearest_first.get("address", ""),
                "nearest_write_module_offset": nearest_first.get("module_offset", ""),
                "nearest_write_instruction": nearest_first.get("instruction", ""),
                "nearest_write_sequence": nearest_first.get("sequence"),
                "nearest_write_thread_id": nearest_first.get("thread_id", ""),
                "nearest_write_size": nearest_first.get("size", 0),
                "distance_to_arg0": nearest_first.get("distance_to_arg0"),
                "bounded_failure_reason": bounded_reason,
                "raw_write_event_count": reason.get("raw_write_event_count", 0),
            }
        )
    if not rows:
        return {}
    try:
        raw_count = int(summary.get("raw_write_event_count", 0) or 0)
        retained_count = int(summary.get("retained_write_count", 0) or 0)
    except (TypeError, ValueError):
        raw_count = 0
        retained_count = 0
    classification = ""
    if raw_count > 0 and retained_count == 0:
        classification = (
            "arg0_pointer_origin_untracked"
            if bounded_reasons and bounded_reasons <= {"write_before_arg0_window", "write_after_arg0_window"}
            else "writer_event_schema_gap"
        )
    return {
        "classification": classification,
        "arg0_pointer_origin_status": "untracked" if classification == "arg0_pointer_origin_untracked" else "unknown",
        "arg0_pointer_origin_gap_reason": "raw_writes_observed_but_none_intersect_actual_arg0"
        if classification == "arg0_pointer_origin_untracked"
        else "nearest_write_fields_incomplete",
        "write_monitor_target_source": "static_compare_callsite_arg0",
        "raw_write_window_summary": rows,
        "recommended_next_hook_points": [
            "bounded pointer-origin trace before module+0x258c actual arg0",
            "module+0x2559..0x258b ESI source window before compare push",
        ]
        if classification == "arg0_pointer_origin_untracked"
        else [],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _without_digest_volatile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_digest_volatile_fields(item)
            for key, item in value.items()
            if key not in STATE_DIGEST_EXCLUDED_KEYS
        }
    if isinstance(value, list):
        return [_without_digest_volatile_fields(item) for item in value]
    return value


def _state_digest(current_state: dict[str, Any]) -> str:
    stable_state = _without_digest_volatile_fields(current_state)
    return _sha256_bytes(_canonical_json_bytes(stable_state))


def _git_commit() -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short=12", "HEAD"],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _source_harness_run_name(artifact_index: dict[str, Any]) -> str:
    latest_harness_run = str(artifact_index.get("latest_harness_run") or "")
    return Path(latest_harness_run.replace("\\", "/")).name if latest_harness_run else ""


def _identity_timestamp() -> tuple[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.strftime("%Y%m%d_%H%M%S"), now.isoformat().replace("+00:00", "Z")


def _is_missing_or_default(path: Path, default_content: str, *legacy_defaults: str) -> bool:
    if not path.exists():
        return True
    try:
        current = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    default_texts = (default_content, *legacy_defaults)
    return not current or any(current == item.strip() for item in default_texts)


def extract_markdown_json_block(text: str, block_name: str) -> dict[str, Any]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("```"):
            continue
        info = stripped[3:].strip().split()
        if "json" not in info or block_name not in info:
            continue
        block_lines: list[str] = []
        for block_line in lines[index + 1 :]:
            if block_line.strip().startswith("```"):
                break
            block_lines.append(block_line)
        else:
            return {"found": True, "parse_error": "unterminated fenced JSON block"}
        raw = "\n".join(block_lines).strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"found": True, "parse_error": f"invalid JSON: {exc.msg}"}
        if not isinstance(parsed, dict):
            return {"found": True, "parse_error": "JSON block must contain an object"}
        return {"found": True, "parse_error": None, **parsed}
    return {"found": False, "parse_error": None}


def _read_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _normalize_status(value: Any, allowed: set[str], *, default: str = "UNKNOWN") -> tuple[str, str | None]:
    status = str(value or default).upper()
    if status in allowed:
        return status, None
    return default, f"invalid status: {value}"


def _template_status(text: str, template: str) -> bool:
    return bool(text.strip()) and text.strip() == template.strip()


def _list_of_strings(value: Any) -> list[str] | None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    return None


def read_decision_meta(state_dir: Path) -> dict[str, Any]:
    path = state_dir / "decision_packet.md"
    text = _read_text_or_empty(path)
    if _template_status(text, DECISION_PACKET_TEMPLATE):
        status = "TEMPLATE_ONLY"
        meta = {"found": False, "parse_error": None}
    else:
        meta = extract_markdown_json_block(text, DECISION_META_BLOCK_NAME)
        status, status_error = _normalize_status(meta.get("status"), DECISION_STATUSES)
        if status_error:
            meta["parse_error"] = status_error
    if not meta.get("found") and status != "TEMPLATE_ONLY":
        status = "UNKNOWN"
    return {
        "status": status,
        "decision_id": meta.get("decision_id") or "",
        "based_on_state_build_id": meta.get("based_on_state_build_id") or "",
        "based_on_state_digest": meta.get("based_on_state_digest") or "",
        "round_id": meta.get("round_id") or "",
        "mainline": meta.get("mainline") or "",
        "skill_profiles": meta.get("skill_profiles"),
        "parse_error": meta.get("parse_error"),
    }


def read_codex_report_summary(state_dir: Path) -> dict[str, Any]:
    path = state_dir / "codex_execution_report.md"
    text = _read_text_or_empty(path)
    if _template_status(text, CODEX_EXECUTION_REPORT_TEMPLATE):
        status = "TEMPLATE_ONLY"
        acceptance_recommendation = "UNKNOWN"
        meta = {"found": False, "parse_error": None}
    else:
        meta = extract_markdown_json_block(text, CODEX_REPORT_SUMMARY_BLOCK_NAME)
        status, status_error = _normalize_status(meta.get("status"), CODEX_REPORT_STATUSES)
        acceptance_recommendation, recommendation_error = _normalize_status(
            meta.get("acceptance_recommendation"),
            CODEX_REPORT_ACCEPTANCE_RECOMMENDATIONS,
        )
        parse_errors = [item for item in (meta.get("parse_error"), status_error, recommendation_error) if item]
        meta["parse_error"] = "; ".join(parse_errors) if parse_errors else None
    if not meta.get("found") and status != "TEMPLATE_ONLY":
        status = "UNKNOWN"
        acceptance_recommendation = "UNKNOWN"
    return {
        "status": status,
        "acceptance_recommendation": acceptance_recommendation,
        "report_id": meta.get("report_id") or "",
        "based_on_decision_id": meta.get("based_on_decision_id") or "",
        "round_id": meta.get("round_id") or "",
        "files_changed": meta.get("files_changed"),
        "tests_ran": meta.get("tests_ran"),
        "generated_artifacts": meta.get("generated_artifacts"),
        "verified_artifacts": meta.get("verified_artifacts"),
        "next_suggested_task": meta.get("next_suggested_task") or "",
        "parse_error": meta.get("parse_error"),
    }


def parse_pytest_result_header(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {
            "found": False,
            "parse_error": None,
            "schema_version": None,
            "decision_id": "",
            "report_id": "",
            "round_id": "",
            "generated_at": "",
            "status": "LEGACY_WITHOUT_HEADER",
            "tests_ran": [],
        }
    lines = text.splitlines()
    first_line = next((line for line in lines if line.strip()), "")
    if not (
        first_line.strip().startswith("```")
        and "json" in first_line
        and PYTEST_RESULT_SUMMARY_BLOCK_NAME in first_line
    ):
        return {
            "found": False,
            "parse_error": None,
            "schema_version": None,
            "decision_id": "",
            "report_id": "",
            "round_id": "",
            "generated_at": "",
            "status": "LEGACY_WITHOUT_HEADER",
            "tests_ran": [],
        }
    meta = extract_markdown_json_block(text, PYTEST_RESULT_SUMMARY_BLOCK_NAME)
    status, status_error = _normalize_status(meta.get("status"), PYTEST_RESULT_STATUSES)
    parse_errors = [item for item in (meta.get("parse_error"), status_error) if item]
    tests_ran = meta.get("tests_ran")
    if tests_ran is None:
        tests_ran_list: list[str] = []
    elif isinstance(tests_ran, list) and all(isinstance(item, str) for item in tests_ran):
        tests_ran_list = list(tests_ran)
    else:
        tests_ran_list = []
        parse_errors.append("tests_ran must be a list of strings")
    parse_error = "; ".join(parse_errors) if parse_errors else None
    return {
        "found": bool(meta.get("found")),
        "parse_error": parse_error,
        "schema_version": meta.get("schema_version"),
        "decision_id": meta.get("decision_id") or "",
        "report_id": meta.get("report_id") or "",
        "round_id": meta.get("round_id") or "",
        "generated_at": meta.get("generated_at") or "",
        "status": status,
        "tests_ran": tests_ran_list,
    }


def _parse_pytest_body_for_failures(body: str) -> dict[str, Any]:
    """Scan pytest output body for failure indicators.

    Returns:
        dict with keys:
        - failed_count: int (0 if no failures detected)
        - has_failure_text: bool
        - failure_lines: list[str] (first few lines containing failure markers)
    """
    failure_patterns = [
        re.compile(r"([1-9]\d*)\s+failed"),
        re.compile(r"FAILED\s+"),
        re.compile(r"ERROR\s+"),
        re.compile(r"=+\s+FAILURES\s+="),
        re.compile(r"=+\s+ERRORS\s+="),
    ]
    failed_count = 0
    has_failure_text = False
    failure_lines: list[str] = []
    for line in body.splitlines():
        for pat in failure_patterns:
            m = pat.search(line)
            if m:
                has_failure_text = True
                if "failed" in pat.pattern:
                    try:
                        failed_count = max(failed_count, int(m.group(1)))
                    except ValueError:
                        pass
                if len(failure_lines) < 5:
                    failure_lines.append(line.strip())
                break
    return {
        "failed_count": failed_count,
        "has_failure_text": has_failure_text,
        "failure_lines": failure_lines,
    }


def validate_pytest_result_for_report(
    pytest_text: str,
    report_summary: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_pytest_result_header(pytest_text)
    errors: list[str] = []
    warnings: list[str] = []
    matches_report: str | bool = "unknown"
    tests_ran_covers_report: str | bool = "unknown"
    missing_report_tests: list[str] = []
    if parsed.get("status") == "LEGACY_WITHOUT_HEADER":
        warnings.append("pytest_result_summary missing")
    if parsed.get("parse_error"):
        errors.append(f"pytest_result_summary invalid: {parsed['parse_error']}")
    report_decision_id = str(report_summary.get("based_on_decision_id") or "")
    report_id = str(report_summary.get("report_id") or "")
    report_round_id = str(report_summary.get("round_id") or "")
    report_tests_ran = report_summary.get("tests_ran")
    pytest_result_tests_ran = parsed.get("tests_ran", [])
    decision_id = str(parsed.get("decision_id") or "")
    parsed_report_id = str(parsed.get("report_id") or "")
    parsed_round_id = str(parsed.get("round_id") or "")
    if report_decision_id and decision_id:
        if decision_id == report_decision_id:
            matches_report = True
        else:
            matches_report = False
            errors.append("pytest_result decision_id does not match codex_report_summary.based_on_decision_id")
    elif report_decision_id and not decision_id:
        warnings.append("pytest_result decision_id missing")
    if report_id and parsed_report_id and parsed_report_id != report_id:
        warnings.append("pytest_result report_id does not match codex_report_summary.report_id")
    if report_round_id and parsed_round_id and parsed_round_id != report_round_id:
        warnings.append("pytest_result round_id does not match codex_report_summary.round_id")
    if isinstance(report_tests_ran, list) and all(isinstance(item, str) for item in report_tests_ran):
        if parsed.get("status") != "LEGACY_WITHOUT_HEADER" and report_tests_ran:
            pytest_test_set = set(pytest_result_tests_ran) if isinstance(pytest_result_tests_ran, list) else set()
            missing_report_tests = [item for item in report_tests_ran if item not in pytest_test_set]
            tests_ran_covers_report = not missing_report_tests
            if missing_report_tests:
                warnings.append("pytest_result tests_ran does not cover codex_report_summary.tests_ran")
    elif report_tests_ran is not None:
        warnings.append("codex_report_summary.tests_ran must be a list of strings for coverage check")

    # Header/body consistency check
    body = pytest_text
    header_end = pytest_text.find("```", pytest_text.find("```json") + 1)
    if header_end != -1:
        body = pytest_text[header_end + 3:]
    body_parse = _parse_pytest_body_for_failures(body)
    header_status = str(parsed.get("status") or "UNKNOWN")
    if header_status == "PASSED" and body_parse["has_failure_text"]:
        errors.append(
            f"pytest_result header status is PASSED but body indicates failures "
            f"({body_parse['failed_count']} failed). Contradiction detected."
        )
    elif header_status == "FAILED" and not body_parse["has_failure_text"]:
        warnings.append(
            "pytest_result header status is FAILED but body contains no failure markers"
        )

    return {
        "found": parsed.get("found"),
        "parse_error": parsed.get("parse_error"),
        "status": parsed.get("status"),
        "decision_id": decision_id,
        "report_id": parsed_report_id,
        "round_id": parsed_round_id,
        "generated_at": parsed.get("generated_at"),
        "tests_ran": pytest_result_tests_ran,
        "matches_report": matches_report,
        "report_tests_ran_count": len(report_tests_ran) if isinstance(report_tests_ran, list) else 0,
        "pytest_result_tests_ran_count": len(pytest_result_tests_ran) if isinstance(pytest_result_tests_ran, list) else 0,
        "tests_ran_covers_report": tests_ran_covers_report,
        "missing_report_tests": missing_report_tests,
        "errors": errors,
        "warnings": warnings,
        "body_failed_count": body_parse["failed_count"],
        "body_has_failure_text": body_parse["has_failure_text"],
        "body_failure_lines": body_parse["failure_lines"],
    }


def write_pytest_result(
    *,
    state_dir: Path,
    summary: dict[str, Any],
    body: str,
) -> Path:
    status, status_error = _normalize_status(summary.get("status"), PYTEST_RESULT_STATUSES, default="UNKNOWN")
    if status_error:
        raise ValueError(status_error)
    tests_ran = summary.get("tests_ran", [])
    if not isinstance(tests_ran, list) or not all(isinstance(item, str) for item in tests_ran):
        raise ValueError("tests_ran must be a list of strings")
    payload = {
        "schema_version": int(summary.get("schema_version") or 1),
        "decision_id": str(summary.get("decision_id") or ""),
        "report_id": str(summary.get("report_id") or ""),
        "round_id": str(summary.get("round_id") or ""),
        "generated_at": str(summary.get("generated_at") or _now_iso()),
        "status": status,
        "tests_ran": list(tests_ran),
    }
    header = f"```json {PYTEST_RESULT_SUMMARY_BLOCK_NAME}\n"
    header += json.dumps(payload, ensure_ascii=True, indent=2)
    header += "\n```\n"
    content = header
    if body.strip():
        content += f"\n{body.rstrip()}\n"
    path = state_dir / "pytest_result.txt"
    path.write_text(content, encoding="utf-8")
    return path


CONSUMED_REPORT_STATUSES = {"SUCCESS", "PARTIAL", "FAILED", "BLOCKED"}


def _build_handoff_consistency(
    decision: dict[str, Any],
    codex_report: dict[str, Any],
    current_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_id = str(decision.get("decision_id") or "")
    report_based_on_decision_id = str(codex_report.get("based_on_decision_id") or "")
    decision_status = str(decision.get("status") or "UNKNOWN")
    report_status = str(codex_report.get("status") or "UNKNOWN")
    decision_based_on_state_digest = str(decision.get("based_on_state_digest") or "")
    current_state_digest = str((current_state or {}).get("state_digest") or "")
    decision_state_digest_match = (
        bool(decision_based_on_state_digest)
        and bool(current_state_digest)
        and decision_based_on_state_digest == current_state_digest
    )
    decision_report_id_match = (
        bool(decision_id)
        and bool(report_based_on_decision_id)
        and decision_id == report_based_on_decision_id
        and decision_status not in {"TEMPLATE_ONLY", "UNKNOWN"}
        and report_status not in {"TEMPLATE_ONLY", "UNKNOWN"}
    )
    decision_consumed_by_report = decision_report_id_match and report_status in CONSUMED_REPORT_STATUSES
    if decision_status in {"TEMPLATE_ONLY", "UNKNOWN"} or not decision_id:
        decision_execution_state = "TEMPLATE_OR_UNKNOWN"
    elif decision_status == "APPROVED" and decision_report_id_match and report_status == "SUCCESS":
        decision_execution_state = "CONSUMED_BY_SUCCESS_REPORT"
    elif (
        decision_status == "APPROVED"
        and decision_report_id_match
        and report_status in {"PARTIAL", "FAILED", "BLOCKED"}
    ):
        decision_execution_state = "CONSUMED_BY_NON_SUCCESS_REPORT"
    elif decision_status == "APPROVED" and decision_state_digest_match and not decision_report_id_match:
        decision_execution_state = "READY_FOR_EXECUTION"
    elif decision_status == "APPROVED" and not decision_state_digest_match and not decision_report_id_match:
        decision_execution_state = "STALE_WITHOUT_MATCHING_REPORT"
    else:
        decision_execution_state = "TEMPLATE_OR_UNKNOWN"
    decision_ready_for_execution = decision_execution_state == "READY_FOR_EXECUTION"
    return {
        "decision_report_id_match": decision_report_id_match,
        "decision_state_digest_match": decision_state_digest_match,
        "decision_consumed_by_report": decision_consumed_by_report,
        "decision_execution_state": decision_execution_state,
        "decision_ready_for_execution": decision_ready_for_execution,
        "decision_id": decision_id,
        "report_based_on_decision_id": report_based_on_decision_id,
        "decision_status": decision_status,
        "report_status": report_status,
        "current_state_digest": current_state_digest,
    }


def build_handoff_status(state_dir: Path) -> dict[str, Any]:
    decision = read_decision_meta(state_dir)
    codex_report = read_codex_report_summary(state_dir)
    current_state = _read_json(state_dir / "current_state.json")
    return {
        "decision": decision,
        "codex_report": codex_report,
        "handoff_consistency": _build_handoff_consistency(decision, codex_report, current_state),
    }


def _repo_root_for_state_dir(state_dir: Path) -> Path:
    return state_dir.resolve().parent if state_dir.name == "project_state" else Path.cwd().resolve()


def _load_skill_registry(repo_root: Path) -> tuple[dict[str, Any], str | None]:
    registry_path = repo_root / ".codex-skills" / "registry.json"
    try:
        raw = registry_path.read_text(encoding="utf-8")
    except OSError:
        return {}, f"skill registry not found: {registry_path}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"skill registry is invalid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return {}, "skill registry must contain a JSON object"
    skills = data.get("skills")
    if not isinstance(skills, dict):
        return {}, "skill registry skills must be an object"
    return skills, None


def _parse_skill_profile(profile: str) -> tuple[str, int, bool, str | None]:
    match = SKILL_PROFILE_RE.fullmatch(profile)
    if not match:
        return "", 0, False, f"invalid skill profile {profile!r}; expected skill-name@vN"
    return match.group("name"), int(match.group("version")), bool(match.group("draft")), None


def _lint_skill_profiles(
    *,
    state_dir: Path,
    decision_status: str,
    mainline: str,
    skill_profiles_value: Any,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    parsed_profiles: list[dict[str, Any]] = []

    if skill_profiles_value is None:
        warnings.append("decision_meta.skill_profiles missing; legacy decision compatibility mode")
        return {"errors": errors, "warnings": warnings, "skill_profiles": [], "parsed_skill_profiles": parsed_profiles}
    skill_profiles = _list_of_strings(skill_profiles_value)
    if skill_profiles is None:
        errors.append("decision_meta.skill_profiles must be a list of strings")
        return {"errors": errors, "warnings": warnings, "skill_profiles": [], "parsed_skill_profiles": parsed_profiles}
    if not skill_profiles:
        warnings.append("decision_meta.skill_profiles is empty; no workflow skill profile declared")
        return {"errors": errors, "warnings": warnings, "skill_profiles": [], "parsed_skill_profiles": parsed_profiles}

    registry, registry_error = _load_skill_registry(_repo_root_for_state_dir(state_dir))
    if registry_error:
        errors.append(registry_error)
        return {
            "errors": errors,
            "warnings": warnings,
            "skill_profiles": skill_profiles,
            "parsed_skill_profiles": parsed_profiles,
        }

    active_generic_count = 0
    valid_profile_count = 0
    for profile in skill_profiles:
        skill_name, version, is_draft, parse_error = _parse_skill_profile(profile)
        if parse_error:
            errors.append(parse_error)
            continue
        if is_draft and decision_status == "APPROVED":
            warnings.append(f"draft skill profile {profile!r} should not be used in APPROVED decisions")
        entry = registry.get(skill_name)
        if not isinstance(entry, dict):
            errors.append(f"skill profile {profile!r} references unknown skill {skill_name!r}")
            continue
        status = str(entry.get("status") or "")
        scope = str(entry.get("scope") or "")
        registry_version = entry.get("version")
        parsed_profiles.append(
            {
                "profile": profile,
                "skill_name": skill_name,
                "version": version,
                "draft": is_draft,
                "registry_status": status,
                "registry_scope": scope,
                "registry_version": registry_version,
            }
        )
        if status != "active":
            errors.append(f"skill profile {profile!r} references non-active skill {skill_name!r} status={status!r}")
            continue
        if registry_version != version:
            errors.append(
                f"skill profile {profile!r} version mismatch: registry version is {registry_version!r}"
            )
            continue
        valid_profile_count += 1
        if scope == "generic_workflow":
            active_generic_count += 1

    if skill_profiles and valid_profile_count == 0:
        errors.append("decision_meta.skill_profiles contains no valid active skill profiles")
    if decision_status == "APPROVED" and mainline in {"engineering_branch", "reverse_solving"} and active_generic_count == 0:
        warnings.append(f"decision_meta.skill_profiles for mainline={mainline} should include an active generic_workflow skill")

    return {
        "errors": errors,
        "warnings": warnings,
        "skill_profiles": skill_profiles,
        "parsed_skill_profiles": parsed_profiles,
    }


def lint_decision(state_dir: Path) -> dict[str, Any]:
    decision = read_decision_meta(state_dir)
    current_state_path = state_dir / "current_state.json"
    task_packet_path = state_dir / "task_packet.json"
    current_state = _read_json(current_state_path)
    task_packet = _read_json(task_packet_path)
    errors: list[str] = []
    warnings: list[str] = []

    decision_status = str(decision.get("status") or "UNKNOWN")
    decision_id = str(decision.get("decision_id") or "")
    based_on_state_build_id = str(decision.get("based_on_state_build_id") or "")
    based_on_state_digest = str(decision.get("based_on_state_digest") or "")
    mainline = str(decision.get("mainline") or "")
    current_state_build_id = str(current_state.get("state_build_id") or "")
    current_state_digest = str(current_state.get("state_digest") or "")
    execution_scope = str(task_packet.get("execution_scope") or "")
    active_decision_packet = str(task_packet.get("active_decision_packet") or "")

    if decision_status == "TEMPLATE_ONLY":
        errors.append("decision status is TEMPLATE_ONLY, expected APPROVED")
    elif decision_status != "APPROVED":
        parse_error = decision.get("parse_error")
        if parse_error:
            errors.append(f"decision_meta invalid: {parse_error}")
        elif not decision_id and not based_on_state_build_id and not based_on_state_digest:
            errors.append("decision_meta missing")
        else:
            errors.append(f"decision status is {decision_status}, expected APPROVED")
    if not decision_id:
        errors.append("decision_id missing")
    if not based_on_state_build_id:
        errors.append("based_on_state_build_id missing")
    if not based_on_state_digest:
        errors.append("based_on_state_digest missing")
    if not current_state_path.exists():
        errors.append("current_state.json missing")
    elif not current_state_digest:
        errors.append("current_state.state_digest missing")
    if based_on_state_digest and current_state_digest and based_on_state_digest != current_state_digest:
        errors.append("based_on_state_digest does not match current_state.state_digest")

    skill_profile_lint = _lint_skill_profiles(
        state_dir=state_dir,
        decision_status=decision_status,
        mainline=mainline,
        skill_profiles_value=decision.get("skill_profiles"),
    )
    errors.extend(skill_profile_lint["errors"])
    warnings.extend(skill_profile_lint["warnings"])

    if not task_packet_path.exists():
        warnings.append("task_packet.json missing")
    else:
        if not execution_scope:
            warnings.append("task_packet.execution_scope missing")
        if not active_decision_packet:
            warnings.append("task_packet.active_decision_packet missing")
        elif active_decision_packet != ACTIVE_DECISION_PACKET:
            warnings.append(
                f"task_packet.active_decision_packet is {active_decision_packet}, expected {ACTIVE_DECISION_PACKET}"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "decision_id": decision_id,
        "decision_status": decision_status,
        "decision_parse_error": decision.get("parse_error"),
        "mainline": mainline,
        "skill_profiles": skill_profile_lint["skill_profiles"],
        "parsed_skill_profiles": skill_profile_lint["parsed_skill_profiles"],
        "based_on_state_build_id": based_on_state_build_id,
        "based_on_state_digest": based_on_state_digest,
        "current_state_build_id": current_state_build_id,
        "current_state_digest": current_state_digest,
        "execution_scope": execution_scope,
        "active_decision_packet": active_decision_packet,
    }


def _list_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _pytest_result_present(state_dir: Path) -> bool:
    path = state_dir / "pytest_result.txt"
    try:
        return bool(path.read_text(encoding="utf-8").strip())
    except OSError:
        return False


def classify_round_archive(*, manifest: dict[str, Any], manifest_present: bool) -> dict[str, Any]:
    files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
    manifest_files = sorted(str(name) for name in files)
    if manifest_present:
        manifest_files = sorted({*manifest_files, ARCHIVE_MANIFEST_NAME})
    forbidden_files = sorted(name for name in manifest_files if name in ARCHIVE_FORBIDDEN_NAMES)
    required_missing = (
        sorted(name for name in ARCHIVE_REQUIRED_NAMES if name not in manifest_files)
        if manifest_present
        else []
    )
    unexpected_files = sorted(
        name
        for name in manifest_files
        if name not in ARCHIVE_MINIMAL_ALLOWED_NAMES and name not in ARCHIVE_FORBIDDEN_NAMES
    )

    if not manifest_present:
        archive_status = "not_archived"
        warning = "report round not archived yet"
    elif "git_diff.patch" in forbidden_files:
        archive_status = "polluted"
        warning = "round_manifest includes forbidden files: " + ", ".join(forbidden_files)
    elif forbidden_files or unexpected_files or required_missing:
        archive_status = "non_minimal"
        parts: list[str] = []
        if forbidden_files:
            parts.append("forbidden files: " + ", ".join(forbidden_files))
        if unexpected_files:
            parts.append("unexpected files: " + ", ".join(unexpected_files))
        if required_missing:
            parts.append("missing required files: " + ", ".join(required_missing))
        warning = "round_manifest is non-minimal: " + "; ".join(parts)
    else:
        archive_status = "archived"
        warning = ""

    return {
        "archive_status": archive_status,
        "round_manifest_present": manifest_present,
        "round_manifest_files": manifest_files,
        "round_manifest_forbidden_files": forbidden_files,
        "round_manifest_required_files_missing": required_missing,
        "round_manifest_warning": warning,
    }


def build_round_consistency(
    *,
    decision: dict[str, Any],
    report: dict[str, Any],
    current_state: dict[str, Any],
    task_packet: dict[str, Any],
    state_dir: Path,
) -> dict[str, Any]:
    report_round_id = str(report.get("round_id") or "")
    decision_round_id = str(decision.get("round_id") or "")
    current_state_round_id = str(current_state.get("round_id") or "")
    current_state_scope = str(
        current_state.get("state_scope") or task_packet.get("state_scope") or ""
    )
    task_source = str(task_packet.get("task_source") or "")
    execution_scope = str(task_packet.get("execution_scope") or "")

    if report_round_id and decision_round_id:
        report_decision_round_id_match: bool | str = report_round_id == decision_round_id
    else:
        report_decision_round_id_match = "unknown"

    if not report_round_id or not current_state_round_id:
        report_current_state_round_relation = "unknown"
    elif report_round_id == current_state_round_id:
        report_current_state_round_relation = "same"
    elif (
        current_state_scope == STATE_SCOPE_SAMPLE
        or task_source == TASK_SOURCE_DERIVED_FROM_SAMPLE_ARTIFACTS
        or execution_scope == EXECUTION_SCOPE_DECISION_PACKET_CONTROLS_CURRENT_ROUND
    ):
        report_current_state_round_relation = "different_but_allowed_sample_state"
    else:
        report_current_state_round_relation = "different_unclassified"

    if not report_round_id:
        manifest_path = None
        archive = {
            "archive_status": "unknown",
            "round_manifest_present": False,
            "round_manifest_files": [],
            "round_manifest_forbidden_files": [],
            "round_manifest_required_files_missing": [],
            "round_manifest_warning": "",
        }
    else:
        manifest_path = state_dir / "rounds" / report_round_id / ARCHIVE_MANIFEST_NAME
        manifest_present = manifest_path.exists()
        manifest = _read_json(manifest_path) if manifest_present else {}
        archive = classify_round_archive(manifest=manifest, manifest_present=manifest_present)

    return {
        "report_round_id": report_round_id,
        "decision_round_id": decision_round_id,
        "current_state_round_id": current_state_round_id,
        "current_state_scope": current_state_scope or "unknown",
        "report_decision_round_id_match": report_decision_round_id_match,
        "report_current_state_round_relation": report_current_state_round_relation,
        "round_manifest_path": _path_for_json(manifest_path) if manifest_path is not None else "",
        **archive,
    }


def lint_report(state_dir: Path) -> dict[str, Any]:
    handoff_status = build_handoff_status(state_dir)
    decision = handoff_status["decision"]
    report = handoff_status["codex_report"]
    consistency = handoff_status["handoff_consistency"]
    current_state = _read_json(state_dir / "current_state.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    round_consistency = build_round_consistency(
        decision=decision,
        report=report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    errors: list[str] = []
    warnings: list[str] = []

    report_status = str(report.get("status") or "UNKNOWN")
    acceptance_recommendation = str(report.get("acceptance_recommendation") or "UNKNOWN")
    report_id = str(report.get("report_id") or "")
    based_on_decision_id = str(report.get("based_on_decision_id") or "")
    decision_id = str(decision.get("decision_id") or "")
    round_id = str(report.get("round_id") or "")
    current_state_round_id = str(current_state.get("round_id") or "")
    decision_round_id = str(decision.get("round_id") or "")
    pytest_text = _read_text_or_empty(state_dir / "pytest_result.txt")
    pytest_result_present = bool(pytest_text.strip())
    pytest_validation = validate_pytest_result_for_report(pytest_text, report)

    if report_status in {"TEMPLATE_ONLY", "UNKNOWN"}:
        parse_error = report.get("parse_error")
        if parse_error:
            errors.append(f"codex_report_summary invalid: {parse_error}")
        elif report_status == "TEMPLATE_ONLY":
            errors.append("codex_report_summary is TEMPLATE_ONLY")
        else:
            errors.append("codex_report_summary missing")
    if not report_id:
        errors.append("report_id missing")
    if not round_id:
        errors.append("round_id missing")
    if not based_on_decision_id:
        errors.append("based_on_decision_id missing")
    if not decision_id:
        errors.append("current decision_id missing")
    if based_on_decision_id and decision_id and based_on_decision_id != decision_id:
        errors.append("based_on_decision_id does not match current decision_id")
    if round_id and decision_round_id and round_id != decision_round_id:
        errors.append("report round_id does not match current decision round_id")

    artifact_list_fields = ("generated_artifacts", "verified_artifacts")
    if report_status in {"SUCCESS", "PARTIAL", "BLOCKED", "FAILED"}:
        if all(report.get(field) is None for field in artifact_list_fields):
            errors.append("generated_artifacts or verified_artifacts missing")

    for field in ("files_changed", "tests_ran", *artifact_list_fields):
        value = report.get(field)
        if value is not None and not isinstance(value, list):
            errors.append(f"{field} must be a list")

    tests_ran = report.get("tests_ran")
    if report_status == "SUCCESS" and not (isinstance(tests_ran, list) and tests_ran):
        errors.append("SUCCESS report requires non-empty tests_ran")
    if report_status == "SUCCESS" and not pytest_result_present:
        errors.append("SUCCESS report requires non-empty pytest_result.txt")
    errors.extend(pytest_validation.get("errors") or [])
    warnings.extend(pytest_validation.get("warnings") or [])

    if round_consistency["report_current_state_round_relation"] == "different_unclassified":
        warnings.append("report round_id differs from current_state.round_id and relation is unclassified")
    if acceptance_recommendation == "UNKNOWN":
        warnings.append("acceptance_recommendation is UNKNOWN")
    if report_status in {"PARTIAL", "FAILED", "BLOCKED"}:
        warnings.append(f"report_status is {report_status}")

    if round_consistency.get("round_manifest_warning"):
        warnings.append(str(round_consistency["round_manifest_warning"]))

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "report_id": report_id,
        "report_status": report_status,
        "acceptance_recommendation": acceptance_recommendation,
        "based_on_decision_id": based_on_decision_id,
        "decision_id": decision_id,
        "decision_report_id_match": consistency.get("decision_report_id_match"),
        "round_id": round_id,
        "current_state_round_id": current_state_round_id,
        **round_consistency,
        "tests_ran_count": _list_count(report.get("tests_ran")),
        "generated_artifacts_count": _list_count(report.get("generated_artifacts")),
        "verified_artifacts_count": _list_count(report.get("verified_artifacts")),
        "pytest_result_present": pytest_result_present,
        "pytest_result_status": pytest_validation.get("status"),
        "pytest_result_decision_id": pytest_validation.get("decision_id"),
        "pytest_result_report_id": pytest_validation.get("report_id"),
        "pytest_result_round_id": pytest_validation.get("round_id"),
        "pytest_result_matches_report": pytest_validation.get("matches_report"),
        "report_tests_ran_count": pytest_validation.get("report_tests_ran_count"),
        "pytest_result_tests_ran_count": pytest_validation.get("pytest_result_tests_ran_count"),
        "pytest_result_tests_cover_report": pytest_validation.get("tests_ran_covers_report"),
        "pytest_result_missing_report_tests": pytest_validation.get("missing_report_tests"),
        "pytest_result_parse_error": pytest_validation.get("parse_error"),
    }


def lint_handoff(state_dir: Path) -> dict[str, Any]:
    handoff_status = build_handoff_status(state_dir)
    consistency = handoff_status["handoff_consistency"]
    decision_state = str(consistency.get("decision_execution_state") or "TEMPLATE_OR_UNKNOWN")
    lint_decision_result = lint_decision(state_dir)
    lint_report_result = lint_report(state_dir)
    errors: list[str] = []
    warnings: list[str] = []

    if decision_state == "READY_FOR_EXECUTION":
        handoff_state = "READY_FOR_CODEX" if lint_decision_result.get("ok") else "FAILED"
        errors.extend(lint_decision_result.get("errors") or [])
        warnings.extend(lint_decision_result.get("warnings") or [])
        report_errors = lint_report_result.get("errors") or []
        if report_errors:
            warnings.extend(f"previous report ignored for READY_FOR_CODEX: {error}" for error in report_errors)
        warnings.extend(lint_report_result.get("warnings") or [])
    elif decision_state == "CONSUMED_BY_SUCCESS_REPORT":
        handoff_state = "REVIEW_COMPLETE" if lint_report_result.get("ok") else "FAILED"
        errors.extend(lint_report_result.get("errors") or [])
        warnings.extend(lint_decision_result.get("warnings") or [])
        warnings.extend(lint_report_result.get("warnings") or [])
    elif decision_state == "CONSUMED_BY_NON_SUCCESS_REPORT":
        handoff_state = "REPORT_NEEDS_REVIEW" if lint_report_result.get("ok") else "FAILED"
        errors.extend(lint_report_result.get("errors") or [])
        warnings.extend(lint_decision_result.get("warnings") or [])
        warnings.extend(lint_report_result.get("warnings") or [])
        if not errors:
            warnings.append("matching report is non-success and needs review")
    elif decision_state == "STALE_WITHOUT_MATCHING_REPORT":
        handoff_state = "STALE_OR_MISMATCH"
        errors.append("decision is stale and has no matching report")
        warnings.extend(lint_decision_result.get("warnings") or [])
        warnings.extend(lint_report_result.get("warnings") or [])
    elif decision_state == "TEMPLATE_OR_UNKNOWN":
        handoff_state = "TEMPLATE_OR_UNKNOWN"
        errors.append("decision is template or unknown")
        warnings.extend(lint_decision_result.get("warnings") or [])
        warnings.extend(lint_report_result.get("warnings") or [])
    else:
        handoff_state = "FAILED"
        errors.append(f"unknown decision_execution_state: {decision_state}")
        warnings.extend(lint_decision_result.get("warnings") or [])
        warnings.extend(lint_report_result.get("warnings") or [])

    ok = handoff_state in {"READY_FOR_CODEX", "REVIEW_COMPLETE", "REPORT_NEEDS_REVIEW"} and not errors
    return {
        "ok": ok,
        "handoff_state": handoff_state,
        "errors": errors,
        "warnings": warnings,
        "decision_execution_state": decision_state,
        "decision_ready_for_execution": consistency.get("decision_ready_for_execution"),
        "decision_report_id_match": consistency.get("decision_report_id_match"),
        "lint_decision_ok": lint_decision_result.get("ok"),
        "lint_report_ok": lint_report_result.get("ok"),
        "lint_decision_errors": lint_decision_result.get("errors") or [],
        "lint_report_errors": lint_report_result.get("errors") or [],
        "lint_report_warnings": lint_report_result.get("warnings") or [],
    }


def doctor(state_dir: Path, *, json_output: bool = False) -> dict[str, Any]:
    """Run diagnostic checks on project state and return a health report.

    Reuses existing lint_decision, lint_report, and status_summary helpers.
    Does not mutate live state files.
    """
    checks: list[dict[str, Any]] = []
    overall_status = "PASS"
    next_action: str | None = None

    # Check 1: decision packet parse and approval
    decision = read_decision_meta(state_dir)
    decision_status = str(decision.get("status") or "UNKNOWN")
    decision_id = str(decision.get("decision_id") or "")
    decision_parse_error = decision.get("parse_error")
    mainline = str(decision.get("mainline") or "")

    if decision_parse_error:
        checks.append({
            "name": "decision_parse",
            "status": "FAIL",
            "detail": f"decision_meta invalid: {decision_parse_error}",
        })
        overall_status = "FAIL"
    elif decision_status != "APPROVED":
        checks.append({
            "name": "decision_approval",
            "status": "FAIL",
            "detail": f"decision status is {decision_status}, expected APPROVED",
        })
        overall_status = "FAIL"
    else:
        checks.append({
            "name": "decision_approval",
            "status": "PASS",
            "detail": f"decision {decision_id} is APPROVED",
        })

    # Check 2: mainline
    ALLOWED_MAINLINES = {"engineering_branch", "reverse_solving", "tool_integration", "training_dataset"}
    if mainline not in ALLOWED_MAINLINES:
        checks.append({
            "name": "mainline",
            "status": "FAIL",
            "detail": f"mainline is {mainline}, expected one of {ALLOWED_MAINLINES}",
        })
        overall_status = "FAIL"
    else:
        checks.append({
            "name": "mainline",
            "status": "PASS",
            "detail": f"mainline is {mainline}",
        })

    # Check 3: skill profiles
    skill_profiles_value = decision.get("skill_profiles")
    skill_profile_lint = _lint_skill_profiles(
        state_dir=state_dir,
        decision_status=decision_status,
        mainline=mainline,
        skill_profiles_value=skill_profiles_value,
    )
    if skill_profile_lint["errors"]:
        checks.append({
            "name": "skill_profiles",
            "status": "FAIL",
            "detail": "; ".join(skill_profile_lint["errors"]),
        })
        overall_status = "FAIL"
    elif skill_profile_lint["warnings"]:
        checks.append({
            "name": "skill_profiles",
            "status": "WARN",
            "detail": "; ".join(skill_profile_lint["warnings"]),
        })
        if overall_status == "PASS":
            overall_status = "WARN"
    else:
        checks.append({
            "name": "skill_profiles",
            "status": "PASS",
            "detail": f"skill profiles active: {skill_profile_lint['parsed_skill_profiles']}",
        })

    # Check 4: report parse and match
    handoff_status = build_handoff_status(state_dir)
    report = handoff_status["codex_report"]
    report_status = str(report.get("status") or "UNKNOWN")
    report_id = str(report.get("report_id") or "")
    based_on_decision_id = str(report.get("based_on_decision_id") or "")
    report_parse_error = report.get("parse_error")

    if report_parse_error:
        checks.append({
            "name": "report_parse",
            "status": "FAIL",
            "detail": f"codex_report_summary invalid: {report_parse_error}",
        })
        overall_status = "FAIL"
    elif report_status in {"TEMPLATE_ONLY", "UNKNOWN"}:
        checks.append({
            "name": "report_parse",
            "status": "FAIL",
            "detail": f"report status is {report_status}",
        })
        overall_status = "FAIL"
    else:
        checks.append({
            "name": "report_parse",
            "status": "PASS",
            "detail": f"report {report_id} status is {report_status}",
        })

    # Check 5: report-to-decision ID match
    if based_on_decision_id and decision_id and based_on_decision_id != decision_id:
        checks.append({
            "name": "report_decision_match",
            "status": "FAIL",
            "detail": f"report based_on_decision_id ({based_on_decision_id}) does not match decision_id ({decision_id})",
        })
        overall_status = "FAIL"
    else:
        checks.append({
            "name": "report_decision_match",
            "status": "PASS",
            "detail": "report decision_id matches",
        })

    # Check 6: pytest result
    pytest_text = _read_text_or_empty(state_dir / "pytest_result.txt")
    pytest_validation = validate_pytest_result_for_report(pytest_text, report)
    pytest_result_present = bool(pytest_text.strip())

    if pytest_validation.get("parse_error"):
        checks.append({
            "name": "pytest_result",
            "status": "FAIL",
            "detail": f"pytest_result.txt invalid: {pytest_validation['parse_error']}",
        })
        overall_status = "FAIL"
    elif not pytest_result_present:
        checks.append({
            "name": "pytest_result",
            "status": "FAIL",
            "detail": "pytest_result.txt is missing or empty",
        })
        overall_status = "FAIL"
    elif not pytest_validation.get("matches_report"):
        checks.append({
            "name": "pytest_result",
            "status": "FAIL",
            "detail": "pytest_result.txt does not match report",
        })
        overall_status = "FAIL"
    elif pytest_validation.get("errors"):
        # Header/body contradiction or other validation errors
        checks.append({
            "name": "pytest_result",
            "status": "FAIL",
            "detail": "; ".join(pytest_validation["errors"]),
        })
        overall_status = "FAIL"
    elif not pytest_validation.get("tests_ran_covers_report"):
        checks.append({
            "name": "pytest_result",
            "status": "WARN",
            "detail": f"pytest_result missing {len(pytest_validation.get('missing_report_tests', []))} report tests",
        })
        if overall_status == "PASS":
            overall_status = "WARN"
    else:
        checks.append({
            "name": "pytest_result",
            "status": "PASS",
            "detail": "pytest_result.txt matches report and covers all tests",
        })

    # Check 7: archive state
    consistency = handoff_status["handoff_consistency"]
    decision_execution_state = str(consistency.get("decision_execution_state") or "UNKNOWN")
    task_packet = _read_json(state_dir / "task_packet.json")
    current_state = _read_json(state_dir / "current_state.json")
    round_consistency = build_round_consistency(
        decision=decision,
        report=report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    round_manifest_present = bool(round_consistency.get("round_manifest_present"))
    archive_status = str(round_consistency.get("archive_status") or "")

    if decision_execution_state == "CONSUMED_BY_SUCCESS_REPORT":
        if not round_manifest_present:
            checks.append({
                "name": "archive",
                "status": "WARN",
                "detail": "decision consumed but round manifest not present",
            })
            if overall_status == "PASS":
                overall_status = "WARN"
        elif archive_status != "archived":
            checks.append({
                "name": "archive",
                "status": "WARN",
                "detail": f"round manifest present but archive_status is {archive_status}",
            })
            if overall_status == "PASS":
                overall_status = "WARN"
        else:
            checks.append({
                "name": "archive",
                "status": "PASS",
                "detail": "decision consumed and archived",
            })
    elif decision_execution_state == "READY_FOR_EXECUTION":
        checks.append({
            "name": "archive",
            "status": "PASS",
            "detail": "decision ready for execution (archive not yet expected)",
        })
    else:
        checks.append({
            "name": "archive",
            "status": "WARN",
            "detail": f"decision_execution_state is {decision_execution_state}",
        })
        if overall_status == "PASS":
            overall_status = "WARN"

    # Check 8: stale/missing artifacts
    artifact_index = _read_json(state_dir / "artifact_index.json")
    freshness = _artifact_freshness_counts(artifact_index)
    artifact_classification = _classify_artifact_freshness(
        freshness=freshness,
        decision=decision,
        report=report,
        decision_execution_state=decision_execution_state,
        round_consistency=round_consistency,
        pytest_validation=pytest_validation,
    )
    missing_count = artifact_classification["counts"].get("missing", 0)
    stale_count = artifact_classification["counts"].get("stale", 0)

    if missing_count > 0 or stale_count > 0:
        checks.append({
            "name": "artifacts",
            "status": artifact_classification["status"],
            "detail": artifact_classification["detail"],
            "counts": artifact_classification["counts"],
            "classification": artifact_classification["classification"],
            "blocking": artifact_classification["blocking"],
        })
        if artifact_classification["blocking"] and overall_status == "PASS":
            overall_status = "WARN"
    else:
        checks.append({
            "name": "artifacts",
            "status": "PASS",
            "detail": "no missing or stale artifacts",
            "counts": artifact_classification["counts"],
            "classification": artifact_classification["classification"],
            "blocking": False,
        })

    # Check 9: state package responsibility classification
    state_package_classification = build_state_package_classification(state_dir)
    classification_checks = state_package_classification["checks"]
    if state_package_classification["status"] == "PASS":
        checks.append({
            "name": "state_package_classification",
            "status": "PASS",
            "detail": (
                "task_packet.json advisory; decision_packet.md authoritative; "
                "gates/*.json derived_cache; rounds/<round_id>/* archive; "
                "solve_reports/ and PROJECT_PROGRESS_LOG.txt heavy_history"
            ),
            "summary": state_package_classification["summary"],
            "checks": classification_checks,
            "entries": state_package_classification["entries"],
        })
    else:
        failed = [check["name"] for check in classification_checks if check["status"] != "PASS"]
        checks.append({
            "name": "state_package_classification",
            "status": "FAIL",
            "detail": f"state package classification checks failed: {failed}",
            "summary": state_package_classification["summary"],
            "checks": classification_checks,
            "entries": state_package_classification["entries"],
        })
        overall_status = "FAIL"

    if overall_status == "FAIL":
        next_action = "fix_project_state_issues"

    result = {
        "status": overall_status,
        "checks": checks,
        "next_action": next_action,
        "decision_id": decision_id,
        "report_id": report_id,
        "decision_execution_state": decision_execution_state,
        "artifact_freshness": artifact_classification,
        "state_package_classification": state_package_classification,
    }

    if json_output:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"doctor: {overall_status}")
        for check in checks:
            symbol = (
                "PASS"
                if check["status"] == "PASS"
                else ("WARN" if check["status"] == "WARN" else ("INFO" if check["status"] == "INFO" else "FAIL"))
            )
            print(f"  [{symbol}] {check['name']}: {check['detail']}")
        if next_action:
            print(f"  next_action: {next_action}")

    return result


def ensure_state_layout(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    rounds_dir = state_dir / "rounds"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    (rounds_dir / ".gitkeep").touch()
    readme_path = state_dir / "README.md"
    if _is_missing_or_default(readme_path, PROJECT_STATE_README):
        _write_text(readme_path, PROJECT_STATE_README)
    decision_path = state_dir / "decision_packet.md"
    if _is_missing_or_default(decision_path, DECISION_PACKET_TEMPLATE, LEGACY_DECISION_PACKET_TEMPLATE):
        _write_text(decision_path, DECISION_PACKET_TEMPLATE)
    report_path = state_dir / "codex_execution_report.md"
    if _is_missing_or_default(
        report_path,
        CODEX_EXECUTION_REPORT_TEMPLATE,
        LEGACY_CODEX_EXECUTION_REPORT_TEMPLATE,
    ):
        _write_text(report_path, CODEX_EXECUTION_REPORT_TEMPLATE)


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _latest_path(paths: list[Path]) -> Path | None:
    return max(paths, key=_safe_mtime) if paths else None


def _classify_artifact(path: Path, sample: str) -> str | None:
    name = path.name
    lower_name = name.lower()
    if lower_name == "h1_h3_boundary_validation.json" and path.parent.name.lower() == "validation":
        return "h1_h3_boundary_validation_runtime"
    for kind, expected_name in IMPORTANT_ARTIFACTS.items():
        if lower_name == expected_name.lower():
            return kind
    if lower_name.endswith("_compare_probe.json"):
        return "compare_probe"
    if lower_name.endswith("_compare_probe.log"):
        return "compare_probe_log"
    if lower_name.endswith("_search_checkpoint.json") and sample.lower() in lower_name:
        return "checkpoint"
    return None


def _scan_artifact_files(
    reports_dir: Path,
    sample: str,
    harness_run: Path | None = None,
) -> list[Path]:
    candidates: list[Path] = []

    legacy_tool_artifacts = reports_dir / "tool_artifacts"
    if legacy_tool_artifacts.exists():
        candidates.extend(item for item in legacy_tool_artifacts.rglob("*") if item.is_file())

    harness_root = reports_dir / "harness_runs"
    if harness_run is not None:
        run_dirs = [harness_run] if harness_run.exists() and harness_run.is_dir() else []
    elif harness_root.exists():
        run_dirs = [item for item in harness_root.iterdir() if item.is_dir()]
    else:
        run_dirs = []
    if run_dirs:
        for run_dir in run_dirs:
            if not run_dir.is_dir():
                continue
            for direct_name in ("summary.json", "run_manifest.json"):
                path = run_dir / direct_name
                if path.exists():
                    candidates.append(path)
            case_results = run_dir / "case_results"
            if case_results.exists():
                candidates.extend(item for item in case_results.glob("*.json") if item.is_file())
            tool_artifacts = run_dir / "reports" / "tool_artifacts"
            if tool_artifacts.exists():
                candidates.extend(item for item in tool_artifacts.rglob("*") if item.is_file())

    return candidates


def _iter_case_artifact_manifest_entries(case_result_paths: list[Path], sample: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for case_result_path in case_result_paths:
        data = _read_json(case_result_path)
        manifest = data.get("artifact_manifest")
        if not isinstance(manifest, list):
            continue
        for raw_entry in manifest:
            if not isinstance(raw_entry, dict):
                continue
            raw_path = str(raw_entry.get("path") or "").strip()
            if not raw_path:
                continue
            path = _path_from_json(raw_path)
            kind = str(raw_entry.get("kind") or "").strip() or (_classify_artifact(path, sample) or "")
            if not kind:
                continue
            entry = dict(raw_entry)
            entry["kind"] = kind
            entry["path"] = path
            entries.append(entry)
    return entries


def _apply_case_artifact_manifest(
    *,
    latest_artifact_paths: dict[str, Path],
    recent_artifacts: list[dict[str, Any]],
    case_result_paths: list[Path],
    reports_dir: Path,
    latest_run: Path | None,
    sample: str,
) -> None:
    for entry in _iter_case_artifact_manifest_entries(case_result_paths, sample):
        kind = str(entry["kind"])
        path = entry["path"]
        if not isinstance(path, Path):
            continue
        latest_artifact_paths[kind] = path
        recent_artifacts.append(
            {
                "kind": kind,
                "path": _path_for_json(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "modified_at": (
                    datetime.fromtimestamp(_safe_mtime(path), tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                    if path.exists()
                    else None
                ),
                "source": "case_result.artifact_manifest",
                "freshness": _artifact_freshness(path, reports_dir=reports_dir, latest_run=latest_run),
            }
        )


def _resolve_latest_run(reports_dir: Path, run_name: str = "") -> Path | None:
    harness_root = reports_dir / "harness_runs"
    if not harness_root.exists():
        return None
    if run_name:
        run_dir = harness_root / run_name
        return run_dir if run_dir.exists() and run_dir.is_dir() else None
    run_dirs = [item for item in harness_root.iterdir() if item.is_dir()]
    return _latest_path(run_dirs)


def _find_fallback_harness_run(
    reports_dir: Path,
    latest_run: Path | None,
) -> dict[str, Any] | None:
    """Find the most recent complete harness run with case_results/ as a fallback.

    A complete run must have:
    - case_results/ directory with at least one .json file
    - summary.json with error_cases == 0
    - run_manifest.json

    The fallback is explicitly marked so it is not silently promoted as latest/current.
    """
    harness_root = reports_dir / "harness_runs"
    if not harness_root.exists():
        return None
    candidates: list[dict[str, Any]] = []
    for run_dir in harness_root.iterdir():
        if not run_dir.is_dir():
            continue
        if latest_run is not None and run_dir.resolve() == latest_run.resolve():
            continue
        case_results_dir = run_dir / "case_results"
        if not case_results_dir.exists() or not any(case_results_dir.glob("*.json")):
            continue
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            continue
        summary_data = _read_json(str(summary_path))
        if not isinstance(summary_data, dict):
            continue
        if int(summary_data.get("error_cases", 0) or 0) > 0:
            continue
        candidates.append(
            {
                "run_dir": run_dir,
                "mtime": _safe_mtime(run_dir),
                "run_name": run_dir.name,
                "summary_path": summary_path,
                "manifest_path": manifest_path,
                "executed_cases": summary_data.get("executed_cases", 0),
                "total_cases": summary_data.get("total_cases", 0),
            }
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: item["mtime"], reverse=True)
    best = candidates[0]
    return {
        "run_name": best["run_name"],
        "run_path": _path_for_json(best["run_dir"]),
        "summary_path": _path_for_json(best["summary_path"]),
        "manifest_path": _path_for_json(best["manifest_path"]),
        "executed_cases": best["executed_cases"],
        "total_cases": best["total_cases"],
        "provenance": "fallback_from_invalid_latest_run",
    }


def _audit_fallback_evidence_readiness(
    fallback_info: dict[str, Any],
) -> dict[str, Any]:
    """Audit the selected fallback harness evidence for readiness.

    Performs bounded metadata-only inspection of the fallback summary,
    run manifest, and case_results directory. Returns a readiness
    classification and supporting metadata.
    """
    summary_path = _path_from_json(fallback_info.get("summary_path", ""))
    manifest_path = _path_from_json(fallback_info.get("manifest_path", ""))
    run_path = _path_from_json(fallback_info.get("run_path", ""))

    audit: dict[str, Any] = {
        "run_name": fallback_info.get("run_name"),
        "audited_at": _now_iso(),
        "summary_present": summary_path.exists(),
        "manifest_present": manifest_path.exists(),
        "case_results_dir_present": False,
        "case_result_count": 0,
        "case_result_statuses": [],
        "structured_evidence_count": 0,
        "tool_artifact_count": 0,
        "candidate_count": 0,
        "validation_count": 0,
        "has_errors": False,
        "classification": "fallback_evidence_schema_gap",
        "reason": "default_schema_gap",
        "next_local_action": "repair_selected_fallback_evidence",
    }

    if not summary_path.exists() or not manifest_path.exists():
        audit["reason"] = "missing_summary_or_manifest"
        audit["classification"] = "fallback_evidence_incomplete"
        audit["next_local_action"] = "repair_selected_fallback_evidence"
        return audit

    summary_data = _read_json(str(summary_path))
    manifest_data = _read_json(str(manifest_path))
    if not isinstance(summary_data, dict) or not isinstance(manifest_data, dict):
        audit["reason"] = "unparseable_summary_or_manifest"
        audit["classification"] = "fallback_evidence_incomplete"
        audit["next_local_action"] = "repair_selected_fallback_evidence"
        return audit

    case_results_dir = run_path / "case_results"
    audit["case_results_dir_present"] = case_results_dir.exists()
    has_not_found_status = False
    has_instrumentation_incomplete = False
    if case_results_dir.exists():
        case_result_files = list(case_results_dir.glob("*.json"))
        audit["case_result_count"] = len(case_result_files)
        for crf in case_result_files:
            cr_data = _read_json(str(crf))
            if isinstance(cr_data, dict):
                status = cr_data.get("status", "unknown")
                audit["case_result_statuses"].append(status)
                if status == "not_found":
                    has_not_found_status = True
                audit["structured_evidence_count"] = max(
                    audit["structured_evidence_count"],
                    cr_data.get("structured_evidence_count", 0),
                )
                audit["tool_artifact_count"] = max(
                    audit["tool_artifact_count"],
                    cr_data.get("tool_artifact_count", 0),
                )
                audit["candidate_count"] = max(
                    audit["candidate_count"],
                    cr_data.get("candidate_count", 0),
                )
                audit["validation_count"] = max(
                    audit["validation_count"],
                    cr_data.get("validation_count", 0),
                )
                if cr_data.get("error"):
                    audit["has_errors"] = True
                # Check embedded artifact manifest for instrumentation_incomplete
                artifact_manifest = cr_data.get("artifact_manifest", [])
                if isinstance(artifact_manifest, list):
                    for entry in artifact_manifest:
                        if isinstance(entry, dict) and entry.get("classification") == "instrumentation_incomplete":
                            has_instrumentation_incomplete = True

    # Check summary-level not_found_cases
    summary_not_found_cases = 0
    if isinstance(summary_data, dict):
        summary_not_found_cases = int(summary_data.get("not_found_cases", 0) or 0)

    # Build repair diagnostics from detected blockers.
    blockers: list[dict[str, Any]] = []
    if audit["has_errors"]:
        blockers.append({
            "code": "case_result_contains_errors",
            "owner_component": "case_result_writer",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if audit["case_result_count"] == 0:
        blockers.append({
            "code": "no_case_results_found",
            "owner_component": "harness",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if has_not_found_status:
        blockers.append({
            "code": "case_result_status_is_not_found",
            "owner_component": "case_result_writer",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if summary_not_found_cases > 0:
        blockers.append({
            "code": "summary_reports_not_found_cases",
            "owner_component": "harness",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if has_instrumentation_incomplete:
        blockers.append({
            "code": "instrumentation_incomplete_in_artifact_manifest",
            "owner_component": "artifact_manifest_writer",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if audit["validation_count"] == 0:
        blockers.append({
            "code": "validation_count_is_zero",
            "owner_component": "case_result_writer",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if audit["structured_evidence_count"] == 0 and audit["tool_artifact_count"] == 0:
        blockers.append({
            "code": "no_structured_evidence_or_tool_artifacts",
            "owner_component": "artifact_manifest_writer",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })
    if audit["candidate_count"] == 0:
        blockers.append({
            "code": "no_candidates_generated",
            "owner_component": "solver",
            "repairable_from_existing_metadata": False,
            "required_rebuild": True,
        })

    # Classify readiness based on bounded metadata inspection.
    if blockers:
        audit["classification"] = "fallback_evidence_incomplete"
        audit["reason"] = blockers[0]["code"]
        # Determine precise next_local_action based on primary blocker owner.
        primary_owner = blockers[0]["owner_component"]
        if primary_owner == "harness":
            audit["next_local_action"] = "rebuild_harness_artifact"
        elif primary_owner == "case_result_writer":
            audit["next_local_action"] = "repair_harness_case_result_materialization"
        elif primary_owner == "artifact_manifest_writer":
            audit["next_local_action"] = "repair_artifact_manifest_metadata"
        elif primary_owner == "solver":
            audit["next_local_action"] = "repair_solver_candidate_generation"
        else:
            audit["next_local_action"] = "repair_selected_fallback_evidence"
        audit["repair_diagnostics"] = {
            "blockers": blockers,
            "repairable_from_existing_metadata": all(b["repairable_from_existing_metadata"] for b in blockers),
            "required_rebuild": any(b["required_rebuild"] for b in blockers),
            "primary_blocker_owner": primary_owner,
            "next_local_action": audit["next_local_action"],
        }
    else:
        # All strictness checks passed: evidence is genuinely ready.
        audit["classification"] = "fallback_evidence_ready_for_reverse_decision"
        audit["reason"] = (
            f"has_{audit['case_result_count']}_case_result(s)_with_"
            f"{audit['structured_evidence_count']}_structured_evidence_"
            f"{audit['tool_artifact_count']}_tool_artifacts_"
            f"{audit['candidate_count']}_candidates_"
            f"{audit['validation_count']}_validations"
        )
        audit["next_local_action"] = "prepare_reverse_solving_from_selected_fallback_evidence"
        audit["repair_diagnostics"] = {
            "blockers": [],
            "repairable_from_existing_metadata": True,
            "required_rebuild": False,
            "primary_blocker_owner": None,
            "next_local_action": audit["next_local_action"],
        }

    return audit


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _path_from_json(path: str) -> Path:
    parsed = Path(path)
    return parsed if parsed.is_absolute() else Path.cwd() / parsed


def _artifact_source_run(path: Path, reports_dir: Path) -> str:
    try:
        parts = path.resolve().relative_to(reports_dir.resolve()).parts
    except ValueError:
        return ""
    lowered = tuple(part.lower() for part in parts)
    if len(parts) >= 2 and lowered[0] == "harness_runs":
        return parts[1]
    if lowered and lowered[0] == "tool_artifacts":
        return "legacy_tool_artifacts"
    return ""


def _artifact_freshness(path: Path | None, *, reports_dir: Path, latest_run: Path | None) -> str:
    if path is None or not path.exists():
        return "missing"
    source_run = _artifact_source_run(path, reports_dir)
    if not source_run:
        return "unknown"
    if latest_run is not None and _is_relative_to(path, latest_run):
        return "current"
    return "stale"


def _artifact_metadata_entry(
    *,
    kind: str,
    path: Path | None,
    reports_dir: Path,
    latest_run: Path | None,
) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "path": _path_for_json(path) if path is not None else None,
            "kind": kind,
            "source_run": "",
            "modified_at": None,
            "size_bytes": None,
            "sha256": None,
            "freshness": "missing",
        }
    return {
        "path": _path_for_json(path),
        "kind": kind,
        "source_run": _artifact_source_run(path, reports_dir),
        "modified_at": datetime.fromtimestamp(_safe_mtime(path), tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "freshness": _artifact_freshness(path, reports_dir=reports_dir, latest_run=latest_run),
    }


def _artifact_freshness_counts(artifact_index: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    latest_artifacts_v2 = artifact_index.get("latest_artifacts_v2", {})
    if not isinstance(latest_artifacts_v2, dict):
        return counts
    for item in latest_artifacts_v2.values():
        if not isinstance(item, dict):
            continue
        freshness = str(item.get("freshness") or "unknown")
        counts[freshness] = counts.get(freshness, 0) + 1
    return dict(sorted(counts.items()))


def _state_package_entry(
    path: str,
    classification: str,
    *,
    role: str,
    default_context: bool,
    authority: str,
    present: bool | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": path,
        "classification": classification,
        "role": role,
        "default_context": default_context,
        "authority": authority,
    }
    if present is not None:
        entry["present"] = present
    return entry


def _state_package_classification_checks(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path = {str(entry.get("path") or ""): entry for entry in entries}

    def _matches(path: str, classification: str, *, default_context: bool | None = None) -> bool:
        entry = by_path.get(path)
        if not entry or entry.get("classification") != classification:
            return False
        if default_context is not None and bool(entry.get("default_context")) is not default_context:
            return False
        return True

    gate_entries = [
        entry
        for entry in entries
        if str(entry.get("path") or "").startswith("project_state/gates/")
        and str(entry.get("path") or "").endswith(".json")
    ]
    round_entries = [
        entry
        for entry in entries
        if str(entry.get("path") or "").startswith("project_state/rounds/")
    ]

    return [
        {
            "name": "task_packet_advisory_only",
            "status": "PASS" if _matches("project_state/task_packet.json", "advisory") else "FAIL",
            "detail": "task_packet.json is advisory and cannot override decision_packet.md",
        },
        {
            "name": "decision_packet_authoritative",
            "status": "PASS" if _matches("project_state/decision_packet.md", "authoritative") else "FAIL",
            "detail": "decision_packet.md is the current execution authority",
        },
        {
            "name": "gate_outputs_derived_cache",
            "status": (
                "PASS"
                if all(entry.get("classification") == "derived_cache" for entry in gate_entries)
                else "FAIL"
            ),
            "detail": f"{len(gate_entries)} gates/*.json entries are derived_cache",
        },
        {
            "name": "rounds_archive_not_default_context",
            "status": (
                "PASS"
                if all(
                    entry.get("classification") == "archive"
                    and bool(entry.get("default_context")) is False
                    for entry in round_entries
                )
                else "FAIL"
            ),
            "detail": f"{len(round_entries)} rounds/<round_id>/* entries are archive and not default context",
        },
        {
            "name": "heavy_history_not_default_context",
            "status": (
                "PASS"
                if _matches("solve_reports/", "heavy_history", default_context=False)
                and _matches("PROJECT_PROGRESS_LOG.txt", "heavy_history", default_context=False)
                else "FAIL"
            ),
            "detail": "solve_reports/ and PROJECT_PROGRESS_LOG.txt are heavy_history and not default context",
        },
    ]


def build_state_package_classification(state_dir: Path) -> dict[str, Any]:
    """Classify project_state files by responsibility without reading heavy history."""
    entries: list[dict[str, Any]] = []

    authoritative_entries = (
        (
            "project_state/decision_packet.md",
            "current_execution_authority",
            "controls_current_round",
            state_dir / "decision_packet.md",
        ),
        (
            "project_state/current_state.json",
            "current_state_summary",
            "required_fact_source",
            state_dir / "current_state.json",
        ),
        (
            "project_state/artifact_index.json",
            "artifact_index_summary",
            "required_fact_source",
            state_dir / "artifact_index.json",
        ),
        (
            "project_state/negative_results.json",
            "negative_result_guardrails",
            "required_fact_source",
            state_dir / "negative_results.json",
        ),
        (
            "project_state/codex_execution_report.md",
            "execution_closeout_report",
            "required_fact_source",
            state_dir / "codex_execution_report.md",
        ),
        (
            "project_state/pytest_result.txt",
            "verification_result",
            "required_fact_source",
            state_dir / "pytest_result.txt",
        ),
    )
    for path, role, authority, local_path in authoritative_entries:
        entries.append(
            _state_package_entry(
                path,
                "authoritative",
                role=role,
                default_context=True,
                authority=authority,
                present=local_path.exists(),
            )
        )

    advisory_entries = (
        (
            "project_state/task_packet.json",
            "suggested_task_context",
            "advisory_only_cannot_override_decision_packet",
            state_dir / "task_packet.json",
        ),
        (
            "project_state/model_gate.json",
            "model_call_hint",
            "advisory_only_cannot_override_decision_packet",
            state_dir / "model_gate.json",
        ),
    )
    for path, role, authority, local_path in advisory_entries:
        entries.append(
            _state_package_entry(
                path,
                "advisory",
                role=role,
                default_context=True,
                authority=authority,
                present=local_path.exists(),
            )
        )

    gates_dir = state_dir / "gates"
    gate_paths = sorted(gates_dir.glob("*.json")) if gates_dir.exists() else []
    for path in gate_paths:
        entries.append(
            _state_package_entry(
                f"project_state/gates/{path.name}",
                "derived_cache",
                role="regenerable_gate_output",
                default_context=False,
                authority="derived_from_project_gate_commands",
                present=path.exists(),
            )
        )

    rounds_dir = state_dir / "rounds"
    round_dirs = sorted(path for path in rounds_dir.iterdir() if path.is_dir()) if rounds_dir.exists() else []
    for path in round_dirs:
        entries.append(
            _state_package_entry(
                f"project_state/rounds/{path.name}/*",
                "archive",
                role="historical_round_archive",
                default_context=False,
                authority="historical_record_not_current_execution_authority",
                present=True,
            )
        )

    entries.append(
        _state_package_entry(
            "solve_reports/",
            "heavy_history",
            role="heavy_solver_and_harness_history",
            default_context=False,
            authority="historical_output_not_default_context",
            present=(state_dir.parent / "solve_reports").exists(),
        )
    )
    entries.append(
        _state_package_entry(
            "PROJECT_PROGRESS_LOG.txt",
            "heavy_history",
            role="heavy_progress_history",
            default_context=False,
            authority="historical_output_not_default_context",
            present=(state_dir.parent / "PROJECT_PROGRESS_LOG.txt").exists(),
        )
    )

    summary = {name: 0 for name in STATE_PACKAGE_CLASSIFICATION_ORDER}
    for entry in entries:
        classification = str(entry.get("classification") or "")
        summary[classification] = summary.get(classification, 0) + 1
    summary = {key: summary[key] for key in STATE_PACKAGE_CLASSIFICATION_ORDER if key in summary}
    checks = _state_package_classification_checks(entries)
    return {
        "status": "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL",
        "summary": summary,
        "entries": entries,
        "checks": checks,
    }


def _classify_artifact_freshness(
    *,
    freshness: dict[str, int],
    decision: dict[str, Any],
    report: dict[str, Any],
    decision_execution_state: str,
    round_consistency: dict[str, Any],
    pytest_validation: dict[str, Any],
) -> dict[str, Any]:
    counts = dict(sorted(freshness.items()))
    missing_count = counts.get("missing", 0)
    stale_count = counts.get("stale", 0)
    has_freshness_problem = missing_count > 0 or stale_count > 0
    if not has_freshness_problem:
        return {
            "status": "PASS",
            "classification": "artifact_freshness_current",
            "blocking": False,
            "counts": counts,
            "detail": "no missing or stale artifacts",
            "reason": "artifact_index reports no missing or stale latest artifacts",
        }

    if _historical_artifact_freshness_is_non_blocking(
        decision=decision,
        report=report,
        decision_execution_state=decision_execution_state,
        round_consistency=round_consistency,
        pytest_validation=pytest_validation,
    ):
        return {
            "status": "INFO",
            "classification": "historical_sample_artifacts_non_blocking",
            "blocking": False,
            "counts": counts,
            "detail": f"{missing_count} missing, {stale_count} stale historical sample artifacts (non-blocking)",
            "reason": "healthy engineering round does not claim current sample artifact freshness",
        }

    return {
        "status": "WARN",
        "classification": "artifact_freshness_requires_review",
        "blocking": True,
        "counts": counts,
        "detail": f"{missing_count} missing, {stale_count} stale artifacts",
        "reason": "active context may depend on current artifact evidence or handoff health is not fully clean",
    }


def _historical_artifact_freshness_is_non_blocking(
    *,
    decision: dict[str, Any],
    report: dict[str, Any],
    decision_execution_state: str,
    round_consistency: dict[str, Any],
    pytest_validation: dict[str, Any],
) -> bool:
    ALLOWED_NON_BLOCKING_MAINLINES = {"engineering_branch", "reverse_solving", "tool_integration", "training_dataset"}
    if str(decision.get("mainline") or "") not in ALLOWED_NON_BLOCKING_MAINLINES:
        return False
    if decision_execution_state != "CONSUMED_BY_SUCCESS_REPORT":
        return False
    if str(report.get("status") or "") != "SUCCESS":
        return False
    if not bool(pytest_validation.get("matches_report")):
        return False
    if not bool(pytest_validation.get("tests_ran_covers_report")):
        return False
    if not bool(round_consistency.get("round_manifest_present")):
        return False
    if str(round_consistency.get("archive_status") or "") != "archived":
        return False
    return not _report_claims_sample_artifact_freshness(report)


def _report_claims_sample_artifact_freshness(report: dict[str, Any]) -> bool:
    artifact_fields = [
        report.get("generated_artifacts"),
        report.get("verified_artifacts"),
    ]
    sample_artifact_markers = ("solve_reports", "harness_runs", "tool_artifacts")
    for value in artifact_fields:
        if not isinstance(value, list):
            continue
        for item in value:
            text = str(item).replace("/", "\\")
            if any(marker in text for marker in sample_artifact_markers):
                return True
    return False


def build_artifact_index(
    *,
    reports_dir: Path,
    sample: str,
    run_name: str = "",
    max_artifacts: int = 20,
) -> dict[str, Any]:
    generated_at = _now_iso()
    missing: list[str] = []
    if not reports_dir.exists():
        return {
            "sample": sample,
            "reports_dir": _path_for_json(reports_dir),
            "latest_harness_run": None,
            "latest_summary": None,
            "latest_case_results": [],
            "latest_artifacts": {key: None for key in LATEST_ARTIFACT_KEYS},
            "latest_artifacts_v2": {
                key: _artifact_metadata_entry(
                    kind=key,
                    path=None,
                    reports_dir=reports_dir,
                    latest_run=None,
                )
                for key in LATEST_ARTIFACT_KEYS
            },
            "recent_artifacts": [],
            "missing": ["reports_dir"],
            "generated_at": generated_at,
        }

    latest_run = _resolve_latest_run(reports_dir, run_name=run_name)
    latest_summary = latest_run / "summary.json" if latest_run and (latest_run / "summary.json").exists() else None
    latest_case_results = (
        sorted((latest_run / "case_results").glob("*.json"), key=_safe_mtime, reverse=True)
        if latest_run and (latest_run / "case_results").exists()
        else []
    )

    latest_artifact_paths: dict[str, Path] = {}
    recent_artifacts: list[dict[str, Any]] = []
    for path in _scan_artifact_files(reports_dir, sample, harness_run=latest_run if run_name else None):
        kind = _classify_artifact(path, sample)
        if not kind:
            continue
        current = latest_artifact_paths.get(kind)
        if current is None or _safe_mtime(path) > _safe_mtime(current):
            latest_artifact_paths[kind] = path
        recent_artifacts.append(
            {
                "kind": kind,
                "path": _path_for_json(path),
                "size_bytes": path.stat().st_size,
                "modified_at": datetime.fromtimestamp(_safe_mtime(path), tz=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            }
        )
    _apply_case_artifact_manifest(
        latest_artifact_paths=latest_artifact_paths,
        recent_artifacts=recent_artifacts,
        case_result_paths=latest_case_results,
        reports_dir=reports_dir,
        latest_run=latest_run,
        sample=sample,
    )

    latest_artifacts: dict[str, str | None] = {key: None for key in LATEST_ARTIFACT_KEYS}
    latest_artifacts.update(
        {
            kind: _path_for_json(path)
            for kind, path in sorted(latest_artifact_paths.items())
        }
    )
    if latest_summary and not latest_artifacts.get("summary"):
        latest_artifacts["summary"] = _path_for_json(latest_summary)
    manifest = latest_run / "run_manifest.json" if latest_run else None
    if manifest and manifest.exists() and not latest_artifacts.get("run_manifest"):
        latest_artifacts["run_manifest"] = _path_for_json(manifest)

    latest_artifacts_v2 = {
        kind: _artifact_metadata_entry(
            kind=kind,
            path=_path_from_json(path) if path else None,
            reports_dir=reports_dir,
            latest_run=latest_run,
        )
        for kind, path in latest_artifacts.items()
    }

    if not latest_run:
        missing.append("latest_harness_run")
    if not latest_summary:
        missing.append("summary")
    if not latest_case_results:
        missing.append("case_results")
    for required in ("frontier_summary", "strata_summary"):
        if not latest_artifacts.get(required):
            missing.append(required)
    if not any(latest_artifacts.get(key) for key in RUNTIME_VALIDATION_KEYS):
        missing.append("runtime_validation")

    recent_artifacts.sort(key=lambda item: str(item["modified_at"]), reverse=True)
    return {
        "sample": sample,
        "reports_dir": _path_for_json(reports_dir),
        "latest_harness_run": _path_for_json(latest_run) if latest_run else None,
        "latest_summary": _path_for_json(latest_summary) if latest_summary else None,
        "latest_case_results": [_path_for_json(path) for path in latest_case_results],
        "latest_artifacts": latest_artifacts,
        "latest_artifacts_v2": latest_artifacts_v2,
        "recent_artifacts": recent_artifacts[: max(0, max_artifacts)],
        "missing": sorted(set(missing)),
        "generated_at": generated_at,
    }


def _compact_candidate(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(entry, dict) or not entry:
        return None
    candidate_hex = str(entry.get("candidate_hex") or "").strip()
    cand8_hex = str(entry.get("cand8_hex") or "").strip()
    candidate_prefix = cand8_hex or (candidate_hex[:16] if candidate_hex else "")
    return {
        "candidate_prefix": candidate_prefix or None,
        "candidate_hex": candidate_hex or None,
        "runtime_ci_exact_wchars": entry.get("runtime_ci_exact_wchars"),
        "runtime_ci_distance5": entry.get("runtime_ci_distance5"),
        "compare_semantics_agree": entry.get("compare_semantics_agree"),
        "frontier_role": entry.get("frontier_role"),
        "anchor_mode": entry.get("anchor_mode"),
        "frontier_submode": entry.get("frontier_submode"),
        "source": entry.get("stage") or entry.get("anchor_lineage") or None,
    }


def _best_from_frontier_anchors(
    frontier_summary: dict[str, Any],
    *,
    exact_wchars: int | None = None,
    role_contains: str = "",
) -> dict[str, Any] | None:
    items = frontier_summary.get("frontier_anchor_candidates", [])
    if not isinstance(items, list):
        return None
    filtered: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if exact_wchars is not None and int(item.get("runtime_ci_exact_wchars", -1) or -1) != exact_wchars:
            continue
        if role_contains and role_contains not in str(item.get("frontier_role", "")):
            continue
        filtered.append(item)
    if not filtered:
        return None
    return min(filtered, key=lambda item: int(item.get("runtime_ci_distance5", 1 << 30) or 1 << 30))


def build_current_state(*, artifact_index: dict[str, Any], sample: str) -> dict[str, Any]:
    artifacts = artifact_index.get("latest_artifacts", {})
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    artifact_refs = {key: value for key, value in artifacts.items() if value}
    strata_summary = _read_json(artifact_refs.get("strata_summary"))
    frontier_summary = _read_json(artifact_refs.get("frontier_summary"))
    transform_trace_consistency = _read_json(artifact_refs.get("transform_trace_consistency"))
    dynamic_compare_path_probe = _read_json(artifact_refs.get("dynamic_compare_path_probe"))
    pre_rc4_material_probe = _read_json(artifact_refs.get("pre_rc4_material_probe"))
    base64_rc4_static_point_discovery = _read_json(artifact_refs.get("base64_rc4_static_point_discovery"))
    base64_rc4_breakpoint_probe = _read_json(artifact_refs.get("base64_rc4_breakpoint_probe"))
    compare_stack_pivot_probe = _read_json(artifact_refs.get("compare_stack_pivot_probe"))
    compare_handoff_probe = _read_json(artifact_refs.get("compare_handoff_probe"))
    compare_handoff_slice_probe = _read_json(artifact_refs.get("compare_handoff_slice_probe"))
    compare_handoff_return_site_probe = _read_json(artifact_refs.get("compare_handoff_return_site_probe"))
    compare_producer_trace_probe = _read_json(artifact_refs.get("compare_producer_trace_probe"))
    compare_producer_material_confirmation = _read_json(
        artifact_refs.get("compare_producer_material_confirmation")
    )
    compare_pre_compare_handoff_target_probe = _read_json(
        artifact_refs.get("compare_pre_compare_handoff_target_probe")
    )
    function_semantic_audit = _read_json(artifact_refs.get("function_semantic_audit"))
    material_hook_runtime_validation = _read_json(artifact_refs.get("material_hook_runtime_validation"))
    post_handoff_branch_outcome_audit = _read_json(
        artifact_refs.get("post_handoff_branch_outcome_audit")
    )
    post_handoff_exception_unwind_audit = _read_json(
        artifact_refs.get("post_handoff_exception_unwind_audit")
    )
    compare_hook_path_reachability_audit = _read_json(
        artifact_refs.get("compare_hook_path_reachability_audit")
    )
    compare_handoff_exit_classifier_audit = _read_json(
        artifact_refs.get("compare_handoff_exit_classifier_audit")
    )
    compare_handoff_path_divergence_audit = _read_json(
        artifact_refs.get("compare_handoff_path_divergence_audit")
    )
    compare_handoff_edge_operand_provenance_audit = _read_json(
        artifact_refs.get("compare_handoff_edge_operand_provenance_audit")
    )
    compare_handoff_branch_operand_runtime_audit = _read_json(
        artifact_refs.get("compare_handoff_branch_operand_runtime_audit")
    )
    compare_handoff_hook_surface_repair_audit = _read_json(
        artifact_refs.get("compare_handoff_hook_surface_repair_audit")
    )
    compare_handoff_post_entry_step_runtime_audit = _read_json(
        artifact_refs.get("compare_handoff_post_entry_step_runtime_audit")
    )
    compare_handoff_narrower_post_entry_breakpoint_audit = _read_json(
        artifact_refs.get("compare_handoff_narrower_post_entry_breakpoint_audit")
    )
    compare_lhs_producer_audit = _read_json(artifact_refs.get("compare_lhs_producer_audit"))
    compare_lhs_upstream_writer_audit = _read_json(artifact_refs.get("compare_lhs_upstream_writer_audit"))
    compare_callsite_reanchor_audit = _read_json(
        artifact_refs.get("compare_callsite_reanchor_and_lhs_provenance_audit")
    )
    compare_real_lhs_provenance_audit = _read_json(
        artifact_refs.get("compare_real_lhs_provenance_audit")
    )
    compare_esi_source_window_audit = _read_json(
        artifact_refs.get("compare_esi_source_window_audit")
    )
    compare_lhs_slot_writer_source_audit = _read_json(
        artifact_refs.get("compare_lhs_slot_writer_source_audit")
    )
    compare_lhs_slot_writer_predecessor_audit = _read_json(
        artifact_refs.get("compare_lhs_slot_writer_predecessor_audit")
    )
    uncertainty: list[str] = []

    exact2 = _compact_candidate(strata_summary.get("best_exact2_runtime"))
    if exact2 is None:
        exact2 = _compact_candidate(_best_from_frontier_anchors(frontier_summary, exact_wchars=2))
    if exact2 is None:
        uncertainty.append("best_exact2_runtime")

    exact1_source = strata_summary.get("best_exact1_runtime")
    if not isinstance(exact1_source, dict) or not exact1_source:
        frontier_candidate = strata_summary.get("best_frontier_runtime")
        if isinstance(frontier_candidate, dict) and int(frontier_candidate.get("runtime_ci_exact_wchars", -1) or -1) == 1:
            exact1_source = frontier_candidate
        else:
            exact1_source = _best_from_frontier_anchors(frontier_summary, exact_wchars=1, role_contains="exact1")
    exact1 = _compact_candidate(exact1_source if isinstance(exact1_source, dict) else None)
    if exact1 is None:
        uncertainty.append("best_exact1_runtime")

    frontier = _compact_candidate(strata_summary.get("best_frontier_runtime"))
    if frontier is None:
        frontier = _compact_candidate(_best_from_frontier_anchors(frontier_summary, role_contains="frontier"))
    if frontier is None:
        uncertainty.append("best_frontier_runtime")

    stage = (
        frontier_summary.get("frontier_stall_stage")
        or strata_summary.get("frontier_stall_stage")
        or frontier_summary.get("frontier_active_lane")
        or None
    )
    reason = (
        frontier_summary.get("frontier_exact1_stall_reason")
        or frontier_summary.get("frontier_converged_reason")
        or strata_summary.get("frontier_exact1_stall_reason")
        or strata_summary.get("frontier_converged_reason")
        or None
    )
    transform_classification = str(transform_trace_consistency.get("classification") or "").strip()
    if transform_classification:
        stage = "transform_consistency"
        reason = transform_classification
    dynamic_classification = str(dynamic_compare_path_probe.get("classification") or "").strip()
    if dynamic_classification:
        stage = "dynamic_compare_path_probe"
        reason = dynamic_classification
    pre_rc4_classification = str(pre_rc4_material_probe.get("classification") or "").strip()
    if pre_rc4_classification:
        stage = "pre_rc4_material_probe"
        reason = pre_rc4_classification
    static_discovery_classification = str(base64_rc4_static_point_discovery.get("classification") or "").strip()
    if static_discovery_classification:
        stage = "base64_rc4_static_point_discovery"
        reason = static_discovery_classification
    breakpoint_classification = str(base64_rc4_breakpoint_probe.get("classification") or "").strip()
    if breakpoint_classification:
        stage = "base64_rc4_breakpoint_probe"
        reason = breakpoint_classification
    compare_stack_classification = str(compare_stack_pivot_probe.get("classification") or "").strip()
    if compare_stack_classification:
        stage = "compare_stack_pivot_probe"
        reason = compare_stack_classification
    compare_handoff_classification = str(compare_handoff_probe.get("classification") or "").strip()
    if compare_handoff_classification:
        stage = "compare_handoff_probe"
        reason = compare_handoff_classification
    compare_handoff_slice_classification = str(compare_handoff_slice_probe.get("classification") or "").strip()
    if compare_handoff_slice_classification:
        stage = "compare_handoff_slice_probe"
        reason = compare_handoff_slice_classification
    compare_handoff_return_site_classification = str(
        compare_handoff_return_site_probe.get("classification") or ""
    ).strip()
    if compare_handoff_return_site_classification:
        stage = "compare_handoff_return_site_probe"
        reason = compare_handoff_return_site_classification
    compare_producer_trace_classification = str(compare_producer_trace_probe.get("classification") or "").strip()
    if compare_producer_trace_classification:
        stage = "compare_producer_trace_probe"
        reason = compare_producer_trace_classification
    material_confirmation_classification = str(
        compare_producer_material_confirmation.get("classification") or ""
    ).strip()
    if material_confirmation_classification:
        stage = "compare_producer_material_confirmation"
        reason = material_confirmation_classification
    pre_compare_handoff_classification = str(
        compare_pre_compare_handoff_target_probe.get("classification") or ""
    ).strip()
    if pre_compare_handoff_classification:
        stage = "compare_pre_compare_handoff_target_probe"
        reason = pre_compare_handoff_classification
    function_semantic_classification = str(function_semantic_audit.get("classification") or "").strip()
    if function_semantic_classification:
        stage = "function_semantic_audit"
        reason = function_semantic_classification
    material_hook_runtime_classification = str(
        material_hook_runtime_validation.get("classification") or ""
    ).strip()
    if material_hook_runtime_classification:
        stage = "material_hook_runtime_validation"
        reason = material_hook_runtime_classification
    post_handoff_classification = str(
        post_handoff_branch_outcome_audit.get("classification") or ""
    ).strip()
    if post_handoff_classification:
        stage = "post_handoff_branch_outcome_audit"
        reason = post_handoff_classification
    exception_unwind_classification = str(
        post_handoff_exception_unwind_audit.get("classification") or ""
    ).strip()
    if exception_unwind_classification:
        stage = "post_handoff_exception_unwind_audit"
        reason = exception_unwind_classification
    hook_path_reachability_classification = str(
        compare_hook_path_reachability_audit.get("classification") or ""
    ).strip()
    hook_path_reachability_blocker = str(
        compare_hook_path_reachability_audit.get("new_blocker")
        or hook_path_reachability_classification
    ).strip()
    if hook_path_reachability_classification:
        stage = "compare_hook_path_reachability_audit"
        reason = hook_path_reachability_blocker or hook_path_reachability_classification
    handoff_exit_classifier_classification = str(
        compare_handoff_exit_classifier_audit.get("classification")
        or compare_handoff_exit_classifier_audit.get("overall_classification")
        or ""
    ).strip()
    handoff_exit_classifier_blocker = str(
        compare_handoff_exit_classifier_audit.get("new_blocker")
        or handoff_exit_classifier_classification
    ).strip()
    if handoff_exit_classifier_classification:
        stage = "compare_handoff_exit_classifier_audit"
        reason = handoff_exit_classifier_blocker or handoff_exit_classifier_classification
    handoff_path_divergence_classification = str(
        compare_handoff_path_divergence_audit.get("classification")
        or compare_handoff_path_divergence_audit.get("overall_classification")
        or ""
    ).strip()
    if handoff_path_divergence_classification:
        stage = "compare_handoff_path_divergence_audit"
        reason = handoff_path_divergence_classification
    handoff_edge_operand_classification = str(
        compare_handoff_edge_operand_provenance_audit.get("classification")
        or compare_handoff_edge_operand_provenance_audit.get("overall_classification")
        or ""
    ).strip()
    if handoff_edge_operand_classification:
        stage = "compare_handoff_edge_operand_provenance_audit"
        reason = handoff_edge_operand_classification
    handoff_branch_operand_classification = str(
        compare_handoff_branch_operand_runtime_audit.get("classification")
        or compare_handoff_branch_operand_runtime_audit.get("overall_classification")
        or ""
    ).strip()
    if handoff_branch_operand_classification:
        stage = "compare_handoff_branch_operand_runtime_audit"
        reason = handoff_branch_operand_classification
    handoff_hook_surface_repair_classification = str(
        compare_handoff_hook_surface_repair_audit.get("classification")
        or compare_handoff_hook_surface_repair_audit.get("overall_classification")
        or ""
    ).strip()
    if handoff_hook_surface_repair_classification:
        stage = "compare_handoff_hook_surface_repair_audit"
        reason = handoff_hook_surface_repair_classification
    handoff_post_entry_step_classification = str(
        compare_handoff_post_entry_step_runtime_audit.get("classification")
        or compare_handoff_post_entry_step_runtime_audit.get("overall_classification")
        or ""
    ).strip()
    if handoff_post_entry_step_classification:
        stage = "compare_handoff_post_entry_step_runtime_audit"
        reason = handoff_post_entry_step_classification
    handoff_narrower_post_entry_breakpoint_classification = str(
        compare_handoff_narrower_post_entry_breakpoint_audit.get("classification")
        or compare_handoff_narrower_post_entry_breakpoint_audit.get("overall_classification")
        or ""
    ).strip()
    handoff_narrower_ui_trigger_diagnostics = (
        compare_handoff_narrower_post_entry_breakpoint_audit.get("ui_trigger_diagnostics")
    )
    handoff_narrower_ui_trigger_diagnostics = (
        handoff_narrower_ui_trigger_diagnostics
        if isinstance(handoff_narrower_ui_trigger_diagnostics, dict)
        else {}
    )
    handoff_narrower_ui_classification = str(
        handoff_narrower_ui_trigger_diagnostics.get("classification") or ""
    ).strip()
    handoff_narrower_window_discovery_diagnostics = (
        compare_handoff_narrower_post_entry_breakpoint_audit.get(
            "window_discovery_diagnostics"
        )
    )
    handoff_narrower_window_discovery_diagnostics = (
        handoff_narrower_window_discovery_diagnostics
        if isinstance(handoff_narrower_window_discovery_diagnostics, dict)
        else {}
    )
    handoff_narrower_window_classification = str(
        handoff_narrower_window_discovery_diagnostics.get("classification") or ""
    ).strip()
    if (
        handoff_narrower_post_entry_breakpoint_classification
        in {"window_discovery_timeout", "ui_trigger_timeout"}
        and handoff_narrower_window_classification
        and handoff_narrower_window_classification
        not in {"window_discovery_timeout", "ui_trigger_timeout"}
    ):
        handoff_narrower_post_entry_breakpoint_classification = (
            handoff_narrower_window_classification
        )
    if (
        handoff_narrower_post_entry_breakpoint_classification == "ui_trigger_timeout"
        and handoff_narrower_ui_classification
        and handoff_narrower_ui_classification != "ui_trigger_timeout"
    ):
        handoff_narrower_post_entry_breakpoint_classification = (
            handoff_narrower_ui_classification
        )
    if handoff_narrower_post_entry_breakpoint_classification:
        stage = "compare_handoff_narrower_post_entry_breakpoint_audit"
        reason = handoff_narrower_post_entry_breakpoint_classification
    compare_lhs_producer_classification = str(
        compare_lhs_producer_audit.get("classification") or ""
    ).strip()
    if compare_lhs_producer_classification:
        stage = "compare_lhs_producer_audit"
        reason = compare_lhs_producer_classification
    upstream_writer_classification = str(
        compare_lhs_upstream_writer_audit.get("classification") or ""
    ).strip()
    if upstream_writer_classification:
        stage = "compare_lhs_upstream_writer_audit"
        reason = upstream_writer_classification
    callsite_reanchor_classification = str(
        compare_callsite_reanchor_audit.get("classification") or ""
    ).strip()
    if callsite_reanchor_classification:
        stage = "compare_callsite_reanchor_and_lhs_provenance_audit"
        reason = callsite_reanchor_classification
    real_lhs_provenance_classification = str(
        compare_real_lhs_provenance_audit.get("classification") or ""
    ).strip()
    real_lhs_writer_blocker = _derive_real_lhs_writer_blocker(compare_real_lhs_provenance_audit)
    real_lhs_raw_write_gap_summary = _derive_raw_write_gap_summary(compare_real_lhs_provenance_audit)
    if real_lhs_provenance_classification:
        stage = "compare_real_lhs_provenance_audit"
        reason = real_lhs_provenance_classification
    esi_source_window_classification = str(
        compare_esi_source_window_audit.get("classification") or ""
    ).strip()
    if esi_source_window_classification:
        stage = "compare_esi_source_window_audit"
        reason = esi_source_window_classification
    slot_writer_source_classification = str(
        compare_lhs_slot_writer_source_audit.get("classification") or ""
    ).strip()
    if slot_writer_source_classification:
        stage = "compare_lhs_slot_writer_source_audit"
        reason = slot_writer_source_classification
    slot_writer_predecessor_classification = str(
        compare_lhs_slot_writer_predecessor_audit.get("classification") or ""
    ).strip()
    if slot_writer_predecessor_classification:
        stage = "compare_lhs_slot_writer_predecessor_audit"
        reason = slot_writer_predecessor_classification
    if hook_path_reachability_classification:
        stage = "compare_hook_path_reachability_audit"
        reason = hook_path_reachability_blocker or hook_path_reachability_classification
    if handoff_exit_classifier_classification:
        stage = "compare_handoff_exit_classifier_audit"
        reason = handoff_exit_classifier_blocker or handoff_exit_classifier_classification
    if handoff_path_divergence_classification:
        stage = "compare_handoff_path_divergence_audit"
        reason = handoff_path_divergence_classification
    if handoff_edge_operand_classification:
        stage = "compare_handoff_edge_operand_provenance_audit"
        reason = handoff_edge_operand_classification
    if handoff_branch_operand_classification:
        stage = "compare_handoff_branch_operand_runtime_audit"
        reason = handoff_branch_operand_classification
    if handoff_hook_surface_repair_classification:
        stage = "compare_handoff_hook_surface_repair_audit"
        reason = handoff_hook_surface_repair_classification
    if handoff_post_entry_step_classification:
        stage = "compare_handoff_post_entry_step_runtime_audit"
        reason = handoff_post_entry_step_classification
    if handoff_narrower_post_entry_breakpoint_classification:
        stage = "compare_handoff_narrower_post_entry_breakpoint_audit"
        reason = handoff_narrower_post_entry_breakpoint_classification
    if (
        pre_compare_handoff_classification
        and function_semantic_classification in {"runtime_instrumentation_required", "evidence_insufficient"}
    ):
        stage = "compare_pre_compare_handoff_target_probe"
        reason = pre_compare_handoff_classification
    if pre_rc4_classification and compare_producer_trace_classification in {
        "producer_trace_inconclusive",
        "needs_pre_rc4_base64_probe",
        "compare_only_capture",
        "manual_disassembly_required",
        "runtime_execution_failure",
    }:
        stage = "pre_rc4_material_probe"
        reason = pre_rc4_classification
    if static_discovery_classification and not compare_producer_trace_classification and not material_confirmation_classification and (
        not breakpoint_classification
        or breakpoint_classification
        in {
            "base64_rc4_static_points_unavailable",
            "base64_rc4_compare_only",
            "breakpoint_probe_partial",
        }
    ):
        stage = "base64_rc4_static_point_discovery"
        reason = static_discovery_classification
    if stage is None:
        uncertainty.append("current_bottleneck.stage")
    if reason is None:
        uncertainty.append("current_bottleneck.reason")

    if artifact_index.get("missing"):
        uncertainty.extend(f"missing:{item}" for item in artifact_index.get("missing", []))

    function_records = function_semantic_audit.get("functions", [])
    function_records = function_records if isinstance(function_records, list) else []
    function_semantics = {
        str(item.get("function")): {
            "semantic_guess": item.get("semantic_guess"),
            "confidence": item.get("confidence"),
            "candidate_dependent": item.get("candidate_dependent"),
            "hookable": item.get("hookable"),
            "instruction_confirmed": item.get("instruction_confirmed"),
            "material_hook_candidate_status": item.get("material_hook_candidate_status"),
            "evidence_artifact": artifact_refs.get("function_semantic_audit"),
        }
        for item in function_records[:8]
        if isinstance(item, dict) and item.get("function")
    }

    return {
        "sample": sample,
        "profile": sample if sample == "samplereverse" else None,
        "active_strategy": "CompareAwareSearchStrategy" if sample == "samplereverse" else None,
        "current_mainline": "L15(prefix8)" if sample == "samplereverse" else None,
        "known_transform": (
            ["input", "UTF-16LE", "Base64", "RC4", "compare flag{ prefix"]
            if sample == "samplereverse"
            else []
        ),
        "best_candidates": {
            "exact2": exact2,
            "exact1": exact1,
            "frontier": frontier,
        },
        "current_bottleneck": {
            "stage": stage,
            "reason": reason,
            "blocker": (
                real_lhs_writer_blocker
                if stage == "compare_real_lhs_provenance_audit"
                else hook_path_reachability_blocker
                if stage == "compare_hook_path_reachability_audit"
                else handoff_exit_classifier_blocker
                if stage == "compare_handoff_exit_classifier_audit"
                else handoff_path_divergence_classification
                if stage == "compare_handoff_path_divergence_audit"
                else handoff_edge_operand_classification
                if stage == "compare_handoff_edge_operand_provenance_audit"
                else handoff_branch_operand_classification
                if stage == "compare_handoff_branch_operand_runtime_audit"
                else handoff_post_entry_step_classification
                if stage == "compare_handoff_post_entry_step_runtime_audit"
                else ""
            ),
            "confidence": "medium" if stage or reason else "low",
        },
        "latest_transform_trace_consistency": {
            "classification": transform_classification or None,
            "artifact": artifact_refs.get("transform_trace_consistency"),
            "runtime_backed_count": transform_trace_consistency.get("runtime_backed_count"),
            "candidate_count": transform_trace_consistency.get("candidate_count"),
            "stop_reason": transform_trace_consistency.get("stop_reason"),
            "next_bounded_action": (
                transform_trace_consistency.get("decision", {}).get("next_bounded_action")
                if isinstance(transform_trace_consistency.get("decision"), dict)
                else None
            ),
        }
        if transform_trace_consistency
        else {},
        "latest_dynamic_compare_path_probe": {
            "classification": dynamic_classification or None,
            "artifact": artifact_refs.get("dynamic_compare_path_probe"),
            "runtime_backed_count": dynamic_compare_path_probe.get("runtime_backed_count"),
            "candidate_count": dynamic_compare_path_probe.get("candidate_count"),
            "probe_points": dynamic_compare_path_probe.get("probe_points"),
            "next_bounded_action": dynamic_compare_path_probe.get("next_bounded_action"),
        }
        if dynamic_compare_path_probe
        else {},
        "latest_pre_rc4_material_probe": {
            "classification": pre_rc4_classification or None,
            "artifact": artifact_refs.get("pre_rc4_material_probe"),
            "runtime_backed_count": pre_rc4_material_probe.get("runtime_backed_count"),
            "candidate_count": pre_rc4_material_probe.get("candidate_count"),
            "probe_points": pre_rc4_material_probe.get("probe_points"),
            "rc4_key_status": pre_rc4_material_probe.get("rc4_key_status"),
            "rc4_input_status": pre_rc4_material_probe.get("rc4_input_status"),
            "first_divergence_stage": pre_rc4_material_probe.get("first_divergence_stage"),
            "offline_runtime_agreement_table": pre_rc4_material_probe.get("offline_runtime_agreement_table"),
            "producer_material_relation_table": pre_rc4_material_probe.get("producer_material_relation_table"),
            "next_bounded_action": pre_rc4_material_probe.get("next_bounded_action"),
        }
        if pre_rc4_material_probe
        else {},
        "latest_base64_rc4_breakpoint_probe": {
            "classification": breakpoint_classification or None,
            "artifact": artifact_refs.get("base64_rc4_breakpoint_probe"),
            "runtime_backed_count": base64_rc4_breakpoint_probe.get("runtime_backed_count"),
            "candidate_count": base64_rc4_breakpoint_probe.get("candidate_count"),
            "hook_event_count": base64_rc4_breakpoint_probe.get("hook_event_count"),
            "static_point_summary": base64_rc4_breakpoint_probe.get("static_point_summary"),
            "hook_results": base64_rc4_breakpoint_probe.get("hook_results"),
            "first_captured_material_kind": base64_rc4_breakpoint_probe.get("first_captured_material_kind"),
            "next_bottleneck": base64_rc4_breakpoint_probe.get("next_bottleneck"),
            "next_bounded_action": base64_rc4_breakpoint_probe.get("next_bounded_action"),
        }
        if base64_rc4_breakpoint_probe
        else {},
        "latest_base64_rc4_static_point_discovery": {
            "classification": static_discovery_classification or None,
            "artifact": artifact_refs.get("base64_rc4_static_point_discovery"),
            "hookable_count": base64_rc4_static_point_discovery.get("hookable_count"),
            "instruction_confirmed_count": base64_rc4_static_point_discovery.get("instruction_confirmed_count"),
            "by_kind": base64_rc4_static_point_discovery.get("by_kind"),
            "best_points": base64_rc4_static_point_discovery.get("best_points"),
            "breakpoint_probe_allowed": base64_rc4_static_point_discovery.get("breakpoint_probe_allowed"),
            "next_bounded_action": base64_rc4_static_point_discovery.get("next_bounded_action"),
        }
        if base64_rc4_static_point_discovery
        else {},
        "latest_static_point_discovery": {
            "classification": static_discovery_classification or None,
            "artifact": artifact_refs.get("base64_rc4_static_point_discovery"),
            "hookable_count": base64_rc4_static_point_discovery.get("hookable_count"),
            "instruction_confirmed_count": base64_rc4_static_point_discovery.get("instruction_confirmed_count"),
            "by_kind": base64_rc4_static_point_discovery.get("by_kind"),
            "best_points": base64_rc4_static_point_discovery.get("best_points"),
            "breakpoint_probe_allowed": base64_rc4_static_point_discovery.get("breakpoint_probe_allowed"),
            "next_bounded_action": base64_rc4_static_point_discovery.get("next_bounded_action"),
        }
        if base64_rc4_static_point_discovery
        else {},
        "latest_compare_stack_pivot_probe": {
            "classification": compare_stack_classification or None,
            "artifact": artifact_refs.get("compare_stack_pivot_probe"),
            "runtime_backed_count": compare_stack_pivot_probe.get("runtime_backed_count"),
            "candidate_count": compare_stack_pivot_probe.get("candidate_count"),
            "utf16le_payload_available_count": compare_stack_pivot_probe.get("utf16le_payload_available_count"),
            "hook_results": compare_stack_pivot_probe.get("hook_results"),
            "static_audit": compare_stack_pivot_probe.get("static_audit"),
            "next_hook_points": compare_stack_pivot_probe.get("next_hook_points"),
            "next_bounded_action": compare_stack_pivot_probe.get("next_bounded_action"),
        }
        if compare_stack_pivot_probe
        else {},
        "latest_compare_handoff_probe": {
            "classification": compare_handoff_classification or None,
            "artifact": artifact_refs.get("compare_handoff_probe"),
            "runtime_backed_count": compare_handoff_probe.get("runtime_backed_count"),
            "candidate_count": compare_handoff_probe.get("candidate_count"),
            "hook_results": compare_handoff_probe.get("hook_results"),
            "compare_stack_pivot_audit": compare_handoff_probe.get("compare_stack_pivot_audit"),
            "next_bounded_action": compare_handoff_probe.get("next_bounded_action"),
        }
        if compare_handoff_probe
        else {},
        "latest_compare_handoff_slice_probe": {
            "classification": compare_handoff_slice_classification or None,
            "artifact": artifact_refs.get("compare_handoff_slice_probe"),
            "runtime_backed_count": compare_handoff_slice_probe.get("runtime_backed_count"),
            "candidate_count": compare_handoff_slice_probe.get("candidate_count"),
            "hook_results": compare_handoff_slice_probe.get("hook_results"),
            "static_audit": compare_handoff_slice_probe.get("static_audit"),
            "cross_candidate_summary": compare_handoff_slice_probe.get("cross_candidate_summary"),
            "next_bounded_action": compare_handoff_slice_probe.get("next_bounded_action"),
        }
        if compare_handoff_slice_probe
        else {},
        "latest_compare_handoff_return_site_probe": {
            "classification": compare_handoff_return_site_classification or None,
            "artifact": artifact_refs.get("compare_handoff_return_site_probe"),
            "runtime_backed_count": compare_handoff_return_site_probe.get("runtime_backed_count"),
            "candidate_count": compare_handoff_return_site_probe.get("candidate_count"),
            "hit_0x2338_count": compare_handoff_return_site_probe.get("hit_0x2338_count"),
            "hit_0x233d_count": compare_handoff_return_site_probe.get("hit_0x233d_count"),
            "hit_0x234e_count": compare_handoff_return_site_probe.get("hit_0x234e_count"),
            "hit_0x2355_count": compare_handoff_return_site_probe.get("hit_0x2355_count"),
            "call_0x401b50_entered_count": compare_handoff_return_site_probe.get("call_0x401b50_entered_count"),
            "call_0x401b50_returned_count": compare_handoff_return_site_probe.get("call_0x401b50_returned_count"),
            "hook_results": compare_handoff_return_site_probe.get("hook_results"),
            "static_audit": compare_handoff_return_site_probe.get("static_audit"),
            "cross_candidate_summary": compare_handoff_return_site_probe.get("cross_candidate_summary"),
            "next_bounded_action": compare_handoff_return_site_probe.get("next_bounded_action"),
        }
        if compare_handoff_return_site_probe
        else {},
        "latest_compare_producer_trace_probe": {
            "classification": compare_producer_trace_classification or None,
            "artifact": artifact_refs.get("compare_producer_trace_probe"),
            "runtime_backed_count": compare_producer_trace_probe.get("runtime_backed_count"),
            "candidate_count": compare_producer_trace_probe.get("candidate_count"),
            "candidate_material_count": compare_producer_trace_probe.get("candidate_material_count"),
            "best_material_candidates": compare_producer_trace_probe.get("candidate_materials", [])[:8]
            if isinstance(compare_producer_trace_probe.get("candidate_materials"), list)
            else [],
            "write_source_trace_count": compare_producer_trace_probe.get("write_source_trace_count"),
            "write_source_trace": compare_producer_trace_probe.get("write_source_trace", [])[:8]
            if isinstance(compare_producer_trace_probe.get("write_source_trace"), list)
            else [],
            "material_hook_candidate_count": compare_producer_trace_probe.get("material_hook_candidate_count"),
            "material_hook_candidates": compare_producer_trace_probe.get("material_hook_candidates", [])[:8]
            if isinstance(compare_producer_trace_probe.get("material_hook_candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_producer_trace_probe.get("breakpoint_probe_allowed"),
            "hook_results": compare_producer_trace_probe.get("hook_results"),
            "hook_miss_classification": compare_producer_trace_probe.get("hook_miss_classification"),
            "static_audit": compare_producer_trace_probe.get("static_audit"),
            "cross_candidate_summary": compare_producer_trace_probe.get("cross_candidate_summary"),
            "next_bounded_action": compare_producer_trace_probe.get("next_bounded_action"),
        }
        if compare_producer_trace_probe
        else {},
        "latest_compare_producer_material_confirmation": {
            "classification": material_confirmation_classification or None,
            "artifact": artifact_refs.get("compare_producer_material_confirmation"),
            "runtime_backed_count": compare_producer_material_confirmation.get("runtime_backed_count"),
            "candidate_count": compare_producer_material_confirmation.get("candidate_count"),
            "instruction_confirmation_table": compare_producer_material_confirmation.get(
                "instruction_confirmation_table", []
            )[:10]
            if isinstance(compare_producer_material_confirmation.get("instruction_confirmation_table"), list)
            else [],
            "material_source_trace": compare_producer_material_confirmation.get("material_source_trace", [])[:8]
            if isinstance(compare_producer_material_confirmation.get("material_source_trace"), list)
            else [],
            "confirmed_material_hook_candidate_count": compare_producer_material_confirmation.get(
                "confirmed_material_hook_candidate_count"
            ),
            "confirmed_material_hook_candidates": compare_producer_material_confirmation.get(
                "confirmed_material_hook_candidates", []
            )[:8]
            if isinstance(compare_producer_material_confirmation.get("confirmed_material_hook_candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_producer_material_confirmation.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_producer_material_confirmation.get("next_bounded_action"),
        }
        if compare_producer_material_confirmation
        else {},
        "latest_compare_pre_compare_handoff_target_probe": {
            "classification": pre_compare_handoff_classification or None,
            "artifact": artifact_refs.get("compare_pre_compare_handoff_target_probe"),
            "runtime_backed_count": compare_pre_compare_handoff_target_probe.get("runtime_backed_count"),
            "candidate_count": compare_pre_compare_handoff_target_probe.get("candidate_count"),
            "hit_summary": compare_pre_compare_handoff_target_probe.get("hit_summary"),
            "hook_miss_classification": compare_pre_compare_handoff_target_probe.get(
                "hook_miss_classification"
            ),
            "candidate_dependent_fields": compare_pre_compare_handoff_target_probe.get(
                "candidate_dependent_fields"
            ),
            "relation_counts": compare_pre_compare_handoff_target_probe.get("relation_counts"),
            "relation_table": compare_pre_compare_handoff_target_probe.get("relation_table", [])[:4]
            if isinstance(compare_pre_compare_handoff_target_probe.get("relation_table"), list)
            else [],
            "material_hook_candidate_count": compare_pre_compare_handoff_target_probe.get(
                "material_hook_candidate_count"
            ),
            "material_hook_candidates": compare_pre_compare_handoff_target_probe.get(
                "material_hook_candidates", []
            )[:8]
            if isinstance(compare_pre_compare_handoff_target_probe.get("material_hook_candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_pre_compare_handoff_target_probe.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_pre_compare_handoff_target_probe.get("next_bounded_action"),
        }
        if compare_pre_compare_handoff_target_probe
        else {},
        "latest_function_semantic_audit": {
            "classification": function_semantic_classification or None,
            "artifact": artifact_refs.get("function_semantic_audit"),
            "function_count": function_semantic_audit.get("function_count"),
            "material_hook_candidate_count": function_semantic_audit.get("material_hook_candidate_count"),
            "breakpoint_probe_allowed": function_semantic_audit.get("breakpoint_probe_allowed"),
            "top_semantic_guesses": function_semantic_audit.get("top_semantic_guesses", [])[:8]
            if isinstance(function_semantic_audit.get("top_semantic_guesses"), list)
            else [],
            "next_bounded_action": function_semantic_audit.get("next_bounded_action"),
        }
        if function_semantic_audit
        else {},
        "latest_material_hook_runtime_validation": {
            "classification": material_hook_runtime_classification or None,
            "artifact": artifact_refs.get("material_hook_runtime_validation"),
            "runtime_backed_count": material_hook_runtime_validation.get("runtime_backed_count"),
            "candidate_count": material_hook_runtime_validation.get("candidate_count"),
            "source_compare_esi_source_window_classification": material_hook_runtime_validation.get(
                "source_compare_esi_source_window_classification"
            ),
            "material_kind": material_hook_runtime_validation.get("material_kind"),
            "validated_hook_count": len(material_hook_runtime_validation.get("validated_hooks", []))
            if isinstance(material_hook_runtime_validation.get("validated_hooks"), list)
            else 0,
            "blocked_hook_count": len(material_hook_runtime_validation.get("blocked_hooks", []))
            if isinstance(material_hook_runtime_validation.get("blocked_hooks"), list)
            else 0,
            "validated_hooks": material_hook_runtime_validation.get("validated_hooks", [])[:4]
            if isinstance(material_hook_runtime_validation.get("validated_hooks"), list)
            else [],
            "blocked_hooks": material_hook_runtime_validation.get("blocked_hooks", [])[:4]
            if isinstance(material_hook_runtime_validation.get("blocked_hooks"), list)
            else [],
            "breakpoint_probe_allowed": material_hook_runtime_validation.get("breakpoint_probe_allowed"),
            "next_bounded_action": material_hook_runtime_validation.get("next_bounded_action"),
        }
        if material_hook_runtime_validation
        else {},
        "latest_post_handoff_branch_outcome_audit": {
            "classification": post_handoff_classification or None,
            "artifact": artifact_refs.get("post_handoff_branch_outcome_audit"),
            "source_pre_compare_handoff_classification": post_handoff_branch_outcome_audit.get(
                "source_pre_compare_handoff_classification"
            ),
            "source_pre_compare_handoff_hook_miss_classification": post_handoff_branch_outcome_audit.get(
                "source_pre_compare_handoff_hook_miss_classification"
            ),
            "source_material_hook_runtime_classification": post_handoff_branch_outcome_audit.get(
                "source_material_hook_runtime_classification"
            ),
            "source_predecessor_classification": post_handoff_branch_outcome_audit.get(
                "source_predecessor_classification"
            ),
            "candidate_count": post_handoff_branch_outcome_audit.get("candidate_count"),
            "runtime_backed_count": post_handoff_branch_outcome_audit.get("runtime_backed_count"),
            "actual_compare": post_handoff_branch_outcome_audit.get("actual_compare", {}),
            "path_observed_counts": post_handoff_branch_outcome_audit.get("path_observed_counts", {}),
            "exit_summary": post_handoff_branch_outcome_audit.get("exit_summary", {}),
            "failed_material_hook_hypotheses": post_handoff_branch_outcome_audit.get(
                "failed_material_hook_hypotheses", []
            )[:4]
            if isinstance(post_handoff_branch_outcome_audit.get("failed_material_hook_hypotheses"), list)
            else [],
            "downstream_transform_calls_reached": post_handoff_branch_outcome_audit.get(
                "window", {}
            ).get("downstream_transform_calls_reached")
            if isinstance(post_handoff_branch_outcome_audit.get("window"), dict)
            else None,
            "breakpoint_probe_allowed": post_handoff_branch_outcome_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": post_handoff_branch_outcome_audit.get("next_bounded_action"),
        }
        if post_handoff_branch_outcome_audit
        else {},
        "latest_post_handoff_exception_unwind_audit": {
            "classification": exception_unwind_classification or None,
            "artifact": artifact_refs.get("post_handoff_exception_unwind_audit"),
            "source_post_handoff_branch_outcome_classification": post_handoff_exception_unwind_audit.get(
                "source_post_handoff_branch_outcome_classification"
            ),
            "candidate_count": post_handoff_exception_unwind_audit.get("candidate_count"),
            "runtime_backed_count": post_handoff_exception_unwind_audit.get("runtime_backed_count"),
            "evidence_gate": post_handoff_exception_unwind_audit.get("evidence_gate", {}),
            "actual_compare": post_handoff_exception_unwind_audit.get("actual_compare", {}),
            "exception_path": post_handoff_exception_unwind_audit.get("exception_path", {}),
            "tentative_hook_candidates": post_handoff_exception_unwind_audit.get(
                "tentative_hook_candidates", []
            )[:8]
            if isinstance(post_handoff_exception_unwind_audit.get("tentative_hook_candidates"), list)
            else [],
            "post_classification_route": post_handoff_exception_unwind_audit.get(
                "post_classification_route"
            ),
            "breakpoint_probe_allowed": post_handoff_exception_unwind_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": post_handoff_exception_unwind_audit.get("next_bounded_action"),
        }
        if post_handoff_exception_unwind_audit
        else {},
        "latest_compare_hook_path_reachability_audit": {
            "classification": hook_path_reachability_classification or None,
            "new_blocker": hook_path_reachability_blocker or None,
            "artifact": artifact_refs.get("compare_hook_path_reachability_audit"),
            "candidate_count": compare_hook_path_reachability_audit.get("candidate_count"),
            "runtime_backed_count": compare_hook_path_reachability_audit.get("runtime_backed_count"),
            "fixed_candidates": compare_hook_path_reachability_audit.get("fixed_candidates", []),
            "hook_points": compare_hook_path_reachability_audit.get("hook_points", [])[:8]
            if isinstance(compare_hook_path_reachability_audit.get("hook_points"), list)
            else [],
            "hook_address_validation": compare_hook_path_reachability_audit.get(
                "hook_address_validation", {}
            ),
            "path_observed_counts": compare_hook_path_reachability_audit.get(
                "path_observed_counts", {}
            ),
            "actual_compare": compare_hook_path_reachability_audit.get("actual_compare", {}),
            "candidate_execution_health": compare_hook_path_reachability_audit.get(
                "candidate_execution_health", []
            )[:3]
            if isinstance(compare_hook_path_reachability_audit.get("candidate_execution_health"), list)
            else [],
            "breakpoint_probe_allowed": compare_hook_path_reachability_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_hook_path_reachability_audit.get("next_bounded_action"),
        }
        if compare_hook_path_reachability_audit
        else {},
        "latest_compare_handoff_exit_classifier_audit": {
            "classification": handoff_exit_classifier_classification or None,
            "overall_classification": compare_handoff_exit_classifier_audit.get(
                "overall_classification"
            ),
            "new_blocker": handoff_exit_classifier_blocker or None,
            "artifact": artifact_refs.get("compare_handoff_exit_classifier_audit"),
            "source_run": compare_handoff_exit_classifier_audit.get("source_run"),
            "candidate_count": compare_handoff_exit_classifier_audit.get("candidate_count"),
            "runtime_backed_count": compare_handoff_exit_classifier_audit.get("runtime_backed_count"),
            "fixed_candidates": compare_handoff_exit_classifier_audit.get("fixed_candidates", []),
            "candidates": compare_handoff_exit_classifier_audit.get("candidates", [])[:3]
            if isinstance(compare_handoff_exit_classifier_audit.get("candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_handoff_exit_classifier_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_exit_classifier_audit.get("next_bounded_action"),
        }
        if compare_handoff_exit_classifier_audit
        else {},
        "latest_compare_handoff_path_divergence_audit": {
            "classification": handoff_path_divergence_classification or None,
            "overall_classification": compare_handoff_path_divergence_audit.get(
                "overall_classification"
            ),
            "artifact": artifact_refs.get("compare_handoff_path_divergence_audit"),
            "source_run": compare_handoff_path_divergence_audit.get("source_run"),
            "source_artifact": compare_handoff_path_divergence_audit.get("source_artifact"),
            "candidate_count": compare_handoff_path_divergence_audit.get("candidate_count"),
            "runtime_backed_count": compare_handoff_path_divergence_audit.get("runtime_backed_count"),
            "cross_candidate": compare_handoff_path_divergence_audit.get("cross_candidate", {}),
            "candidates": compare_handoff_path_divergence_audit.get("candidates", [])[:3]
            if isinstance(compare_handoff_path_divergence_audit.get("candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_handoff_path_divergence_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_path_divergence_audit.get("next_bounded_action"),
        }
        if compare_handoff_path_divergence_audit
        else {},
        "latest_compare_handoff_edge_operand_provenance_audit": {
            "classification": handoff_edge_operand_classification or None,
            "overall_classification": compare_handoff_edge_operand_provenance_audit.get(
                "overall_classification"
            ),
            "artifact": artifact_refs.get("compare_handoff_edge_operand_provenance_audit"),
            "source_run": compare_handoff_edge_operand_provenance_audit.get("source_run"),
            "source_artifacts": compare_handoff_edge_operand_provenance_audit.get(
                "source_artifacts",
                [],
            ),
            "candidate_count": compare_handoff_edge_operand_provenance_audit.get("candidate_count"),
            "runtime_backed_count": compare_handoff_edge_operand_provenance_audit.get(
                "runtime_backed_count"
            ),
            "cross_candidate": compare_handoff_edge_operand_provenance_audit.get(
                "cross_candidate",
                {},
            ),
            "candidates": compare_handoff_edge_operand_provenance_audit.get("candidates", [])[:3]
            if isinstance(compare_handoff_edge_operand_provenance_audit.get("candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_handoff_edge_operand_provenance_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_edge_operand_provenance_audit.get(
                "next_bounded_action"
            ),
        }
        if compare_handoff_edge_operand_provenance_audit
        else {},
        "latest_compare_handoff_branch_operand_runtime_audit": {
            "classification": handoff_branch_operand_classification or None,
            "overall_classification": compare_handoff_branch_operand_runtime_audit.get(
                "overall_classification"
            ),
            "artifact": artifact_refs.get("compare_handoff_branch_operand_runtime_audit"),
            "source_run": compare_handoff_branch_operand_runtime_audit.get("source_run"),
            "source_artifacts": compare_handoff_branch_operand_runtime_audit.get(
                "source_artifacts",
                [],
            ),
            "candidate_count": compare_handoff_branch_operand_runtime_audit.get("candidate_count"),
            "runtime_backed_count": compare_handoff_branch_operand_runtime_audit.get(
                "runtime_backed_count"
            ),
            "cross_candidate": compare_handoff_branch_operand_runtime_audit.get(
                "cross_candidate",
                {},
            ),
            "candidates": compare_handoff_branch_operand_runtime_audit.get("candidates", [])[:3]
            if isinstance(compare_handoff_branch_operand_runtime_audit.get("candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_handoff_branch_operand_runtime_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_branch_operand_runtime_audit.get(
                "next_bounded_action"
            ),
        }
        if compare_handoff_branch_operand_runtime_audit
        else {},
        "latest_compare_handoff_hook_surface_repair_audit": {
            "classification": handoff_hook_surface_repair_classification or None,
            "overall_classification": compare_handoff_hook_surface_repair_audit.get(
                "overall_classification"
            ),
            "artifact": artifact_refs.get("compare_handoff_hook_surface_repair_audit"),
            "source_run": compare_handoff_hook_surface_repair_audit.get("source_run"),
            "source_artifacts": compare_handoff_hook_surface_repair_audit.get(
                "source_artifacts",
                [],
            ),
            "candidate_count": compare_handoff_hook_surface_repair_audit.get("candidate_count"),
            "runtime_backed_count": compare_handoff_hook_surface_repair_audit.get(
                "runtime_backed_count"
            ),
            "hook_surface_repair": compare_handoff_hook_surface_repair_audit.get(
                "hook_surface_repair",
                {},
            ),
            "hook_surface_coverage": compare_handoff_hook_surface_repair_audit.get(
                "hook_surface_coverage",
                {},
            ),
            "cross_candidate": compare_handoff_hook_surface_repair_audit.get(
                "cross_candidate",
                {},
            ),
            "candidates": compare_handoff_hook_surface_repair_audit.get("candidates", [])[:3]
            if isinstance(compare_handoff_hook_surface_repair_audit.get("candidates"), list)
            else [],
            "breakpoint_probe_allowed": compare_handoff_hook_surface_repair_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_hook_surface_repair_audit.get(
                "next_bounded_action"
            ),
        }
        if compare_handoff_hook_surface_repair_audit
        else {},
        "latest_compare_handoff_post_entry_step_runtime_audit": {
            "classification": handoff_post_entry_step_classification or None,
            "overall_classification": compare_handoff_post_entry_step_runtime_audit.get(
                "overall_classification"
            ),
            "artifact": artifact_refs.get("compare_handoff_post_entry_step_runtime_audit"),
            "source_run": compare_handoff_post_entry_step_runtime_audit.get("source_run"),
            "source_artifacts": compare_handoff_post_entry_step_runtime_audit.get(
                "source_artifacts",
                [],
            ),
            "candidate_count": compare_handoff_post_entry_step_runtime_audit.get(
                "candidate_count"
            ),
            "runtime_sidecar_executed": compare_handoff_post_entry_step_runtime_audit.get(
                "runtime_sidecar_executed"
            ),
            "runtime_scope": compare_handoff_post_entry_step_runtime_audit.get(
                "runtime_scope",
                {},
            ),
            "diagnostic_summary": compare_handoff_post_entry_step_runtime_audit.get(
                "diagnostic_summary",
                {},
            ),
            "environment_diagnostics": compare_handoff_post_entry_step_runtime_audit.get(
                "environment_diagnostics",
                {},
            ),
            "breakpoint_installation_diagnostics": (
                compare_handoff_post_entry_step_runtime_audit.get(
                    "breakpoint_installation_diagnostics",
                    {},
                )
            ),
            "single_step_diagnostics": compare_handoff_post_entry_step_runtime_audit.get(
                "single_step_diagnostics",
                {},
            ),
            "artifact_parse_diagnostics": compare_handoff_post_entry_step_runtime_audit.get(
                "artifact_parse_diagnostics",
                {},
            ),
            "cross_candidate": compare_handoff_post_entry_step_runtime_audit.get(
                "cross_candidate",
                {},
            ),
            "candidates": compare_handoff_post_entry_step_runtime_audit.get("candidates", [])[:3]
            if isinstance(
                compare_handoff_post_entry_step_runtime_audit.get("candidates"), list
            )
            else [],
            "breakpoint_probe_allowed": compare_handoff_post_entry_step_runtime_audit.get(
                "breakpoint_probe_allowed"
            ),
            "next_bounded_action": compare_handoff_post_entry_step_runtime_audit.get(
                "next_bounded_action"
            ),
        }
        if compare_handoff_post_entry_step_runtime_audit
        else {},
        "latest_compare_handoff_narrower_post_entry_breakpoint_audit": {
            "classification": handoff_narrower_post_entry_breakpoint_classification or None,
            "overall_classification": (
                compare_handoff_narrower_post_entry_breakpoint_audit.get(
                    "overall_classification"
                )
            ),
            "artifact": artifact_refs.get(
                "compare_handoff_narrower_post_entry_breakpoint_audit"
            ),
            "source_run": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "source_run"
            ),
            "source_artifacts": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "source_artifacts",
                [],
            ),
            "candidate_count": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "candidate_count"
            ),
            "fixed_candidates": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "fixed_candidates",
                [],
            ),
            "runtime_scope": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "runtime_scope",
                {},
            ),
            "breakpoint_plan": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "breakpoint_plan",
                [],
            ),
            "diagnostic_summary": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "diagnostic_summary",
                {},
            ),
            "lifecycle_schema_version": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "lifecycle_schema_version"
            ),
            "lifecycle_diagnostics": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "lifecycle_diagnostics",
                {},
            ),
            "ui_trigger_schema_version": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "ui_trigger_schema_version"
            ),
            "ui_trigger_diagnostics": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "ui_trigger_diagnostics",
                {},
            ),
            "window_discovery_schema_version": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "window_discovery_schema_version"
            ),
            "window_discovery_diagnostics": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "window_discovery_diagnostics",
                {},
            ),
            "cross_candidate": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "cross_candidate",
                {},
            ),
            "candidates": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "candidates",
                [],
            )[:3]
            if isinstance(
                compare_handoff_narrower_post_entry_breakpoint_audit.get("candidates"),
                list,
            )
            else [],
            "breakpoint_probe_allowed": (
                compare_handoff_narrower_post_entry_breakpoint_audit.get(
                    "breakpoint_probe_allowed"
                )
            ),
            "next_bounded_action": compare_handoff_narrower_post_entry_breakpoint_audit.get(
                "next_bounded_action"
            ),
        }
        if compare_handoff_narrower_post_entry_breakpoint_audit
        else {},
        "latest_compare_lhs_producer_audit": {
            "classification": compare_lhs_producer_classification or None,
            "artifact": artifact_refs.get("compare_lhs_producer_audit"),
            "candidate_count": compare_lhs_producer_audit.get("candidate_count"),
            "runtime_backed_count": compare_lhs_producer_audit.get("runtime_backed_count"),
            "relations": compare_lhs_producer_audit.get("relations", {}),
            "checked_windows": compare_lhs_producer_audit.get("checked_windows", [])[:5]
            if isinstance(compare_lhs_producer_audit.get("checked_windows"), list)
            else [],
            "identified_producers": compare_lhs_producer_audit.get("identified_producers", [])[:3]
            if isinstance(compare_lhs_producer_audit.get("identified_producers"), list)
            else [],
            "breakpoint_probe_allowed": compare_lhs_producer_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_lhs_producer_audit.get("next_bounded_action"),
        }
        if compare_lhs_producer_audit
        else {},
        "latest_compare_lhs_upstream_writer_audit": {
            "classification": upstream_writer_classification or None,
            "artifact": artifact_refs.get("compare_lhs_upstream_writer_audit"),
            "candidate_count": compare_lhs_upstream_writer_audit.get("candidate_count"),
            "runtime_backed_count": compare_lhs_upstream_writer_audit.get("runtime_backed_count"),
            "relations": compare_lhs_upstream_writer_audit.get("relations", {}),
            "checked_writers": compare_lhs_upstream_writer_audit.get("checked_writers", [])[:6]
            if isinstance(compare_lhs_upstream_writer_audit.get("checked_writers"), list)
            else [],
            "identified_writers": compare_lhs_upstream_writer_audit.get("identified_writers", [])[:3]
            if isinstance(compare_lhs_upstream_writer_audit.get("identified_writers"), list)
            else [],
            "candidate_dependent_writers": compare_lhs_upstream_writer_audit.get(
                "candidate_dependent_writers", []
            )[:3]
            if isinstance(compare_lhs_upstream_writer_audit.get("candidate_dependent_writers"), list)
            else [],
            "breakpoint_probe_allowed": compare_lhs_upstream_writer_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_lhs_upstream_writer_audit.get("next_bounded_action"),
        }
        if compare_lhs_upstream_writer_audit
        else {},
        "latest_compare_callsite_reanchor_and_lhs_provenance_audit": {
            "classification": callsite_reanchor_classification or None,
            "artifact": artifact_refs.get("compare_callsite_reanchor_and_lhs_provenance_audit"),
            "candidate_count": compare_callsite_reanchor_audit.get("candidate_count"),
            "runtime_backed_count": compare_callsite_reanchor_audit.get("runtime_backed_count"),
            "actual_compare": compare_callsite_reanchor_audit.get("actual_compare", {}),
            "frame_anchor": compare_callsite_reanchor_audit.get("frame_anchor", {}),
            "provenance": {
                **(
                    compare_callsite_reanchor_audit.get("provenance", {})
                    if isinstance(compare_callsite_reanchor_audit.get("provenance"), dict)
                    else {}
                ),
                "evidence": (
                    compare_callsite_reanchor_audit.get("provenance", {}).get("evidence", [])[:6]
                    if isinstance(compare_callsite_reanchor_audit.get("provenance"), dict)
                    and isinstance(compare_callsite_reanchor_audit.get("provenance", {}).get("evidence"), list)
                    else []
                ),
            },
            "relation_table": compare_callsite_reanchor_audit.get("relation_table", [])[:8]
            if isinstance(compare_callsite_reanchor_audit.get("relation_table"), list)
            else [],
            "identified_producers": compare_callsite_reanchor_audit.get("identified_producers", [])[:3]
            if isinstance(compare_callsite_reanchor_audit.get("identified_producers"), list)
            else [],
            "breakpoint_probe_allowed": compare_callsite_reanchor_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_callsite_reanchor_audit.get("next_bounded_action"),
        }
        if compare_callsite_reanchor_audit
        else {},
        "latest_compare_real_lhs_provenance_audit": {
            "classification": real_lhs_provenance_classification or None,
            "artifact": artifact_refs.get("compare_real_lhs_provenance_audit"),
            "candidate_count": compare_real_lhs_provenance_audit.get("candidate_count"),
            "runtime_backed_count": compare_real_lhs_provenance_audit.get("runtime_backed_count"),
            "actual_compare": compare_real_lhs_provenance_audit.get("actual_compare", {}),
            "frame_anchor": compare_real_lhs_provenance_audit.get("frame_anchor", {}),
            "relations": compare_real_lhs_provenance_audit.get("relations", {}),
            "provenance": {
                **(
                    compare_real_lhs_provenance_audit.get("provenance", {})
                    if isinstance(compare_real_lhs_provenance_audit.get("provenance"), dict)
                    else {}
                ),
                "evidence": (
                    compare_real_lhs_provenance_audit.get("provenance", {}).get("evidence", [])[:7]
                    if isinstance(compare_real_lhs_provenance_audit.get("provenance"), dict)
                    and isinstance(compare_real_lhs_provenance_audit.get("provenance", {}).get("evidence"), list)
                    else []
                ),
            },
            "relation_table": compare_real_lhs_provenance_audit.get("relation_table", [])[:8]
            if isinstance(compare_real_lhs_provenance_audit.get("relation_table"), list)
            else [],
            "last_writer_summary": compare_real_lhs_provenance_audit.get("last_writer_summary", {}),
            "raw_write_gap_summary": real_lhs_raw_write_gap_summary,
            "arg0_pointer_origin_trace": _derive_arg0_pointer_origin_trace(compare_real_lhs_provenance_audit),
            "arg0_final_data_writer_trace": _derive_arg0_final_data_writer_trace(
                compare_real_lhs_provenance_audit
            ),
            "sidecar_observation_blocker": _derive_sidecar_observation_blocker(
                compare_real_lhs_provenance_audit
            ),
            "write_monitor_health": compare_real_lhs_provenance_audit.get("write_monitor_health", {}),
            "lhs_writer_classification_blocker": real_lhs_writer_blocker,
            "last_writer_candidates": compare_real_lhs_provenance_audit.get("last_writer_candidates", [])[:3]
            if isinstance(compare_real_lhs_provenance_audit.get("last_writer_candidates"), list)
            else [],
            "identified_producers": compare_real_lhs_provenance_audit.get("identified_producers", [])[:3]
            if isinstance(compare_real_lhs_provenance_audit.get("identified_producers"), list)
            else [],
            "next_producer_window": compare_real_lhs_provenance_audit.get("next_producer_window", {}),
            "breakpoint_probe_allowed": compare_real_lhs_provenance_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_real_lhs_provenance_audit.get("next_bounded_action"),
        }
        if compare_real_lhs_provenance_audit
        else {},
        "latest_compare_esi_source_window_audit": {
            "classification": esi_source_window_classification or None,
            "artifact": artifact_refs.get("compare_esi_source_window_audit"),
            "candidate_count": compare_esi_source_window_audit.get("candidate_count"),
            "runtime_backed_count": compare_esi_source_window_audit.get("runtime_backed_count"),
            "actual_compare": compare_esi_source_window_audit.get("actual_compare", {}),
            "relations": compare_esi_source_window_audit.get("relations", {}),
            "window_rows": compare_esi_source_window_audit.get("window_rows", [])[:12]
            if isinstance(compare_esi_source_window_audit.get("window_rows"), list)
            else [],
            "relation_table": compare_esi_source_window_audit.get("relation_table", [])[:8]
            if isinstance(compare_esi_source_window_audit.get("relation_table"), list)
            else [],
            "identified_producers": compare_esi_source_window_audit.get("identified_producers", [])[:3]
            if isinstance(compare_esi_source_window_audit.get("identified_producers"), list)
            else [],
            "branch_summary": compare_esi_source_window_audit.get("branch_summary", {}),
            "next_producer_window": compare_esi_source_window_audit.get("next_producer_window", {}),
            "breakpoint_probe_allowed": compare_esi_source_window_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_esi_source_window_audit.get("next_bounded_action"),
        }
        if compare_esi_source_window_audit
        else {},
        "latest_compare_lhs_slot_writer_source_audit": {
            "classification": slot_writer_source_classification or None,
            "artifact": artifact_refs.get("compare_lhs_slot_writer_source_audit"),
            "candidate_count": compare_lhs_slot_writer_source_audit.get("candidate_count"),
            "runtime_backed_count": compare_lhs_slot_writer_source_audit.get("runtime_backed_count"),
            "actual_compare": compare_lhs_slot_writer_source_audit.get("actual_compare", {}),
            "relations": compare_lhs_slot_writer_source_audit.get("relations", {}),
            "slot_writer": compare_lhs_slot_writer_source_audit.get("slot_writer", {}),
            "eax_source": compare_lhs_slot_writer_source_audit.get("eax_source", {}),
            "writer_rows": compare_lhs_slot_writer_source_audit.get("writer_rows", [])[:8]
            if isinstance(compare_lhs_slot_writer_source_audit.get("writer_rows"), list)
            else [],
            "identified_writers": compare_lhs_slot_writer_source_audit.get("identified_writers", [])[:3]
            if isinstance(compare_lhs_slot_writer_source_audit.get("identified_writers"), list)
            else [],
            "identified_sources": compare_lhs_slot_writer_source_audit.get("identified_sources", [])[:3]
            if isinstance(compare_lhs_slot_writer_source_audit.get("identified_sources"), list)
            else [],
            "breakpoint_probe_allowed": compare_lhs_slot_writer_source_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_lhs_slot_writer_source_audit.get("next_bounded_action"),
        }
        if compare_lhs_slot_writer_source_audit
        else {},
        "latest_compare_lhs_slot_writer_predecessor_audit": {
            "classification": slot_writer_predecessor_classification or None,
            "artifact": artifact_refs.get("compare_lhs_slot_writer_predecessor_audit"),
            "candidate_count": compare_lhs_slot_writer_predecessor_audit.get("candidate_count"),
            "runtime_backed_count": compare_lhs_slot_writer_predecessor_audit.get("runtime_backed_count"),
            "actual_compare": compare_lhs_slot_writer_predecessor_audit.get("actual_compare", {}),
            "relations": compare_lhs_slot_writer_predecessor_audit.get("relations", {}),
            "path_observed_counts": compare_lhs_slot_writer_predecessor_audit.get("path_observed_counts", {}),
            "predecessor_rows": compare_lhs_slot_writer_predecessor_audit.get("predecessor_rows", [])[:10]
            if isinstance(compare_lhs_slot_writer_predecessor_audit.get("predecessor_rows"), list)
            else [],
            "identified_sources": compare_lhs_slot_writer_predecessor_audit.get("identified_sources", [])[:3]
            if isinstance(compare_lhs_slot_writer_predecessor_audit.get("identified_sources"), list)
            else [],
            "breakpoint_probe_allowed": compare_lhs_slot_writer_predecessor_audit.get("breakpoint_probe_allowed"),
            "next_bounded_action": compare_lhs_slot_writer_predecessor_audit.get("next_bounded_action"),
        }
        if compare_lhs_slot_writer_predecessor_audit
        else {},
        "function_semantics": function_semantics,
        "uncertainty": sorted(set(uncertainty)),
        "artifact_refs": artifact_refs,
        "generated_at": _now_iso(),
    }


def build_negative_results(artifact_index: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    results = [
        {
            "direction": "old sample_solver blind search",
            "severity": "soft_block",
            "do_not_repeat": True,
            "reason": "compare-aware profile path is current primary route",
            "override_allowed": True,
            "override_reason_required": True,
        },
        {
            "direction": "only increase guided_pool beam or budget",
            "severity": "soft_block",
            "do_not_repeat": True,
            "reason": "previous project notes indicate low return",
            "override_allowed": True,
            "override_reason_required": True,
        },
        {
            "direction": "use compare_semantics_agree=false candidates as primary frontier",
            "severity": "hard_block",
            "do_not_repeat": True,
            "reason": "runtime/offline semantics disagree",
            "override_allowed": True,
            "override_reason_required": True,
        },
        {
            "direction": "commit full solve_reports directory",
            "severity": "hard_block",
            "do_not_repeat": True,
            "reason": "solve_reports is runtime output and may contain bulky or local data",
            "override_allowed": False,
            "override_reason_required": False,
        },
        {
            "direction": "exact2 basin value-pool evaluation with pools 0:78 1:d5/3e/3c 2:40/7f/80 3:b4/8f 4:9c",
            "severity": "soft_block",
            "do_not_repeat": True,
            "reason": (
                "bounded exact2 value-pool branch generated 18 unique candidates and runtime-validated all 18; "
                "best remained exact2 / distance5 246 with no exact3+ or distance improvement"
            ),
            "override_allowed": True,
            "override_reason_required": True,
        },
        {
            "direction": (
                "H1/H3 fixed 8-candidate prefix8 plus Base64 boundary contrast set: "
                "78d540b49c59077041414141414141, 78d540b49c59076f41414141414141, "
                "78d540b49c59077141414141414141, 78d540b49c5907b041414141414141, "
                "78d540b49c5907d041414141414141, 78d540b49c59077040414141414141, "
                "78d540b49c59077042414141414141, 78d540b49c59076f42414141414141"
            ),
            "severity": "soft_block",
            "do_not_repeat": True,
            "reason": (
                "H1/H3 fixed contrast set was runtime-validated with compare_semantics_agree=true; "
                "best stayed exact2 / distance5 246 and improved_over_exact2=false"
            ),
            "override_allowed": True,
            "override_reason_required": True,
        },
        {
            "direction": "repeat current 5-candidate transform trace consistency audit without new runtime evidence",
            "severity": "soft_block",
            "do_not_repeat": True,
            "reason": (
                "transform trace consistency diagnostic confirmed five runtime-backed candidates agree with "
                "offline UTF-16LE/Base64/RC4/compare trace; next work needs a different bounded evidence source"
            ),
            "override_allowed": True,
            "override_reason_required": True,
        },
    ]
    artifacts = artifact_index.get("latest_artifacts", {}) if isinstance(artifact_index, dict) else {}
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    dynamic_probe = _read_json(artifacts.get("dynamic_compare_path_probe"))
    probe_points = dynamic_probe.get("probe_points", {})
    if isinstance(probe_points, dict) and probe_points.get("pre_rc4_runtime_material") == "unavailable":
        results.append(
            {
                "direction": "focused dynamic compare-path probe with current compare-site hook",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "dynamic compare-path probe captured compare-site evidence but did not directly expose "
                    "pre-RC4/Base64/RC4 key material; next evidence source should be lower-level instrumentation"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    pre_rc4_probe = _read_json(artifacts.get("pre_rc4_material_probe"))
    pre_rc4_classification = str(pre_rc4_probe.get("classification") or "").strip()
    if pre_rc4_classification in {
        "pre_rc4_probe_unavailable",
        "material_capture_unreliable",
        "material_capture_partial",
    }:
        results.append(
            {
                "direction": "memory-scan lower-level pre-RC4/key material probe with current automatic harness",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "current memory-scan lower-level probe did not reliably capture pre-RC4/Base64/RC4 key material; "
                    "next evidence source should be narrower material hooks or IDA/x64dbg manual breakpoints around Base64/RC4 construction"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    breakpoint_probe = _read_json(artifacts.get("base64_rc4_breakpoint_probe"))
    breakpoint_classification = str(breakpoint_probe.get("classification") or "").strip()
    hook_results = breakpoint_probe.get("hook_results", {})
    hook_results = hook_results if isinstance(hook_results, dict) else {}
    construction_unavailable = all(
        str(hook_results.get(key, "unavailable")) == "unavailable"
        for key in ("base64_input", "base64_output", "rc4_key", "rc4_input", "rc4_output")
    )
    if breakpoint_classification in {
        "breakpoint_probe_unavailable",
        "base64_rc4_static_points_unavailable",
        "base64_rc4_hook_failed",
        "base64_rc4_compare_only",
    } or (breakpoint_classification == "breakpoint_probe_partial" and construction_unavailable):
        results.append(
            {
                "direction": "scripted Base64/RC4 breakpoint probe with current static access points",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "scripted breakpoint/access probe did not capture Base64 or RC4 construction material; "
                    "next evidence source should be manual IDA/x64dbg breakpoints with explicit addresses"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    static_point_discovery = _read_json(artifacts.get("base64_rc4_static_point_discovery"))
    static_point_classification = str(static_point_discovery.get("classification") or "").strip()
    if static_point_classification in {"static_point_discovery_failed", "manual_disassembly_required"}:
        results.append(
            {
                "direction": "repeat Base64/RC4 static point discovery without new manual disassembly evidence",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "the bounded static discovery did not produce instruction-confirmed Base64/RC4 hook points; "
                    "next evidence source should be manual IDA/x64dbg confirmation"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif static_point_classification == "hookable_points_found":
        results.append(
            {
                "direction": "rerun Base64/RC4 breakpoint probe before confirming a Base64/RC4 instruction hook",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "static discovery found hookable compare-side evidence but no instruction-confirmed Base64/RC4 point; "
                    "the breakpoint probe remains gated until a material construction hook is confirmed"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    compare_stack_probe = _read_json(artifacts.get("compare_stack_pivot_probe"))
    compare_stack_classification = str(compare_stack_probe.get("classification") or "").strip()
    if compare_stack_classification == "compare_stack_pivot_unavailable":
        results.append(
            {
                "direction": "repeat compare stack pivot probe without a new compare-frame evidence source",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "compare stack pivot did not expose UTF-16LE payload or static anchors; "
                    "next evidence source should be explicit manual IDA/x64dbg breakpoints"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif compare_stack_classification in {"compare_stack_pivot_partial", "compare_stack_pivot_complete"}:
        results.append(
            {
                "direction": "repeat scripted Base64/RC4 breakpoint probe before using compare stack pivot hook points",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "compare stack pivot extracted closer handoff evidence from the compare frame; "
                    "next work should hook the recorded handoff points instead of repeating the prior static access probe"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    compare_handoff_probe = _read_json(artifacts.get("compare_handoff_probe"))
    compare_handoff_classification = str(compare_handoff_probe.get("classification") or "").strip()
    if compare_handoff_classification == "handoff_capture_failed":
        results.append(
            {
                "direction": "expand candidate search after compare handoff hooks failed",
                "severity": "hard_block",
                "do_not_repeat": True,
                "reason": (
                    "compare handoff hooks did not capture the expected runtime slot evidence; "
                    "next work should revalidate static hook addresses before any search expansion"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif compare_handoff_classification == "handoff_capture_partial":
        results.append(
            {
                "direction": "repeat compare handoff probe without narrowing the 0x401b50 helper slice",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "compare handoff hooks produced partial runtime evidence; "
                    "next work should backward-slice helper arguments instead of repeating the same hook set"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    compare_handoff_slice_probe = _read_json(artifacts.get("compare_handoff_slice_probe"))
    compare_handoff_slice_classification = str(compare_handoff_slice_probe.get("classification") or "").strip()
    if compare_handoff_slice_classification in {"helper_arg_slice_confirmed", "wrong_reload_anchor"}:
        results.append(
            {
                "direction": "repeat compare handoff helper slice without using its corrected hook conclusion",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "helper argument slicing produced a more specific handoff classification; "
                    "next work should consume that conclusion instead of rerunning the same diagnostic"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif compare_handoff_slice_classification == "helper_arg_slice_partial":
        results.append(
            {
                "direction": "expand candidate search after partial helper argument slice",
                "severity": "hard_block",
                "do_not_repeat": True,
                "reason": (
                    "the helper slice still needs tighter runtime evidence before search expansion is justified"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    compare_handoff_return_site_probe = _read_json(artifacts.get("compare_handoff_return_site_probe"))
    compare_handoff_return_site_classification = str(
        compare_handoff_return_site_probe.get("classification") or ""
    ).strip()
    if compare_handoff_return_site_classification:
        results.append(
            {
                "direction": "repeat compare return-site audit without using its classification",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "the return-site probe produced a more specific handoff classification; "
                    "next work should use that evidence rather than rerunning the same hook set"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    compare_producer_trace_probe = _read_json(artifacts.get("compare_producer_trace_probe"))
    compare_producer_trace_classification = str(compare_producer_trace_probe.get("classification") or "").strip()
    if compare_producer_trace_classification:
        results.append(
            {
                "direction": "repeat compare producer trace without using its classification",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "the producer trace produced a compare-side dataflow classification; "
                    "next work should use that evidence rather than rerunning the same probe"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    material_confirmation = _read_json(artifacts.get("compare_producer_material_confirmation"))
    material_confirmation_classification = str(material_confirmation.get("classification") or "").strip()
    if material_confirmation_classification == "material_confirmation_inconclusive":
        results.append(
            {
                "direction": "repeat producer material confirmation without adding instruction-level evidence",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "the producer material confirmation remained inconclusive; next work should inspect the "
                    "reported producer offsets or add a more specific hook before repeating it"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif material_confirmation_classification in {
        "breakpoint_probe_ready",
        "base64_material_captured",
        "rc4_material_captured",
    }:
        results.append(
            {
                "direction": "rerun Base64/RC4 breakpoint probe without using confirmed material hooks",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "producer material confirmation found instruction-confirmed hooks; the next runtime probe "
                    "must consume those hooks instead of falling back to old static points"
                ),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    pre_compare_handoff = _read_json(artifacts.get("compare_pre_compare_handoff_target_probe"))
    pre_compare_handoff_classification = str(pre_compare_handoff.get("classification") or "").strip()
    if pre_compare_handoff_classification:
        results.append(
            {
                "direction": "repeat old 0x401b50 -> 0x2559 helper assumption after pre-compare handoff evidence",
                "scope": "compare_pre_compare_handoff_target_probe",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "pre-compare handoff follow-up supersedes the old post-helper reload assumption; "
                    "use its relation table or hook miss classification instead"
                ),
                "evidence_artifact": artifacts.get("compare_pre_compare_handoff_target_probe"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        if not bool(pre_compare_handoff.get("breakpoint_probe_allowed")):
            results.append(
                {
                    "direction": "rerun Base64/RC4 breakpoint probe from pre-compare handoff evidence before semantic gate is ready",
                    "scope": "compare_pre_compare_handoff_target_probe",
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": "no hookable candidate-dependent material hook is connected to compare lhs or transform chain yet",
                    "evidence_artifact": artifacts.get("compare_pre_compare_handoff_target_probe"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
    material_hook_runtime_validation = _read_json(artifacts.get("material_hook_runtime_validation"))
    material_hook_runtime_classification = str(material_hook_runtime_validation.get("classification") or "").strip()
    if material_hook_runtime_classification in {"BLOCKED", "REJECTED"}:
        source_esi = (
            str(material_hook_runtime_validation.get("source_compare_esi_source_window_classification") or "").strip()
            == "esi_source_identified"
        )
        results.append(
            {
                "direction": "rerun Base64/RC4 breakpoint probe after material hook runtime validation blocked it",
                "scope": "material_hook_runtime_validation",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "0x2559 did not confirm instruction-backed post-RC4 compare material; "
                    "Base64/RC4 probing remains gated until the writer/source before [ebp-0x1170] is traced"
                    if source_esi
                    else (
                        "0x233d/0x2346 did not confirm instruction-backed, candidate-dependent transform material; "
                        "Base64/RC4 probing remains gated until a different material hook is validated"
                    )
                ),
                "evidence_artifact": artifacts.get("material_hook_runtime_validation"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    elif material_hook_runtime_classification == "ACCEPT":
        results.append(
            {
                "direction": "ignore validated material hook runtime evidence when preparing Base64/RC4 breakpoint points",
                "scope": "material_hook_runtime_validation",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "validated hooks must be consumed directly instead of falling back to older static access points",
                "evidence_artifact": artifacts.get("material_hook_runtime_validation"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    slot_writer_source_audit = _read_json(artifacts.get("compare_lhs_slot_writer_source_audit"))
    slot_writer_source_classification = str(slot_writer_source_audit.get("classification") or "").strip()
    if slot_writer_source_classification:
        results.append(
            {
                "direction": "rerun old 0x2559 material hook after slot writer/source audit",
                "scope": "compare_lhs_slot_writer_source_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "0x2559 was rejected as direct post-RC4 material; use the writer/source audit evidence "
                    "to choose any next material hook"
                ),
                "evidence_artifact": artifacts.get("compare_lhs_slot_writer_source_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        if slot_writer_source_classification not in {"slot_writer_confirmed", "eax_source_identified"}:
            results.append(
                {
                    "direction": "run Base64/RC4 breakpoint probe before slot writer/source validation",
                    "scope": "compare_lhs_slot_writer_source_audit",
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": (
                        "breakpoint probing remains gated until a runtime-backed writer/source is promoted "
                        "and validated as material"
                    ),
                    "evidence_artifact": artifacts.get("compare_lhs_slot_writer_source_audit"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
    predecessor_audit = _read_json(artifacts.get("compare_lhs_slot_writer_predecessor_audit"))
    predecessor_classification = str(predecessor_audit.get("classification") or "").strip()
    if predecessor_classification:
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe before predecessor path validation",
                "scope": "compare_lhs_slot_writer_predecessor_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "breakpoint probing remains gated until the pre-slot predecessor path either identifies "
                    "a runtime-backed source or explains the 0x401b50 path divergence"
                ),
                "evidence_artifact": artifacts.get("compare_lhs_slot_writer_predecessor_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        if predecessor_classification != "pre_slot_source_identified":
            results.append(
                {
                    "direction": "validate 0x253a direct material hook after predecessor path rejected it",
                    "scope": "compare_lhs_slot_writer_predecessor_audit",
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": "0x253a was not reached; the next hook must come from predecessor runtime evidence",
                    "evidence_artifact": artifacts.get("compare_lhs_slot_writer_predecessor_audit"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
    post_handoff_audit = _read_json(artifacts.get("post_handoff_branch_outcome_audit"))
    post_handoff_classification = str(post_handoff_audit.get("classification") or "").strip()
    if post_handoff_classification:
        results.append(
            {
                "direction": "reuse 0x233d/0x2346 as material-hook breakpoints after post-handoff audit rejected them",
                "scope": "post_handoff_branch_outcome_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "post-handoff branch outcome audit consumes the material runtime rejection and keeps "
                    "these hooks blocked until new transform-chain evidence appears"
                ),
                "evidence_artifact": artifacts.get("post_handoff_branch_outcome_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        window = post_handoff_audit.get("window", {})
        window = window if isinstance(window, dict) else {}
        if not bool(window.get("downstream_transform_calls_reached")):
            results.append(
                {
                    "direction": "probe downstream 0x234e/0x2355 Base64/RC4 hooks before branch outcome reaches them",
                    "scope": "post_handoff_branch_outcome_audit",
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": (
                        "0x234e/0x2355 remain downstream of the rejected post-handoff window; "
                        "first identify the branch/call outcome that connects to compare lhs"
                    ),
                    "evidence_artifact": artifacts.get("post_handoff_branch_outcome_audit"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
    exception_unwind_audit = _read_json(artifacts.get("post_handoff_exception_unwind_audit"))
    exception_unwind_classification = str(exception_unwind_audit.get("classification") or "").strip()
    if exception_unwind_classification:
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe before exception/unwind material gates close",
                "scope": "post_handoff_exception_unwind_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "exception/unwind audit keeps breakpoint probing blocked until actual compare lhs, "
                    "connected producer, and candidate-dependent transform material are all runtime-backed"
                ),
                "evidence_artifact": artifacts.get("post_handoff_exception_unwind_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        if exception_unwind_classification in {"inconclusive", "instrumentation_missed_return"}:
            results.append(
                {
                    "direction": "repeat exception/unwind audit without new hook reliability evidence",
                    "scope": "post_handoff_exception_unwind_audit",
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": "the current exception/unwind artifact explicitly routes to missing evidence or hook reliability",
                    "evidence_artifact": artifacts.get("post_handoff_exception_unwind_audit"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
    compare_lhs_audit = _read_json(artifacts.get("compare_lhs_producer_audit"))
    compare_lhs_classification = str(compare_lhs_audit.get("classification") or "").strip()
    if compare_lhs_classification in {"producer_window_rejected", "inconclusive"}:
        results.append(
            {
                "direction": "expand compare-aware search instead of using fixed compare lhs producer audit evidence",
                "scope": "compare_lhs_producer_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "compare lhs producer audit is a bounded sidecar over three fixed candidates and five fixed hooks; "
                    "rejected or inconclusive evidence should move the next runtime hook point, not grow search"
                ),
                "evidence_artifact": artifacts.get("compare_lhs_producer_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe directly from compare lhs producer audit",
                "scope": "compare_lhs_producer_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "this audit never authorizes breakpoint probing; it only supplies a next bounded material-hook start",
                "evidence_artifact": artifacts.get("compare_lhs_producer_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    upstream_writer_audit = _read_json(artifacts.get("compare_lhs_upstream_writer_audit"))
    upstream_writer_classification = str(upstream_writer_audit.get("classification") or "").strip()
    if upstream_writer_classification in {
        "upstream_window_rejected",
        "candidate_dependent_upstream_observed",
        "inconclusive",
    }:
        results.append(
            {
                "direction": "expand compare-aware search instead of following upstream writer evidence",
                "scope": "compare_lhs_upstream_writer_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "upstream writer audit is bounded to fixed candidates and hook points; unresolved evidence "
                    "should move or narrow runtime instrumentation rather than grow search"
                ),
                "evidence_artifact": artifacts.get("compare_lhs_upstream_writer_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe directly from upstream writer audit",
                "scope": "compare_lhs_upstream_writer_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "upstream writer evidence still needs compare-lhs and transform-chain semantic confirmation "
                    "before breakpoint probing is allowed"
                ),
                "evidence_artifact": artifacts.get("compare_lhs_upstream_writer_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    function_semantic_audit = _read_json(artifacts.get("function_semantic_audit"))
    function_semantic_classification = str(function_semantic_audit.get("classification") or "").strip()
    functions = function_semantic_audit.get("functions", [])
    functions = functions if isinstance(functions, list) else []
    if function_semantic_classification and not bool(function_semantic_audit.get("breakpoint_probe_allowed")):
        for item in functions:
            if not isinstance(item, dict):
                continue
            function = str(item.get("function") or "").strip()
            if not function:
                continue
            results.append(
                {
                    "direction": f"treat {function} as Base64/RC4 material producer without new semantic evidence",
                    "scope": "function_semantics",
                    "function": function,
                    "severity": "soft_block",
                    "do_not_repeat": True,
                    "reason": (
                        "function semantic audit did not confirm instruction-confirmed, hookable, "
                        "candidate-dependent material output connected to compare lhs"
                    ),
                    "evidence_artifact": artifacts.get("function_semantic_audit"),
                    "override_allowed": True,
                    "override_reason_required": True,
                }
            )
            if (
                function == "0x401b50"
                and str(item.get("semantic_guess") or "").strip() == "copy_or_handoff"
                and not bool(item.get("candidate_dependent"))
            ):
                results.append(
                    {
                        "direction": "treat 0x401b50 as material producer after 0x2338 without new candidate-dependent return evidence",
                        "scope": "function_semantics",
                        "function": "0x401b50",
                        "severity": "soft_block",
                        "do_not_repeat": True,
                        "reason": (
                            "0x2338 call-outcome evidence indicates copy/handoff behavior without candidate-dependent "
                            "material output connected to compare lhs or transform chain"
                        ),
                        "evidence_artifact": artifacts.get("function_semantic_audit"),
                        "override_allowed": True,
                "override_reason_required": True,
            }
        )
    callsite_reanchor_audit = _read_json(
        artifacts.get("compare_callsite_reanchor_and_lhs_provenance_audit")
    )
    callsite_reanchor_classification = str(callsite_reanchor_audit.get("classification") or "").strip()
    if callsite_reanchor_classification in {
        "frame_anchor_rejected",
        "callsite_reanchored_but_producer_unknown",
        "inconclusive",
    }:
        results.append(
            {
                "direction": "reuse old [ebp-0x1170] frame anchor without actual compare re-anchor evidence",
                "scope": "compare_callsite_reanchor_and_lhs_provenance_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "the real compare lhs side and frame source must be confirmed before following old frame assumptions",
                "evidence_artifact": artifacts.get("compare_callsite_reanchor_and_lhs_provenance_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe directly from callsite re-anchor audit",
                "scope": "compare_callsite_reanchor_and_lhs_provenance_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "breakpoint probing still requires a runtime-backed lhs producer connected to compare lhs",
                "evidence_artifact": artifacts.get("compare_callsite_reanchor_and_lhs_provenance_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    real_lhs_provenance_audit = _read_json(artifacts.get("compare_real_lhs_provenance_audit"))
    real_lhs_provenance_classification = str(real_lhs_provenance_audit.get("classification") or "").strip()
    if real_lhs_provenance_classification in {
        "lhs_register_source_confirmed",
        "old_frame_anchor_rejected",
        "writer_path_observed_but_unconnected",
        "compare_lhs_runtime_backed_writer_missing",
        "instrumentation_incomplete",
        "inconclusive",
    }:
        results.append(
            {
                "direction": "reuse old [ebp-0x1170] without real-lhs provenance evidence",
                "scope": "compare_real_lhs_provenance_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "old frame anchor still is not a runtime-backed source for confirmed compare arg0",
                "evidence_artifact": artifacts.get("compare_real_lhs_provenance_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe before real lhs producer identification",
                "scope": "compare_real_lhs_provenance_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "breakpoint probing remains blocked until a runtime-backed real lhs producer is identified",
                "evidence_artifact": artifacts.get("compare_real_lhs_provenance_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    esi_source_window_audit = _read_json(artifacts.get("compare_esi_source_window_audit"))
    esi_source_window_classification = str(esi_source_window_audit.get("classification") or "").strip()
    if esi_source_window_classification in {
        "repair_call_updates_lhs",
        "pre_compare_branch_bypasses_repair",
        "window_observed_but_source_unknown",
        "inconclusive",
    }:
        results.append(
            {
                "direction": "run Base64/RC4 breakpoint probe before ESI source window identification",
                "scope": "compare_esi_source_window_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "breakpoint probing remains blocked until a runtime-backed ESI source connects to compare arg0",
                "evidence_artifact": artifacts.get("compare_esi_source_window_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
        results.append(
            {
                "direction": "reuse old [ebp-0x1170] as proven source without ESI window evidence",
                "scope": "compare_esi_source_window_audit",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": "the old frame slot must be re-proven inside 0x2559..0x258b before guiding material hooks",
                "evidence_artifact": artifacts.get("compare_esi_source_window_audit"),
                "override_allowed": True,
                "override_reason_required": True,
            }
        )
    return results


def _case_results_have_errors(paths: list[str]) -> bool:
    for path in paths:
        data = _read_json(path)
        if str(data.get("status") or "").lower() == "error":
            return True
        if data.get("error"):
            return True
    return False


def _summary_has_errors(path: str | None) -> bool:
    data = _read_json(path)
    try:
        return int(data.get("error_cases", 0) or 0) > 0
    except (TypeError, ValueError):
        return False


def _build_summary_error_detail(
    *,
    artifact_index: dict[str, Any],
    case_paths: list[Any],
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Build a backward-compatible diagnostic dict explaining why the latest harness run triggered errors.

    This field is only populated when the ``latest harness case has errors`` gate fires.
    Existing consumers that do not read ``harness_diagnostics`` continue to work.
    """
    latest_run = artifact_index.get("latest_harness_run")
    latest_summary_path = artifact_index.get("latest_summary")
    detail: dict[str, Any] = {
        "latest_harness_run": latest_run,
        "summary_present": latest_summary_path is not None,
        "case_results_count": len(case_paths),
        "case_results_missing": len(case_paths) == 0,
    }
    if latest_summary_path:
        summary_data = _read_json(str(latest_summary_path))
        if isinstance(summary_data, dict):
            detail["summary_total_cases"] = summary_data.get("total_cases")
            detail["summary_executed_cases"] = summary_data.get("executed_cases")
            detail["summary_resumed_cases"] = summary_data.get("resumed_cases")
            detail["summary_error_cases"] = summary_data.get("error_cases")
    # Classify the root cause for downstream consumers
    if len(case_paths) == 0:
        detail["diagnosis"] = "case_results_directory_absent"
        detail["diagnosis_detail"] = (
            "The latest harness run has no case_results/ directory. "
            "The summary may report error_cases if cases were resumed from a prior incomplete run "
            "or the run completed without executing any case."
        )
        detail["latest_harness_run_status"] = "invalid_or_incomplete"
    else:
        detail["diagnosis"] = "case_results_contain_errors"
        detail["diagnosis_detail"] = (
            "One or more case result files have status='error' or an 'error' field."
        )
        detail["latest_harness_run_status"] = "case_results_have_errors"
    # Look for a complete fallback run when the latest is invalid/incomplete
    if reports_dir is not None and detail.get("latest_harness_run_status") == "invalid_or_incomplete":
        latest_run_path = _path_from_json(latest_run) if latest_run else None
        fallback = _find_fallback_harness_run(reports_dir, latest_run_path)
        if fallback is not None:
            detail["fallback_harness_run"] = fallback
            detail["fallback_available"] = True
        else:
            detail["fallback_available"] = False
    return detail


def _has_runtime_validation(artifact_refs: dict[str, Any]) -> bool:
    return any(key in artifact_refs for key in RUNTIME_VALIDATION_KEYS)


def _has_disagreeing_candidate(current_state: dict[str, Any]) -> bool:
    best = current_state.get("best_candidates", {})
    if not isinstance(best, dict):
        return False
    for value in best.values():
        if isinstance(value, dict) and value.get("compare_semantics_agree") is False:
            return True
    return False


def build_model_gate(
    *,
    artifact_index: dict[str, Any],
    current_state: dict[str, Any],
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    artifact_refs = current_state.get("artifact_refs", {})
    artifact_refs = artifact_refs if isinstance(artifact_refs, dict) else {}
    missing = list(artifact_index.get("missing", []))
    has_runtime_validation = _has_runtime_validation(artifact_refs)
    bottleneck = current_state.get("current_bottleneck", {})
    bottleneck = bottleneck if isinstance(bottleneck, dict) else {}
    stage = bottleneck.get("stage")
    reason = bottleneck.get("reason")
    case_paths = artifact_index.get("latest_case_results", [])
    case_paths = case_paths if isinstance(case_paths, list) else []

    if "reports_dir" in missing or "latest_harness_run" in missing:
        return {
            "should_call_model": False,
            "context_level": 0,
            "reason": "solve_reports or latest harness run is missing",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": "collect_artifacts",
            "missing_evidence": missing,
            "generated_at": _now_iso(),
        }

    if not has_runtime_validation or "frontier_summary" in missing or "strata_summary" in missing:
        needed = sorted(set([*missing, "runtime_validation"] if not has_runtime_validation else missing))
        return {
            "should_call_model": False,
            "context_level": 0,
            "reason": "artifact evidence is incomplete; do not ask the model to guess",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": "collect_artifacts",
            "missing_evidence": needed,
            "generated_at": _now_iso(),
        }

    latest_summary = artifact_index.get("latest_summary")
    summary_error_detail = _build_summary_error_detail(
        artifact_index=artifact_index,
        case_paths=case_paths,
        reports_dir=reports_dir,
    )
    if _summary_has_errors(str(latest_summary) if latest_summary else None) or _case_results_have_errors(
        [str(item) for item in case_paths]
    ):
        # When case_results/ is missing, there is no concrete failed case-result to inspect.
        # Surface a more actionable next step instead of an unactionable inspection instruction.
        if summary_error_detail.get("case_results_missing") is True:
            # If a complete fallback run exists, keep the latest marked as invalid and
            # surface the fallback explicitly; do not silently promote it as current.
            if summary_error_detail.get("fallback_available") is True:
                fallback_info = summary_error_detail.get("fallback_harness_run", {})
                # Audit the selected fallback evidence for readiness
                readiness_audit = _audit_fallback_evidence_readiness(fallback_info)
                selected_evidence = {
                    "selection_role": "fallback",
                    "run_name": fallback_info.get("run_name"),
                    "run_path": fallback_info.get("run_path"),
                    "summary_path": fallback_info.get("summary_path"),
                    "manifest_path": fallback_info.get("manifest_path"),
                    "case_results_count": fallback_info.get("executed_cases", 0),
                    "total_cases": fallback_info.get("total_cases", 0),
                    "provenance": fallback_info.get("provenance", "fallback_from_invalid_latest_run"),
                    "latest_invalid_run": summary_error_detail.get("latest_harness_run"),
                    "latest_invalid_run_status": summary_error_detail.get("latest_harness_run_status"),
                    "latest_invalid_run_reason": summary_error_detail.get("diagnosis"),
                    "readiness_audit": readiness_audit,
                }
                # Advance next_local_action based on readiness classification
                next_local_action = readiness_audit.get("next_local_action", "repair_selected_fallback_evidence")
            else:
                selected_evidence = None
                next_local_action = "rebuild_harness_artifact"
        else:
            selected_evidence = None
            next_local_action = "inspect_failed_case_result"
        result: dict[str, Any] = {
            "should_call_model": False,
            "context_level": 1,
            "reason": "latest harness case has errors",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": next_local_action,
            "missing_evidence": [],
            "harness_diagnostics": summary_error_detail,
            "generated_at": _now_iso(),
        }
        if selected_evidence is not None:
            result["selected_harness_evidence_source"] = selected_evidence
        return result

    if _has_disagreeing_candidate(current_state):
        return {
            "should_call_model": True,
            "context_level": 2,
            "reason": "offline/runtime compare semantics disagree for at least one current candidate",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": "",
            "missing_evidence": [],
            "generated_at": _now_iso(),
        }

    if stage or reason:
        text = f"{stage or ''} {reason or ''}".lower()
        context_level = 3 if "mainline" in text and "wrong" in text else 2
        return {
            "should_call_model": True,
            "context_level": context_level,
            "reason": reason or f"{stage} appears stalled",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": "",
            "missing_evidence": [],
            "generated_at": _now_iso(),
        }

    return {
        "should_call_model": False,
        "context_level": 0,
        "reason": "insufficient bottleneck evidence",
        "recommended_packet": "project_state/task_packet.json",
        "next_local_action": "generate_missing_evidence",
        "missing_evidence": ["current_bottleneck"],
        "generated_at": _now_iso(),
    }


def _do_not_do_items(negative_results: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    for result in negative_results:
        if not result.get("do_not_repeat"):
            continue
        direction = str(result.get("direction") or "").strip()
        if direction == "old sample_solver blind search":
            items.append("do not return to old sample_solver blind search")
        elif direction == "only increase guided_pool beam or budget":
            items.append("do not only increase beam or budget")
        elif direction == "use compare_semantics_agree=false candidates as primary frontier":
            items.append("do not use compare_semantics_agree=false candidates as primary frontier")
        elif direction == "commit full solve_reports directory":
            items.append("do not commit full solve_reports directory")
        elif direction:
            items.append(f"do not repeat: {direction}")
    items.append("do not scan entire solve_reports unless explicitly needed")
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _task_from_bottleneck(current_state: dict[str, Any]) -> str:
    bottleneck = current_state.get("current_bottleneck", {})
    bottleneck = bottleneck if isinstance(bottleneck, dict) else {}
    best_candidates = current_state.get("best_candidates", {})
    best_candidates = best_candidates if isinstance(best_candidates, dict) else {}
    stage = str(bottleneck.get("stage") or "")
    reason = str(bottleneck.get("reason") or "")
    blocker = str(bottleneck.get("blocker") or "")
    text = f"{stage} {reason}".lower()
    has_exact1 = isinstance(best_candidates.get("exact1"), dict) and bool(best_candidates.get("exact1"))
    latest_material_hook = current_state.get("latest_material_hook_runtime_validation", {})
    latest_material_hook = latest_material_hook if isinstance(latest_material_hook, dict) else {}
    source_esi = str(latest_material_hook.get("source_compare_esi_source_window_classification") or "")
    if stage == "compare_real_lhs_provenance_audit" and reason == "last_writer_identified":
        return "Validate bounded material hook from confirmed compare lhs last writer"
    if stage == "compare_real_lhs_provenance_audit" and blocker == "arg0_final_data_writer_identified":
        return "Validate bounded material hook from confirmed actual arg0 final data writer"
    if stage == "compare_real_lhs_provenance_audit" and blocker in {
        "arg0_pointer_chain_identified_writer_missing",
        "arg0_final_writer_trace_schema_gap",
        "arg0_final_writer_not_observed_in_bounded_window",
        "arg0_writer_trace_runtime_blocked",
    }:
        return "Refine bounded actual arg0 final data writer trace"
    if stage == "compare_real_lhs_provenance_audit" and blocker in {
        "arg0_hook_installed_but_not_hit",
        "hook_installed_but_compare_call_not_reached_after_ui_trigger",
        "ui_trigger_success_but_target_path_skipped_compare_call",
        "static_compare_callsite_address_mismatch",
        "hook_hit_payload_emitted_but_python_filter_dropped",
        "python_message_bridge_received_but_aggregation_dropped",
        "ui_trigger_executed_but_compare_arg_observation_missing",
        "arg0_hook_hit_but_message_delivery_failed",
        "message_bridge_dropped_observation",
        "arg0_ui_trigger_timing_fixed_observations_available",
        "hooks_not_ready_before_ui_trigger",
        "arg0_ui_trigger_or_timeout_blocked",
        "arg0_target_path_or_process_mismatch",
        "ui_trigger_not_executed",
        "sidecar_payload_schema_gap",
        "compare_arg_payload_schema_gap",
        "sidecar_runtime_precondition_failed",
        "project_state_projection_gap",
        "artifact_aggregation_gap",
        "inconclusive_with_missing_required_telemetry",
    }:
        return "Diagnose sidecar observation delivery blocker"
    if stage == "compare_real_lhs_provenance_audit" and blocker == "arg0_pointer_carrier_identified_writer_missing":
        return "Trace final writer for actual compare arg0 after confirmed ESI carrier"
    if stage == "compare_hook_path_reachability_audit":
        if reason == "compare_window_reached_after_ui_trigger":
            return "Resume bounded compare-arg observation diagnosis"
        if reason == "static_compare_hook_address_stale_for_current_binary":
            return "Refresh static compare hook address validation"
        if reason == "sidecar_runtime_precondition_failed":
            return "Restore bounded sidecar runtime prerequisites"
        return "Diagnose bounded compare hook path reachability"
    if stage == "compare_handoff_exit_classifier_audit":
        if reason == "exception_unwind_before_compare":
            return "Trace exception unwind edge before compare"
        if reason == "branch_guard_before_compare":
            return "Trace branch guard before compare"
        if reason == "wrong_successor_or_hook_site":
            return "Correct bounded handoff successor hook surface"
        if reason == "instrumentation_inconclusive":
            return "Restore bounded handoff-exit classifier instrumentation"
        return "Classify bounded candidate-dependent handoff exit"
    if stage == "compare_handoff_path_divergence_audit":
        return "Trace bounded branch operand or exception edge provenance"
    if stage == "compare_handoff_edge_operand_provenance_audit":
        if reason in {
            "candidate_dependent_handoff_exit_edge_unresolved",
            "hook_surface_or_instrumentation_gap",
        }:
            return "Trace bounded branch operand runtime sidecar or instruction boundary"
        return "Review bounded handoff edge operand provenance"
    if stage == "compare_handoff_branch_operand_runtime_audit":
        if reason in {"instruction_boundary_gap", "instrumentation_gap"}:
            return "Repair bounded handoff branch hook surface"
        if reason == "return_target_candidate_dependent":
            return "Correct bounded handoff return-target provenance"
        return "Review bounded handoff branch operand audit"
    if stage == "compare_handoff_hook_surface_repair_audit":
        if reason == "hook_surface_requires_post_entry_step":
            return "Run bounded post-entry step runtime audit"
        if reason == "return_target_schema_gap":
            return "Correct bounded handoff return-target schema"
        return "Review bounded handoff hook surface repair audit"
    if stage == "compare_handoff_post_entry_step_runtime_audit":
        if reason in {
            "runtime_unavailable",
            "instrumentation_gap",
            "hook_surface_unresolved",
            "debugger_backend_missing",
            "target_process_launch_failed",
            "breakpoint_install_failed",
            "entry_breakpoint_not_hit",
            "step_api_unavailable",
            "instrumentation_gap_but_environment_verified",
        }:
            return "Repair bounded post-entry step instrumentation"
        if reason == "exception_edge_before_branch":
            return "Confirm bounded post-entry exception edge"
        if reason == "post_entry_branch_observed":
            return "Audit bounded post-entry branch operand statically"
        return "Review bounded post-entry step runtime audit"
    if stage == "compare_handoff_narrower_post_entry_breakpoint_audit":
        if reason in {
            "process_exited_before_window_discovery",
            "window_lifecycle_no_window_created",
            "process_alive_no_top_window",
            "process_window_inventory_empty",
            "process_no_visible_window",
            "pid_alive_but_no_owned_window",
            "win32_enum_windows_empty",
            "window_exists_but_not_visible",
            "top_window_call_timeout",
            "top_window_call_failed",
            "window_discovery_api_blocked",
            "win32_enum_windows_succeeded_pywinauto_failed",
            "uia_backend_succeeded_win32_failed",
            "window_backend_mismatch",
            "window_discovery_succeeded_input_lookup_next",
            "window_discovery_instrumentation_gap",
        }:
            return "Review bounded window discovery diagnostics"
        if reason in {
            "target_launch_failed",
            "frida_attach_or_spawn_failed",
            "breakpoint_install_failed",
            "entry_breakpoint_not_hit",
            "successor_breakpoint_not_hit",
            "instrumentation_gap_but_environment_verified",
        }:
            return "Review bounded narrower post-entry breakpoint blocker"
        if reason == "post_entry_breakpoint_observed":
            return "Project bounded post-entry breakpoint control-flow evidence"
        return "Review bounded narrower post-entry breakpoint audit"
    if stage == "compare_real_lhs_provenance_audit" and reason in {
        "writer_path_observed_but_unconnected",
        "compare_lhs_runtime_backed_writer_missing",
        "instrumentation_incomplete",
    }:
        return "Improve compare lhs last-writer instrumentation"
    if stage == "compare_real_lhs_provenance_audit" and reason == "lhs_register_source_confirmed":
        return "Trace ESI source window 0x2559..0x258b"
    if stage == "material_hook_runtime_validation" and reason == "ACCEPT" and source_esi == "esi_source_identified":
        return "Run bounded Base64/RC4 breakpoint probe with validated 0x2559 hook"
    if stage == "material_hook_runtime_validation" and reason in {"BLOCKED", "REJECTED"} and source_esi == "esi_source_identified":
        return "Trace writer/source before 0x2559 / [ebp-0x1170]"
    if stage == "compare_lhs_slot_writer_source_audit" and reason in {
        "slot_writer_confirmed",
        "eax_source_identified",
    }:
        return "Validate bounded material hook from confirmed slot writer/source"
    if stage == "compare_lhs_slot_writer_source_audit" and reason == "writer_hook_not_reached":
        return "Trace 0x2338..0x253a predecessor path before slot writer"
    if stage == "compare_lhs_slot_writer_source_audit":
        return "Investigate stalled compare lhs slot writer/source path"
    if stage == "compare_lhs_slot_writer_predecessor_audit" and reason == "pre_slot_source_identified":
        return "Validate bounded material hook from confirmed pre-slot predecessor source"
    if stage == "compare_lhs_slot_writer_predecessor_audit" and reason == "handoff_call_does_not_return_to_linear_path":
        return "Trace 0x401b50 return, branch, or exception outcome"
    if stage == "compare_lhs_slot_writer_predecessor_audit" and reason == "linear_path_diverges_before_output_call":
        return "Trace linear path divergence between 0x233d and output calls"
    if stage == "compare_lhs_slot_writer_predecessor_audit":
        return "Investigate stalled compare lhs slot writer predecessor path"
    if stage == "post_handoff_branch_outcome_audit" and reason == "handoff_returns_to_alternate_site":
        return "Validate bounded material/source hook from confirmed 0x401b50 alternate return site"
    if stage == "post_handoff_branch_outcome_audit" and reason == "handoff_tailcalls_or_jumps":
        return "Trace 0x401b50 tail-call or jump target"
    if stage == "post_handoff_branch_outcome_audit" and reason == "handoff_exception_or_unwind":
        return "Trace 0x401b50 exception or unwind handler"
    if stage == "post_handoff_branch_outcome_audit" and reason == "callee_observed_but_exit_unknown":
        return "Improve bounded 0x401b50 exit coverage"
    if stage == "post_handoff_branch_outcome_audit" and reason == "inconclusive":
        return "Improve post-handoff branch outcome evidence"
    if stage == "post_handoff_exception_unwind_audit" and reason == "normal_return_to_compare_path":
        return "Trace lhs producer provenance from normal 0x401b50 return path"
    if stage == "post_handoff_exception_unwind_audit" and reason in {
        "exception_dispatch_to_compare_path",
        "seh_unwind_to_compare_path",
    }:
        return "Trace handler-to-lhs dataflow"
    if stage == "post_handoff_exception_unwind_audit" and reason == "alternate_return_to_compare_path":
        return "Slice confirmed 0x401b50 alternate return target"
    if stage == "post_handoff_exception_unwind_audit" and reason == "compare_reached_but_path_unresolved":
        return "Trace last-writer memory provenance before 0x258c"
    if stage == "post_handoff_exception_unwind_audit" and reason == "instrumentation_missed_return":
        return "Fix 0x401b50 exception/unwind hook reliability"
    if stage == "post_handoff_exception_unwind_audit":
        return "Collect missing 0x401b50 exception/unwind evidence"
    if stage == "compare_esi_source_window_audit" and reason == "esi_source_identified":
        return "Promote identified ESI source into bounded material-hook validation"
    if stage == "compare_esi_source_window_audit":
        return "Investigate stalled ESI source window path"
    if ("exact1" in text and ("pair" in text or "projected" in text)) or (has_exact1 and "pair" in text):
        return "Generate next decision for exact1 pair_pool bottleneck"
    if stage or reason:
        return f"Investigate stalled {stage or reason} path"
    return "collect_missing_evidence"


def _task_scope_fields(task: str) -> dict[str, str]:
    return {
        "state_scope": STATE_SCOPE_SAMPLE,
        "task_source": TASK_SOURCE_DERIVED_FROM_SAMPLE_ARTIFACTS,
        "derived_task": task,
        "active_decision_packet": ACTIVE_DECISION_PACKET,
        "execution_scope": EXECUTION_SCOPE_DECISION_PACKET_CONTROLS_CURRENT_ROUND,
    }


def build_task_packet(
    *,
    current_state: dict[str, Any],
    negative_results: list[dict[str, Any]],
    model_gate: dict[str, Any],
) -> dict[str, Any]:
    artifact_refs = current_state.get("artifact_refs", {})
    artifact_refs = artifact_refs if isinstance(artifact_refs, dict) else {}
    best_candidates = current_state.get("best_candidates", {})
    best_candidates = best_candidates if isinstance(best_candidates, dict) else {}
    bottleneck = current_state.get("current_bottleneck", {})
    bottleneck = bottleneck if isinstance(bottleneck, dict) else {}
    has_current_best = any(isinstance(value, dict) and value for value in best_candidates.values())
    has_stall_stage = bool(bottleneck.get("stage") or bottleneck.get("reason"))
    has_runtime_validation = _has_runtime_validation(artifact_refs)
    missing_evidence = model_gate.get("missing_evidence", [])

    if not model_gate.get("should_call_model"):
        next_local_action = model_gate.get("next_local_action")
        # When the actionable local step is repairing the harness artifact,
        # frame the task as harness repair rather than generic reverse-solving.
        # Also handle fallback selection and rebuild actions with precise naming.
        if next_local_action in (
            "repair_harness_artifact",
            "select_fallback_harness_run",
            "rebuild_harness_artifact",
            "inspect_selected_fallback_evidence",
            "prepare_reverse_solving_from_selected_fallback_evidence",
            "repair_selected_fallback_evidence",
            "repair_harness_case_result_materialization",
            "repair_artifact_manifest_metadata",
            "repair_solver_candidate_generation",
        ):
            task = next_local_action
        else:
            task = "collect_missing_evidence"
        return {
            "task": task,
            **_task_scope_fields(task),
            "sample": current_state.get("sample"),
            "profile": current_state.get("profile"),
            "active_strategy": current_state.get("active_strategy"),
            "current_bottleneck": bottleneck,
            "current_best": best_candidates,
            "do_not_do": _do_not_do_items(negative_results),
            "relevant_files": [
                "reverse_agent/function_semantics.py",
                "reverse_agent/strategies/compare_aware_search.py",
                "tests/test_compare_aware_search_strategy.py",
                "tests/test_project_state.py",
            ],
            "missing_evidence": missing_evidence,
            "next_local_action": next_local_action,
            "reason": model_gate.get("reason"),
            "artifact_refs": artifact_refs,
            "included": ["artifact references", "missing evidence", "model gate reason"],
            "omitted": [
                {
                    "name": "full PROJECT_PROGRESS_LOG.txt",
                    "reason": "too long; use only for strategic review",
                },
                {
                    "name": "full solve_reports",
                    "reason": "runtime output; indexed via artifact_index.json",
                },
            ],
            "sufficiency_check": {
                "has_current_best": has_current_best,
                "has_stall_stage": has_stall_stage,
                "has_negative_results": bool(negative_results),
                "has_artifact_refs": bool(artifact_refs),
                "has_runtime_validation": has_runtime_validation,
            },
            "expected_gpt_output": ACTIVE_DECISION_PACKET,
            "generated_at": _now_iso(),
        }

    task = _task_from_bottleneck(current_state)
    return {
        "task": task,
        **_task_scope_fields(task),
        "sample": current_state.get("sample"),
        "profile": current_state.get("profile"),
        "active_strategy": current_state.get("active_strategy"),
        "current_bottleneck": bottleneck,
        "current_best": best_candidates,
        "do_not_do": _do_not_do_items(negative_results),
        "relevant_files": [
            "reverse_agent/function_semantics.py",
            "reverse_agent/strategies/compare_aware_search.py",
            "tests/test_compare_aware_search_strategy.py",
            "tests/test_project_state.py",
        ],
        "artifact_refs": artifact_refs,
        "included": [
            "current state",
            "best candidates",
            "stall reason",
            "negative results",
            "artifact references",
        ],
        "omitted": [
            {
                "name": "full PROJECT_PROGRESS_LOG.txt",
                "reason": "too long; use only for strategic review",
            },
            {
                "name": "full solve_reports",
                "reason": "runtime output; indexed via artifact_index.json",
            },
        ],
        "sufficiency_check": {
            "has_current_best": has_current_best,
            "has_stall_stage": has_stall_stage,
            "has_negative_results": bool(negative_results),
            "has_artifact_refs": bool(artifact_refs),
            "has_runtime_validation": has_runtime_validation,
        },
        "model_gate": {
            "should_call_model": model_gate.get("should_call_model"),
            "context_level": model_gate.get("context_level"),
            "reason": model_gate.get("reason"),
        },
        "expected_gpt_output": ACTIVE_DECISION_PACKET,
        "generated_at": _now_iso(),
    }


def apply_state_identity(
    *,
    artifact_index: dict[str, Any],
    current_state: dict[str, Any],
    task_packet: dict[str, Any],
) -> None:
    stamp, generated_at = _identity_timestamp()
    source_harness_run = _source_harness_run_name(artifact_index)
    source_git_commit = _git_commit()
    current_state.update(
        {
            "schema_version": STATE_SCHEMA_VERSION,
            "workflow_status": DEFAULT_WORKFLOW_STATUS,
            "current_owner": DEFAULT_CURRENT_OWNER,
            "review_status": DEFAULT_REVIEW_STATUS,
            "source_git_commit": source_git_commit,
            "source_harness_run": source_harness_run,
            "generated_at": generated_at,
        }
    )
    digest = _state_digest(current_state)
    current_state.update(
        {
            "state_build_id": f"state_{stamp}_{digest[:12]}",
            "round_id": f"round_{stamp}",
            "state_digest": digest,
        }
    )
    task_packet.update(
        {
            "schema_version": STATE_SCHEMA_VERSION,
            "state_build_id": current_state["state_build_id"],
            "round_id": current_state["round_id"],
            "based_on_state_digest": digest,
        }
    )


def build_project_state(
    *,
    reports_dir: Path,
    state_dir: Path,
    sample: str,
    run_name: str = "",
    progress_log: Path | None = None,
    max_artifacts: int = 20,
) -> dict[str, Any]:
    _ = progress_log
    ensure_state_layout(state_dir)
    artifact_index = build_artifact_index(
        reports_dir=reports_dir,
        sample=sample,
        run_name=run_name,
        max_artifacts=max_artifacts,
    )
    current_state = build_current_state(artifact_index=artifact_index, sample=sample)
    negative_results = build_negative_results(artifact_index=artifact_index)
    model_gate = build_model_gate(artifact_index=artifact_index, current_state=current_state, reports_dir=reports_dir)
    task_packet = build_task_packet(
        current_state=current_state,
        negative_results=negative_results,
        model_gate=model_gate,
    )
    apply_state_identity(
        artifact_index=artifact_index,
        current_state=current_state,
        task_packet=task_packet,
    )

    outputs = {
        "artifact_index": artifact_index,
        "current_state": current_state,
        "negative_results": negative_results,
        "model_gate": model_gate,
        "task_packet": task_packet,
    }
    for name, payload in outputs.items():
        _write_json(state_dir / f"{name}.json", payload)
    return outputs


def new_round(*, state_dir: Path) -> dict[str, Any]:
    ensure_state_layout(state_dir)
    return {
        "state_dir": _path_for_json(state_dir),
        "rounds_dir": _path_for_json(state_dir / "rounds"),
        "initialized": True,
    }


def _resolve_round_dir(state_dir: Path, round_id: str = "") -> Path:
    rounds_dir = state_dir / "rounds"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    if round_id:
        return rounds_dir / round_id
    index = 1
    while True:
        candidate = rounds_dir / f"round_{index:03d}"
        if not candidate.exists():
            return candidate
        index += 1


def _git_diff_text() -> str:
    try:
        proc = subprocess.run(
            ["git", "diff", "--no-ext-diff"],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"git diff unavailable: {exc}\n"
    if proc.returncode != 0:
        return f"git diff failed ({proc.returncode}): {(proc.stderr or proc.stdout).strip()}\n"
    return proc.stdout or ""


def _archive_source_file_bytes(
    state_dir: Path,
    pytest_result: Path | None,
    *,
    include_state_snapshot: bool,
    include_diff: bool,
) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    include_names = list(ARCHIVE_MINIMAL_NAMES)
    if include_state_snapshot:
        include_names.extend(ARCHIVE_STATE_SNAPSHOT_NAMES)
    for name in include_names:
        src = state_dir / name
        if src.exists():
            files[name] = src.read_bytes()
    if include_diff:
        files["git_diff.patch"] = _git_diff_text().encode("utf-8")
    result_src = pytest_result or (state_dir / "pytest_result.txt")
    if result_src.exists():
        files["pytest_result.txt"] = result_src.read_bytes()
    else:
        files["pytest_result.txt"] = b"No pytest_result.txt was available for this round.\n"
    return files


def _archive_file_source_path(
    state_dir: Path,
    name: str,
    pytest_result: Path | None,
    *,
    include_state_snapshot: bool,
    include_diff: bool,
) -> Path | None:
    if name in ARCHIVE_MINIMAL_NAMES or (include_state_snapshot and name in ARCHIVE_STATE_SNAPSHOT_NAMES):
        return state_dir / name
    if name == "pytest_result.txt":
        result_src = pytest_result or (state_dir / "pytest_result.txt")
        return result_src if result_src.exists() else None
    if name == "git_diff.patch" and include_diff:
        return None
    return None


def _archive_file_manifest(
    state_dir: Path,
    round_id: str,
    files: dict[str, bytes],
    pytest_result: Path | None,
    *,
    include_state_snapshot: bool,
    include_diff: bool,
) -> dict[str, dict[str, str | None]]:
    manifest: dict[str, dict[str, str | None]] = {}
    for name, data in sorted(files.items()):
        source_path = _archive_file_source_path(
            state_dir,
            name,
            pytest_result,
            include_state_snapshot=include_state_snapshot,
            include_diff=include_diff,
        )
        archived_path = state_dir / "rounds" / round_id / name
        manifest[name] = {
            "source_path": _path_for_json(source_path) if source_path is not None else None,
            "archived_path": _path_for_json(archived_path),
            "sha256": _sha256_bytes(data),
        }
    return manifest


def _build_round_manifest(
    *,
    round_id: str,
    state_dir: Path,
    archived_at: str,
    files: dict[str, bytes],
    pytest_result: Path | None,
    include_state_snapshot: bool,
    include_diff: bool,
) -> dict[str, Any]:
    current_state = _read_json(state_dir / "current_state.json")
    archive_mode = "full" if include_state_snapshot and include_diff else "state_snapshot" if include_state_snapshot else "minimal"
    omitted_files = [
        name for name in ARCHIVE_OPTIONAL_NAMES if name not in files
    ]
    return {
        "schema_version": 1,
        "round_id": round_id,
        "archived_at": archived_at,
        "source_git_commit": _git_commit() or current_state.get("source_git_commit") or "",
        "source_harness_run": current_state.get("source_harness_run") or "",
        "state_build_id": current_state.get("state_build_id") or "",
        "state_digest": current_state.get("state_digest") or "",
        "workflow_status": current_state.get("workflow_status") or "",
        "archive_mode": archive_mode,
        "included_diff": bool(include_diff),
        "included_state_snapshot": bool(include_state_snapshot),
        "omitted_files": omitted_files,
        "files": _archive_file_manifest(
            state_dir,
            round_id,
            files,
            pytest_result,
            include_state_snapshot=include_state_snapshot,
            include_diff=include_diff,
        ),
    }


def _manifest_for_compare(manifest: dict[str, Any]) -> dict[str, Any]:
    comparable = dict(manifest)
    comparable.pop("archived_at", None)
    return comparable


def archive_round(
    *,
    state_dir: Path,
    round_id: str = "",
    pytest_result: Path | None = None,
    include_state_snapshot: bool = False,
    include_diff: bool = False,
) -> dict[str, Any]:
    ensure_state_layout(state_dir)
    current_state = _read_json(state_dir / "current_state.json")
    selected_round_id = round_id or str(current_state.get("round_id") or "")
    round_dir = _resolve_round_dir(state_dir, round_id=selected_round_id)
    files = _archive_source_file_bytes(
        state_dir,
        pytest_result,
        include_state_snapshot=include_state_snapshot,
        include_diff=include_diff,
    )
    existing_manifest = _read_json(round_dir / "round_manifest.json")
    archived_at = str(existing_manifest.get("archived_at") or _now_iso())
    manifest = _build_round_manifest(
        round_id=round_dir.name,
        state_dir=state_dir,
        archived_at=archived_at,
        files=files,
        pytest_result=pytest_result,
        include_state_snapshot=include_state_snapshot,
        include_diff=include_diff,
    )
    if round_dir.exists():
        if not existing_manifest:
            raise FileExistsError(f"round already exists without round_manifest.json: {round_dir}")
        if _manifest_for_compare(existing_manifest) == _manifest_for_compare(manifest):
            return {
                "round_id": round_dir.name,
                "round_dir": _path_for_json(round_dir),
                "copied": [],
                "manifest": _path_for_json(round_dir / "round_manifest.json"),
                "status": "no-op",
            }
        raise FileExistsError(f"round manifest differs; refusing to overwrite: {round_dir}")

    round_dir.mkdir(parents=True, exist_ok=False)
    copied: list[str] = []
    for name, data in files.items():
        (round_dir / name).write_bytes(data)
        copied.append(name)
    _write_json(round_dir / "round_manifest.json", manifest)
    return {
        "round_id": round_dir.name,
        "round_dir": _path_for_json(round_dir),
        "copied": copied,
        "manifest": _path_for_json(round_dir / "round_manifest.json"),
        "status": "created",
    }


def _latest_round_dir(state_dir: Path) -> Path | None:
    rounds_dir = state_dir / "rounds"
    if not rounds_dir.exists():
        return None
    rounds = [path for path in rounds_dir.iterdir() if path.is_dir() and path.name.startswith("round_")]
    return _latest_path(rounds)


def pack_context(*, state_dir: Path, out_path: Path) -> dict[str, Any]:
    ensure_state_layout(state_dir)
    archive_root = "project_state"
    allowed_files: list[tuple[Path, str]] = []
    for name in ARCHIVE_STATE_NAMES:
        path = state_dir / name
        if path.exists():
            allowed_files.append((path, f"{archive_root}/{name}"))
    latest_round = _latest_round_dir(state_dir)
    if latest_round:
        for name in ("pytest_result.txt", "git_diff.patch"):
            path = latest_round / name
            if path.exists():
                allowed_files.append((path, f"{archive_root}/rounds/{latest_round.name}/{name}"))

    out_path.parent.mkdir(parents=True, exist_ok=True) if out_path.parent != Path("") else None
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, arcname in allowed_files:
            archive.write(path, arcname=arcname)
    return {
        "out": _path_for_json(out_path),
        "files": [arcname for _, arcname in allowed_files],
    }


def status_summary(*, state_dir: Path) -> dict[str, Any]:
    artifact_index = _read_json(state_dir / "artifact_index.json")
    model_gate = _read_json(state_dir / "model_gate.json")
    task_packet = _read_json(state_dir / "task_packet.json")
    current_state = _read_json(state_dir / "current_state.json")
    task = task_packet.get("task")
    handoff_status = build_handoff_status(state_dir)
    decision = handoff_status["decision"]
    codex_report = handoff_status["codex_report"]
    handoff_consistency = handoff_status["handoff_consistency"]
    pytest_text = _read_text_or_empty(state_dir / "pytest_result.txt")
    pytest_validation = validate_pytest_result_for_report(pytest_text, codex_report)
    round_consistency = build_round_consistency(
        decision=decision,
        report=codex_report,
        current_state=current_state,
        task_packet=task_packet,
        state_dir=state_dir,
    )
    artifact_freshness = _artifact_freshness_counts(artifact_index)
    artifact_freshness_classification = _classify_artifact_freshness(
        freshness=artifact_freshness,
        decision=decision,
        report=codex_report,
        decision_execution_state=str(handoff_consistency.get("decision_execution_state") or "UNKNOWN"),
        round_consistency=round_consistency,
        pytest_validation=pytest_validation,
    )
    state_package_classification = build_state_package_classification(state_dir)
    return {
        "state_dir": _path_for_json(state_dir),
        "latest_harness_run": artifact_index.get("latest_harness_run"),
        "missing": artifact_index.get("missing", []),
        "artifact_freshness": artifact_freshness,
        "artifact_freshness_classification": artifact_freshness_classification["classification"],
        "artifact_freshness_blocking": artifact_freshness_classification["blocking"],
        "state_package_classification": state_package_classification,
        "state_package_classification_summary": state_package_classification["summary"],
        "state_package_classification_status": state_package_classification["status"],
        "should_call_model": model_gate.get("should_call_model"),
        "context_level": model_gate.get("context_level"),
        "model_gate_reason": model_gate.get("reason"),
        "harness_diagnostics": model_gate.get("harness_diagnostics"),
        "task": task,
        "state_scope": task_packet.get("state_scope", STATE_SCOPE_SAMPLE),
        "task_source": task_packet.get("task_source", TASK_SOURCE_DERIVED_FROM_SAMPLE_ARTIFACTS),
        "derived_task": task_packet.get("derived_task", task),
        "active_decision_packet": task_packet.get("active_decision_packet", ACTIVE_DECISION_PACKET),
        "execution_scope": task_packet.get(
            "execution_scope",
            EXECUTION_SCOPE_DECISION_PACKET_CONTROLS_CURRENT_ROUND,
        ),
        "expected_gpt_output": task_packet.get("expected_gpt_output", ACTIVE_DECISION_PACKET),
        "handoff_status": handoff_status,
        "decision_status": decision.get("status"),
        "decision_id": decision.get("decision_id"),
        "decision_based_on_state_digest": decision.get("based_on_state_digest"),
        "decision_parse_error": decision.get("parse_error"),
        "report_status": codex_report.get("status"),
        "report_acceptance_recommendation": codex_report.get("acceptance_recommendation"),
        "report_id": codex_report.get("report_id"),
        "report_based_on_decision_id": codex_report.get("based_on_decision_id"),
        "report_parse_error": codex_report.get("parse_error"),
        "pytest_result_status": pytest_validation.get("status"),
        "pytest_result_decision_id": pytest_validation.get("decision_id"),
        "pytest_result_report_id": pytest_validation.get("report_id"),
        "pytest_result_round_id": pytest_validation.get("round_id"),
        "pytest_result_matches_report": pytest_validation.get("matches_report"),
        "report_tests_ran_count": pytest_validation.get("report_tests_ran_count"),
        "pytest_result_tests_ran_count": pytest_validation.get("pytest_result_tests_ran_count"),
        "pytest_result_tests_cover_report": pytest_validation.get("tests_ran_covers_report"),
        "pytest_result_missing_report_tests": pytest_validation.get("missing_report_tests"),
        "handoff_consistency": handoff_consistency,
        "decision_report_id_match": handoff_consistency.get("decision_report_id_match"),
        "decision_state_digest_match": handoff_consistency.get("decision_state_digest_match"),
        "decision_consumed_by_report": handoff_consistency.get("decision_consumed_by_report"),
        "decision_execution_state": handoff_consistency.get("decision_execution_state"),
        "decision_ready_for_execution": handoff_consistency.get("decision_ready_for_execution"),
        **round_consistency,
    }


def _print_status(summary: dict[str, Any]) -> None:
    print(f"state_dir: {summary.get('state_dir')}")
    print(f"latest_harness_run: {summary.get('latest_harness_run')}")
    print(f"missing: {summary.get('missing')}")
    print(f"artifact_freshness: {summary.get('artifact_freshness')}")
    print(f"artifact_freshness_classification: {summary.get('artifact_freshness_classification')}")
    print(f"artifact_freshness_blocking: {summary.get('artifact_freshness_blocking')}")
    print(f"state_package_classification_status: {summary.get('state_package_classification_status')}")
    print(f"state_package_classification: {summary.get('state_package_classification_summary')}")
    print(f"should_call_model: {summary.get('should_call_model')}")
    print(f"context_level: {summary.get('context_level')}")
    print(f"reason: {summary.get('model_gate_reason')}")
    diag = summary.get("harness_diagnostics")
    if diag:
        print(f"harness_diagnostics: {json.dumps(diag, default=str)}")
    print(f"task: {summary.get('task')}")
    print(f"state_scope: {summary.get('state_scope')}")
    print(f"task_source: {summary.get('task_source')}")
    print(f"derived_task: {summary.get('derived_task')}")
    print(f"active_decision_packet: {summary.get('active_decision_packet')}")
    print(f"execution_scope: {summary.get('execution_scope')}")
    print(f"expected_gpt_output: {summary.get('expected_gpt_output')}")
    print(f"decision_status: {summary.get('decision_status')}")
    print(f"decision_id: {summary.get('decision_id')}")
    print(f"decision_based_on_state_digest: {summary.get('decision_based_on_state_digest')}")
    print(f"decision_parse_error: {summary.get('decision_parse_error')}")
    print(f"report_status: {summary.get('report_status')}")
    print(f"report_acceptance_recommendation: {summary.get('report_acceptance_recommendation')}")
    print(f"report_id: {summary.get('report_id')}")
    print(f"report_based_on_decision_id: {summary.get('report_based_on_decision_id')}")
    print(f"report_parse_error: {summary.get('report_parse_error')}")
    print(f"pytest_result_status: {summary.get('pytest_result_status')}")
    print(f"pytest_result_decision_id: {summary.get('pytest_result_decision_id')}")
    print(f"pytest_result_report_id: {summary.get('pytest_result_report_id')}")
    print(f"pytest_result_round_id: {summary.get('pytest_result_round_id')}")
    print(f"pytest_result_matches_report: {summary.get('pytest_result_matches_report')}")
    print(f"report_tests_ran_count: {summary.get('report_tests_ran_count')}")
    print(f"pytest_result_tests_ran_count: {summary.get('pytest_result_tests_ran_count')}")
    print(f"pytest_result_tests_cover_report: {summary.get('pytest_result_tests_cover_report')}")
    print(f"pytest_result_missing_report_tests: {summary.get('pytest_result_missing_report_tests')}")
    print(f"decision_report_id_match: {summary.get('decision_report_id_match')}")
    print(f"decision_state_digest_match: {summary.get('decision_state_digest_match')}")
    print(f"decision_consumed_by_report: {summary.get('decision_consumed_by_report')}")
    print(f"decision_execution_state: {summary.get('decision_execution_state')}")
    print(f"decision_ready_for_execution: {summary.get('decision_ready_for_execution')}")
    print(f"report_round_id: {summary.get('report_round_id')}")
    print(f"decision_round_id: {summary.get('decision_round_id')}")
    print(f"current_state_round_id: {summary.get('current_state_round_id')}")
    print(f"current_state_scope: {summary.get('current_state_scope')}")
    print(f"report_decision_round_id_match: {summary.get('report_decision_round_id_match')}")
    print(f"report_current_state_round_relation: {summary.get('report_current_state_round_relation')}")
    print(f"round_manifest_present: {summary.get('round_manifest_present')}")
    print(f"archive_status: {summary.get('archive_status')}")
    print(f"round_manifest_path: {summary.get('round_manifest_path')}")
    print(f"round_manifest_files: {summary.get('round_manifest_files')}")
    print(f"round_manifest_forbidden_files: {summary.get('round_manifest_forbidden_files')}")
    print(
        "round_manifest_required_files_missing: "
        f"{summary.get('round_manifest_required_files_missing')}"
    )


def _print_lint_decision(result: dict[str, Any]) -> None:
    print("lint-decision: OK" if result.get("ok") else "lint-decision: FAILED")
    for error in result.get("errors") or []:
        print(f"error: {error}")
    for warning in result.get("warnings") or []:
        print(f"warning: {warning}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"decision_status: {result.get('decision_status')}")
    print(f"mainline: {result.get('mainline')}")
    print(f"skill_profiles: {result.get('skill_profiles')}")
    print(f"based_on_state_build_id: {result.get('based_on_state_build_id')}")
    print(f"based_on_state_digest: {result.get('based_on_state_digest')}")
    print(f"current_state_build_id: {result.get('current_state_build_id')}")
    print(f"current_state_digest: {result.get('current_state_digest')}")
    print(f"execution_scope: {result.get('execution_scope')}")
    print(f"active_decision_packet: {result.get('active_decision_packet')}")


def _print_lint_report(result: dict[str, Any]) -> None:
    print("lint-report: OK" if result.get("ok") else "lint-report: FAILED")
    for error in result.get("errors") or []:
        print(f"error: {error}")
    for warning in result.get("warnings") or []:
        print(f"warning: {warning}")
    print(f"report_id: {result.get('report_id')}")
    print(f"report_status: {result.get('report_status')}")
    print(f"acceptance_recommendation: {result.get('acceptance_recommendation')}")
    print(f"based_on_decision_id: {result.get('based_on_decision_id')}")
    print(f"decision_id: {result.get('decision_id')}")
    print(f"decision_report_id_match: {result.get('decision_report_id_match')}")
    print(f"round_id: {result.get('round_id')}")
    print(f"report_round_id: {result.get('report_round_id')}")
    print(f"decision_round_id: {result.get('decision_round_id')}")
    print(f"current_state_round_id: {result.get('current_state_round_id')}")
    print(f"current_state_scope: {result.get('current_state_scope')}")
    print(f"report_decision_round_id_match: {result.get('report_decision_round_id_match')}")
    print(f"report_current_state_round_relation: {result.get('report_current_state_round_relation')}")
    print(f"round_manifest_present: {result.get('round_manifest_present')}")
    print(f"archive_status: {result.get('archive_status')}")
    print(f"round_manifest_path: {result.get('round_manifest_path')}")
    print(f"round_manifest_files: {result.get('round_manifest_files')}")
    print(f"round_manifest_forbidden_files: {result.get('round_manifest_forbidden_files')}")
    print(
        "round_manifest_required_files_missing: "
        f"{result.get('round_manifest_required_files_missing')}"
    )
    print(f"tests_ran_count: {result.get('tests_ran_count')}")
    print(f"generated_artifacts_count: {result.get('generated_artifacts_count')}")
    print(f"verified_artifacts_count: {result.get('verified_artifacts_count')}")
    print(f"pytest_result_present: {result.get('pytest_result_present')}")
    print(f"pytest_result_status: {result.get('pytest_result_status')}")
    print(f"pytest_result_decision_id: {result.get('pytest_result_decision_id')}")
    print(f"pytest_result_report_id: {result.get('pytest_result_report_id')}")
    print(f"pytest_result_round_id: {result.get('pytest_result_round_id')}")
    print(f"pytest_result_matches_report: {result.get('pytest_result_matches_report')}")
    print(f"report_tests_ran_count: {result.get('report_tests_ran_count')}")
    print(f"pytest_result_tests_ran_count: {result.get('pytest_result_tests_ran_count')}")
    print(f"pytest_result_tests_cover_report: {result.get('pytest_result_tests_cover_report')}")
    print(f"pytest_result_missing_report_tests: {result.get('pytest_result_missing_report_tests')}")
    print(f"pytest_result_parse_error: {result.get('pytest_result_parse_error')}")


def _print_lint_handoff(result: dict[str, Any]) -> None:
    print("lint-handoff: OK" if result.get("ok") else "lint-handoff: FAILED")
    for error in result.get("errors") or []:
        print(f"error: {error}")
    for warning in result.get("warnings") or []:
        print(f"warning: {warning}")
    print(f"handoff_state: {result.get('handoff_state')}")
    print(f"decision_execution_state: {result.get('decision_execution_state')}")
    print(f"decision_ready_for_execution: {result.get('decision_ready_for_execution')}")
    print(f"decision_report_id_match: {result.get('decision_report_id_match')}")
    print(f"lint_decision_ok: {result.get('lint_decision_ok')}")
    print(f"lint_report_ok: {result.get('lint_report_ok')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build low-token project state packets.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Build project state JSON files.")
    build_parser.add_argument("--reports-dir", default=str(DEFAULT_REPORTS_DIR))
    build_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    build_parser.add_argument("--sample", default=DEFAULT_SAMPLE)
    build_parser.add_argument("--run-name", default="")
    build_parser.add_argument("--progress-log", default=str(DEFAULT_PROGRESS_LOG))
    build_parser.add_argument("--max-artifacts", type=int, default=20)

    new_round_parser = subparsers.add_parser("new-round", help="Initialize project_state workflow files.")
    new_round_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

    archive_parser = subparsers.add_parser("archive-round", help="Archive current project_state files.")
    archive_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    archive_parser.add_argument("--round-id", default="")
    archive_parser.add_argument("--pytest-result", default="")
    archive_parser.add_argument("--include-state-snapshot", action="store_true")
    archive_parser.add_argument("--include-diff", action="store_true")

    pack_parser = subparsers.add_parser("pack", help="Pack compact GPT context files.")
    pack_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    pack_parser.add_argument("--out", default=DEFAULT_PACK_NAME)

    status_parser = subparsers.add_parser("status", help="Print concise project_state status.")
    status_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

    lint_decision_parser = subparsers.add_parser("lint-decision", help="Lint the active decision packet.")
    lint_decision_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

    lint_report_parser = subparsers.add_parser("lint-report", help="Lint the active Codex execution report.")
    lint_report_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

    lint_handoff_parser = subparsers.add_parser("lint-handoff", help="Lint aggregate handoff health.")
    lint_handoff_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostic checks on project state.")
    doctor_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    doctor_parser.add_argument("--json", action="store_true", help="Output JSON instead of text.")

    args = parser.parse_args(argv)
    if args.command == "build":
        build_project_state(
            reports_dir=Path(args.reports_dir),
            state_dir=Path(args.state_dir),
            sample=str(args.sample),
            run_name=str(args.run_name or ""),
            progress_log=Path(args.progress_log),
            max_artifacts=max(0, int(args.max_artifacts)),
        )
        return 0
    if args.command == "new-round":
        new_round(state_dir=Path(args.state_dir))
        return 0
    if args.command == "archive-round":
        archive_round(
            state_dir=Path(args.state_dir),
            round_id=str(args.round_id or ""),
            pytest_result=Path(args.pytest_result) if args.pytest_result else None,
            include_state_snapshot=bool(args.include_state_snapshot),
            include_diff=bool(args.include_diff),
        )
        return 0
    if args.command == "pack":
        pack_context(state_dir=Path(args.state_dir), out_path=Path(args.out))
        return 0
    if args.command == "status":
        _print_status(status_summary(state_dir=Path(args.state_dir)))
        return 0
    if args.command == "lint-decision":
        result = lint_decision(state_dir=Path(args.state_dir))
        _print_lint_decision(result)
        return 0 if result.get("ok") else 1
    if args.command == "lint-report":
        result = lint_report(state_dir=Path(args.state_dir))
        _print_lint_report(result)
        return 0 if result.get("ok") else 1
    if args.command == "lint-handoff":
        result = lint_handoff(state_dir=Path(args.state_dir))
        _print_lint_handoff(result)
        return 0 if result.get("ok") else 1
    if args.command == "doctor":
        result = doctor(state_dir=Path(args.state_dir), json_output=bool(args.json))
        return 0 if result["status"] in {"PASS", "WARN"} else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
