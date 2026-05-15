from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .function_semantics import FUNCTION_SEMANTIC_AUDIT_FILE_NAME


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
    "compare_lhs_producer_audit": "compare_lhs_producer_audit.json",
    "compare_lhs_upstream_writer_audit": "compare_lhs_upstream_writer_audit.json",
    "compare_callsite_reanchor_and_lhs_provenance_audit": (
        "compare_callsite_reanchor_and_lhs_provenance_audit.json"
    ),
    "compare_real_lhs_provenance_audit": "compare_real_lhs_provenance_audit.json",
    "compare_esi_source_window_audit": "compare_esi_source_window_audit.json",
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
    "compare_lhs_producer_audit",
    "compare_lhs_upstream_writer_audit",
    "compare_callsite_reanchor_and_lhs_provenance_audit",
    "compare_real_lhs_provenance_audit",
    "compare_esi_source_window_audit",
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
DEFAULT_STATE_DIR = Path("project_state")
DEFAULT_SAMPLE = "samplereverse"
DEFAULT_REPORTS_DIR = Path("solve_reports")
DEFAULT_PROGRESS_LOG = Path("PROJECT_PROGRESS_LOG.txt")
DEFAULT_PACK_NAME = "gpt_context_pack.zip"

DECISION_PACKET_TEMPLATE = """# DECISION_PACKET

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

CODEX_EXECUTION_REPORT_TEMPLATE = """# CODEX_EXECUTION_REPORT

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


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _is_missing_or_default(path: Path, default_content: str) -> bool:
    if not path.exists():
        return True
    try:
        current = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return not current or current == default_content.strip()


def ensure_state_layout(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    rounds_dir = state_dir / "rounds"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    (rounds_dir / ".gitkeep").touch()
    readme_path = state_dir / "README.md"
    if _is_missing_or_default(readme_path, PROJECT_STATE_README):
        _write_text(readme_path, PROJECT_STATE_README)
    decision_path = state_dir / "decision_packet.md"
    if _is_missing_or_default(decision_path, DECISION_PACKET_TEMPLATE):
        _write_text(decision_path, DECISION_PACKET_TEMPLATE)
    report_path = state_dir / "codex_execution_report.md"
    if _is_missing_or_default(report_path, CODEX_EXECUTION_REPORT_TEMPLATE):
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


def _resolve_latest_run(reports_dir: Path, run_name: str = "") -> Path | None:
    harness_root = reports_dir / "harness_runs"
    if not harness_root.exists():
        return None
    if run_name:
        run_dir = harness_root / run_name
        return run_dir if run_dir.exists() and run_dir.is_dir() else None
    run_dirs = [item for item in harness_root.iterdir() if item.is_dir()]
    return _latest_path(run_dirs)


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
    if real_lhs_provenance_classification:
        stage = "compare_real_lhs_provenance_audit"
        reason = real_lhs_provenance_classification
    esi_source_window_classification = str(
        compare_esi_source_window_audit.get("classification") or ""
    ).strip()
    if esi_source_window_classification:
        stage = "compare_esi_source_window_audit"
        reason = esi_source_window_classification
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
        results.append(
            {
                "direction": "rerun Base64/RC4 breakpoint probe after material hook runtime validation blocked it",
                "scope": "material_hook_runtime_validation",
                "severity": "soft_block",
                "do_not_repeat": True,
                "reason": (
                    "0x233d/0x2346 did not confirm instruction-backed, candidate-dependent transform material; "
                    "Base64/RC4 probing remains gated until a different material hook is validated"
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
    if _summary_has_errors(str(latest_summary) if latest_summary else None) or _case_results_have_errors(
        [str(item) for item in case_paths]
    ):
        return {
            "should_call_model": False,
            "context_level": 1,
            "reason": "latest harness case has errors",
            "recommended_packet": "project_state/task_packet.json",
            "next_local_action": "inspect_failed_case_result",
            "missing_evidence": [],
            "generated_at": _now_iso(),
        }

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
    text = f"{stage} {reason}".lower()
    has_exact1 = isinstance(best_candidates.get("exact1"), dict) and bool(best_candidates.get("exact1"))
    if stage == "compare_real_lhs_provenance_audit" and reason == "lhs_register_source_confirmed":
        return "Trace ESI source window 0x2559..0x258b"
    if stage == "compare_esi_source_window_audit" and reason == "esi_source_identified":
        return "Promote identified ESI source into bounded material-hook validation"
    if stage == "compare_esi_source_window_audit":
        return "Investigate stalled ESI source window path"
    if ("exact1" in text and ("pair" in text or "projected" in text)) or (has_exact1 and "pair" in text):
        return "Generate next decision for exact1 pair_pool bottleneck"
    if stage or reason:
        return f"Investigate stalled {stage or reason} path"
    return "collect_missing_evidence"


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
        return {
            "task": "collect_missing_evidence",
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
            "next_local_action": model_gate.get("next_local_action"),
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
            "expected_gpt_output": "project_state/decision_packet.md",
            "generated_at": _now_iso(),
        }

    return {
        "task": _task_from_bottleneck(current_state),
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
        "expected_gpt_output": "project_state/decision_packet.md",
        "generated_at": _now_iso(),
    }


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
    model_gate = build_model_gate(artifact_index=artifact_index, current_state=current_state)
    task_packet = build_task_packet(
        current_state=current_state,
        negative_results=negative_results,
        model_gate=model_gate,
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
        candidate = rounds_dir / round_id
        if candidate.exists():
            raise FileExistsError(f"round already exists: {candidate}")
        return candidate
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


def archive_round(
    *,
    state_dir: Path,
    round_id: str = "",
    pytest_result: Path | None = None,
) -> dict[str, Any]:
    ensure_state_layout(state_dir)
    round_dir = _resolve_round_dir(state_dir, round_id=round_id)
    round_dir.mkdir(parents=True, exist_ok=False)
    copied: list[str] = []
    for name in ARCHIVE_STATE_NAMES:
        src = state_dir / name
        dst = round_dir / name
        if src.exists():
            dst.write_bytes(src.read_bytes())
            copied.append(name)
    _write_text(round_dir / "git_diff.patch", _git_diff_text())
    result_src = pytest_result or (state_dir / "pytest_result.txt")
    if result_src.exists():
        (round_dir / "pytest_result.txt").write_bytes(result_src.read_bytes())
    else:
        _write_text(round_dir / "pytest_result.txt", "No pytest_result.txt was available for this round.")
    return {
        "round_id": round_dir.name,
        "round_dir": _path_for_json(round_dir),
        "copied": copied,
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
    return {
        "state_dir": _path_for_json(state_dir),
        "latest_harness_run": artifact_index.get("latest_harness_run"),
        "missing": artifact_index.get("missing", []),
        "should_call_model": model_gate.get("should_call_model"),
        "context_level": model_gate.get("context_level"),
        "model_gate_reason": model_gate.get("reason"),
        "task": task_packet.get("task"),
        "expected_gpt_output": task_packet.get("expected_gpt_output", "project_state/decision_packet.md"),
    }


def _print_status(summary: dict[str, Any]) -> None:
    print(f"state_dir: {summary.get('state_dir')}")
    print(f"latest_harness_run: {summary.get('latest_harness_run')}")
    print(f"missing: {summary.get('missing')}")
    print(f"should_call_model: {summary.get('should_call_model')}")
    print(f"context_level: {summary.get('context_level')}")
    print(f"reason: {summary.get('model_gate_reason')}")
    print(f"task: {summary.get('task')}")
    print(f"expected_gpt_output: {summary.get('expected_gpt_output')}")


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

    pack_parser = subparsers.add_parser("pack", help="Pack compact GPT context files.")
    pack_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    pack_parser.add_argument("--out", default=DEFAULT_PACK_NAME)

    status_parser = subparsers.add_parser("status", help="Print concise project_state status.")
    status_parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))

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
        )
        return 0
    if args.command == "pack":
        pack_context(state_dir=Path(args.state_dir), out_path=Path(args.out))
        return 0
    if args.command == "status":
        _print_status(status_summary(state_dir=Path(args.state_dir)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
