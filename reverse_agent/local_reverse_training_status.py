"""
Local Reverse Training Status Overlay
=====================================

Merges metadata inventory with existing solved/blocked/validated results
to produce a per-sample training status overlay and a prioritized evaluation queue.

This module does NOT:
- Upload original samples
- Run solvers or dynamic analysis
- Generate candidates or flags
- Create a third corpus scanner

It DOES:
- Read from local_reverse_inventory.json (metadata only)
- Read from validated_candidate_handoff.json (status overlay)
- Read from local_reverse_constraint_recovery_result.json (blocked/solved facts)
- Read from local_reverse_ida_solver_result.json (prior evidence)
- Read current console runtime validation artifacts from artifact_index.json
- Produce training_status.json, evaluation_queue.json, status_overlay.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INVENTORY = Path("project_state/local_reverse_inventory.json")
DEFAULT_GITHUB_INVENTORY = Path("training_materials/local_reverse/inventory.json")
DEFAULT_VALIDATED = Path("project_state/local_reverse_validated_candidate_handoff.json")
DEFAULT_CONSTRAINT = Path("project_state/local_reverse_constraint_recovery_result.json")
DEFAULT_SOLVER = Path("project_state/local_reverse_ida_solver_result.json")
DEFAULT_ARTIFACT_INDEX = Path("project_state/artifact_index.json")
DEFAULT_OUT = Path("project_state/local_reverse_training_status.json")
DEFAULT_QUEUE_OUT = Path("project_state/local_reverse_evaluation_queue.json")
DEFAULT_GITHUB_STATUS = Path("training_materials/local_reverse/status_overlay.json")

QUEUE_POLICY = "simple_static_first_unsolved_only"

TRAINING_STATUS_SOLVED = "solved"
TRAINING_STATUS_BLOCKED = "blocked"
TRAINING_STATUS_NEEDS_TRIAGE = "needs_triage"
TRAINING_STATUS_INVENTORY_ONLY = "inventory_only"

# Artifact key suffixes that indicate a static handoff / reextract / decompile artifact.
_STATIC_HANDOFF_SUFFIXES = (
    "local_reverse_affine_inverse_handoff",
    "local_reverse_targeted_static_reextraction_result",
)

_STATIC_ANALYSIS_SUFFIXES = (
    "local_reverse_affine_main0_targeted_ida_decompile",
    "local_reverse_affine_main_input_flow_reextract",
    "local_reverse_ida_evidence_",
    "local_reverse_ida_summary",
)

_STATIC_BLOCKED_ARTIFACT_PRIORITY = (
    ("target_provenance_recheck", 50),
    ("signed_transform_recheck", 40),
    ("transform_recheck", 30),
    ("inverse_handoff", 20),
    ("static_triage", 10),
    ("targeted_static_reextraction_result", 10),
    ("ida_decompile", 5),
    ("ida_evidence", 5),
    ("ida_summary", 5),
)

STATIC_TRIAGE_TARGET_EXTENSIONS = {
    ".exe",
    ".dll",
    ".sys",
    ".com",
    ".bin",
    ".dat",
    ".elf",
    ".so",
}

STATIC_TRIAGE_TARGET_FILE_TYPES = {"pe", "elf", "raw"}

STATIC_TRIAGE_EXCLUDED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".doc",
    ".docx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.json:
        status_result = build_training_status(
            inventory_path=Path(args.inventory),
            validated_path=Path(args.validated),
            constraint_path=Path(args.constraint_recovery),
            solver_result_path=Path(args.solver_result),
            artifact_index_path=Path(args.artifact_index),
            out_path=None,
            queue_out_path=None,
            github_status_path=None,
        )
        print(json.dumps({
            "schema_version": 1,
            "sample_count": status_result["sample_count"],
            "status_summary": status_result["status_summary"],
            "queue_policy": status_result["queue"].get("queue_policy", ""),
            "queue_item_count": len(status_result["queue"].get("items", [])),
            "source_inventory": str(args.inventory),
            "artifact_index": str(args.artifact_index),
            "writes_files": False,
        }, ensure_ascii=False, indent=2))
        return 0

    status_result = build_training_status(
        inventory_path=Path(args.inventory),
        validated_path=Path(args.validated),
        constraint_path=Path(args.constraint_recovery),
        solver_result_path=Path(args.solver_result),
        artifact_index_path=Path(args.artifact_index),
        out_path=Path(args.out),
        queue_out_path=Path(args.queue_out),
        github_status_path=Path(args.github_status_out) if args.github_status_out else None,
    )

    print(
        f"[training_status] samples={status_result['sample_count']} "
        f"solved={status_result['status_summary']['solved']} "
        f"blocked={status_result['status_summary']['blocked']} "
        f"needs_triage={status_result['status_summary']['needs_triage']} "
        f"inventory_only={status_result['status_summary']['inventory_only']}"
    )
    print(f"[training_status] status out: {status_result['status_out_path']}")
    print(f"[training_status] queue out: {status_result['queue_out_path']}")
    if status_result.get("github_status_path"):
        print(f"[training_status] github status: {status_result['github_status_path']}")
    print(f"[training_status] queue items: {len(status_result['queue']['items'])}")
    return 0


def build_training_status(
    inventory_path: Path,
    validated_path: Path,
    constraint_path: Path,
    solver_result_path: Path,
    artifact_index_path: Path = DEFAULT_ARTIFACT_INDEX,
    out_path: Path | None = DEFAULT_OUT,
    queue_out_path: Path | None = DEFAULT_QUEUE_OUT,
    github_status_path: Path | None = None,
) -> dict[str, Any]:
    inventory = _load_json(inventory_path, "inventory")
    validated_data = _load_json(validated_path, "validated_handoff")
    constraint_data = _load_json(constraint_path, "constraint_recovery")
    solver_data = _load_json(solver_result_path, "solver_result")

    # Build lookup maps from existing results
    # Map: sample_id (inventory format) -> status info
    solved_map = _build_solved_map(validated_data)
    blocked_map = _build_blocked_map(constraint_data)
    evidence_sources_map = _build_evidence_sources_map(solver_data, validated_path, constraint_path)

    # Runtime/probe overlays from artifact_index
    runtime_validation_map = _build_runtime_validation_overlay(artifact_index_path)
    runtime_blocked_map = _build_runtime_blocked_overlay(artifact_index_path)
    mature_backend_blocked_map = _build_mature_backend_blocked_overlay(artifact_index_path)
    static_handoff_map = _build_static_handoff_overlay(artifact_index_path)
    static_triage_success_map = _build_static_triage_success_overlay(artifact_index_path)
    static_tool_blocked_map = _build_static_tool_blocked_overlay(artifact_index_path)

    # Merge with inventory entries
    samples: list[dict[str, Any]] = []
    counts = {"solved": 0, "blocked": 0, "needs_triage": 0, "inventory_only": 0}

    for entry in inventory.get("entries", []):
        sample_id = entry["sample_id"]
        sha256 = entry.get("sha256", "")
        # Also try short digest (first 16 chars) for matching with older records
        short_id = sha256[:16]

        if sample_id in solved_map:
            status = TRAINING_STATUS_SOLVED
            info = solved_map[sample_id]
            counts["solved"] += 1
        elif sample_id in runtime_validation_map:
            status = TRAINING_STATUS_SOLVED
            info = runtime_validation_map[sample_id]
            counts["solved"] += 1
        elif sample_id in blocked_map:
            status = TRAINING_STATUS_BLOCKED
            info = blocked_map[sample_id]
            counts["blocked"] += 1
        elif short_id in solved_map:
            status = TRAINING_STATUS_SOLVED
            info = solved_map[short_id]
            counts["solved"] += 1
        elif short_id in runtime_validation_map:
            status = TRAINING_STATUS_SOLVED
            info = runtime_validation_map[short_id]
            counts["solved"] += 1
        elif short_id in blocked_map:
            status = TRAINING_STATUS_BLOCKED
            info = blocked_map[short_id]
            counts["blocked"] += 1
        # Priority: mature_backend_blocked > runtime_blocked > static_handoff
        elif sample_id in mature_backend_blocked_map:
            status = TRAINING_STATUS_BLOCKED
            info = mature_backend_blocked_map[sample_id]
            counts["blocked"] += 1
        elif sample_id in runtime_blocked_map:
            status = TRAINING_STATUS_BLOCKED
            info = runtime_blocked_map[sample_id]
            counts["blocked"] += 1
        elif sample_id in static_handoff_map:
            overlay = static_handoff_map[sample_id]
            status = overlay.get("training_status", TRAINING_STATUS_NEEDS_TRIAGE)
            info = overlay
            counts[status] = counts.get(status, 0) + 1
        elif sample_id in static_triage_success_map:
            status = TRAINING_STATUS_NEEDS_TRIAGE
            info = static_triage_success_map[sample_id]
            counts["needs_triage"] += 1
        elif sample_id in static_tool_blocked_map:
            status = TRAINING_STATUS_NEEDS_TRIAGE
            info = static_tool_blocked_map[sample_id]
            counts["needs_triage"] += 1
        else:
            status = TRAINING_STATUS_INVENTORY_ONLY
            info = {}
            counts["inventory_only"] += 1

        sample_entry = _build_sample_entry(entry, status, info, evidence_sources_map)
        samples.append(sample_entry)

    # Sort: solved first (for reference), then inventory_only for triage
    priority_order = {
        TRAINING_STATUS_SOLVED: 0,
        TRAINING_STATUS_BLOCKED: 1,
        TRAINING_STATUS_NEEDS_TRIAGE: 2,
        TRAINING_STATUS_INVENTORY_ONLY: 3,
    }
    samples.sort(key=lambda s: (priority_order.get(s["training_status"], 99), s.get("sample_id", "")))

    training_status = {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "source_inventory": str(inventory_path),
        "sample_count": len(samples),
        "status_summary": counts,
        "samples": samples,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(out_path, training_status)

    # Build evaluation queue (unsolved + inventory_only only)
    queue = _build_evaluation_queue(samples)
    if queue_out_path is not None:
        queue_out_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(queue_out_path, queue)

    github_status: dict[str, Any] | None = None
    if github_status_path:
        github_status = {
            "schema_version": 1,
            "generated_at": _now_iso(),
            "source_inventory_hint": "LOCAL_REVERSE_ROOT",
            "sample_count": len(samples),
            "status_summary": counts,
            "samples": [
                {
                    "sample_id": s["sample_id"],
                    "relative_path": s["relative_path"],
                    "category": s.get("category", "unknown"),
                    "tags": s.get("tags", []),
                    "training_status": s["training_status"],
                    "known_candidate": s.get("known_candidate", ""),
                    "blocked_reason": s.get("blocked_reason", ""),
                }
                for s in samples
            ],
        }
        github_status_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(github_status_path, github_status)

    return {
        "status_out_path": str(out_path) if out_path is not None else None,
        "queue_out_path": str(queue_out_path) if queue_out_path is not None else None,
        "github_status_path": str(github_status_path) if github_status_path else None,
        "sample_count": len(samples),
        "status_summary": counts,
        "queue": queue,
    }


def _build_solved_map(validated_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map sample_id -> solved info from validated candidates."""
    result: dict[str, dict[str, Any]] = {}
    for vc in validated_data.get("validated_candidates", []):
        sid = vc.get("sample_id", "")
        if vc.get("validation_status") == "validated":
            result[sid] = {
                "known_candidate": vc.get("candidate", ""),
                "source_relation": vc.get("source_relation", ""),
                "validation_status": "validated",
            }
    return result


def _build_blocked_map(constraint_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map sample_id -> blocked info from constraint recovery."""
    result: dict[str, dict[str, Any]] = {}
    for target in constraint_data.get("targets", []):
        sid = target.get("sample_id", "")
        if target.get("constraint_status") == "blocked":
            result[sid] = {
                "blocked_reason": target.get("blocked_reason", ""),
                "classification": target.get("classification", ""),
                "next_action": target.get("next_action", ""),
            }
    return result


def _build_runtime_validation_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for current successful console runtime validations."""
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue
        if meta.get("kind") != "local_reverse_console_runtime_validation":
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        known_candidate = artifact.get("known_candidate", "")
        if not sample_id or not known_candidate:
            continue
        if artifact.get("validation_status") != "VALIDATED_SUCCESS":
            continue
        if artifact.get("runtime_validated") is not True:
            continue
        if artifact.get("solved") is not True:
            continue

        overlay[sample_id] = {
            "known_candidate": known_candidate,
            "classification": artifact.get("analysis_mode", ""),
            "validation_status": artifact.get("validation_status", ""),
            "evidence_sources": [
                f"source:{artifact_path.name}",
                "console_runtime_validation",
                "runtime_validated_success",
            ],
            "next_action": "sample solved by current console runtime validation",
        }

    return overlay


def _build_runtime_blocked_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for current runtime validation artifacts that are blocked.

    Accepts artifacts with:
      - validation_status in (AMBIGUOUS_OUTPUT, VALIDATED_FAILURE, BLOCKED)
      - solved=False
      - blocked_reason present
    Does NOT produce known_candidate.
    """
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue
        kind = meta.get("kind", "")
        # Accept both direct runtime validation and pair runtime validation
        if kind not in ("local_reverse_console_runtime_validation", "local_reverse_console_pair_runtime_validation"):
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        if not sample_id:
            continue

        validation_status = artifact.get("validation_status", "")
        solved = artifact.get("solved", False)
        blocked_reason = artifact.get("blocked_reason", "")
        failure_reason = artifact.get("failure_reason", "")

        # Only accept non-success blocked states
        if validation_status not in ("AMBIGUOUS_OUTPUT", "VALIDATED_FAILURE", "BLOCKED"):
            continue
        if solved is not False:
            continue
        if not blocked_reason and not failure_reason:
            continue

        # Use blocked_reason, fallback to failure_reason, fallback to validation_status
        effective_blocked_reason = blocked_reason or failure_reason or validation_status

        overlay[sample_id] = {
            "training_status": TRAINING_STATUS_BLOCKED,
            "blocked_reason": effective_blocked_reason,
            "classification": artifact.get("analysis_mode", ""),
            "evidence_sources": [
                f"source:{artifact_path.name}",
                "console_runtime_validation",
                f"runtime_validation_status:{validation_status}",
            ],
            "next_action": f"resolve: {effective_blocked_reason}",
        }

    return overlay


def _build_mature_backend_blocked_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for current mature backend availability probe artifacts.

    Accepts artifacts with:
      - probe_status=BLOCKED_MATURE_BACKEND_MISSING
      - can_attempt_interactive_console_validation_next=False
      - solved=False
    """
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue
        kind = meta.get("kind", "")
        if kind != "local_reverse_console_mature_backend_availability_probe":
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        if not sample_id:
            continue

        probe_status = artifact.get("probe_status", "")
        can_attempt = artifact.get("can_attempt_interactive_console_validation_next", True)
        solved = artifact.get("solved", False)
        blocked_reason = artifact.get("blocked_reason", "")

        if probe_status != "BLOCKED_MATURE_BACKEND_MISSING":
            continue
        if can_attempt is not False:
            continue
        if solved is not False:
            continue
        if not blocked_reason:
            continue

        overlay[sample_id] = {
            "training_status": TRAINING_STATUS_BLOCKED,
            "blocked_reason": blocked_reason,
            "classification": artifact.get("analysis_mode", ""),
            "evidence_sources": [
                f"source:{artifact_path.name}",
                "console_mature_backend_probe",
                "mature_backend_missing",
            ],
            "next_action": f"resolve: {blocked_reason}",
        }

    return overlay


def _build_static_handoff_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for current static-blocked artifacts and build overlay map.

    Returns a map: sample_id -> overlay info dict with training_status, blocked_reason,
    classification, evidence_sources, next_action, cipher_type.
    """
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    overlay_priority: dict[str, int] = {}

    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        artifact_priority = _static_blocked_artifact_priority(key, meta, artifact)
        if artifact_priority is None:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        if not sample_id:
            continue

        # --- Strict acceptance gate for static handoff overlay ---
        # Only accept artifacts that are truly static-only blocked evidence.
        # Reject anything that claims to be solved, runtime-validated, or
        # has a candidate (static handoff must NOT produce solved/known_candidate).
        static_only = artifact.get("static_only", False)
        executed_sample = artifact.get("executed_sample", False)
        runtime_validated = artifact.get("runtime_validated", False)
        candidate = artifact.get("candidate")
        status = artifact.get("status", "")
        blocked_reason = artifact.get("blocked_reason", "")

        # Skip if not explicitly static-only
        if static_only is not True:
            continue
        # Skip if sample was executed (runtime evidence, not static)
        if executed_sample is not False:
            continue
        # Skip if runtime-validated (should go through validated candidate path)
        if runtime_validated is not False:
            continue
        # Skip if candidate is present (static handoff must not produce solved)
        if candidate is not None:
            continue
        # Skip if not BLOCKED with a reason
        if status != "BLOCKED" or not blocked_reason:
            continue

        # Extract metadata for classification and evidence
        cipher_type = artifact.get("cipher_type", "")
        analysis_mode = artifact.get("analysis_mode", "")
        provenance_verdict = artifact.get("provenance_verdict", "")
        confidence = artifact.get("confidence", "")
        recommended_next = artifact.get("recommended_next_action", "")

        # Build classification from artifact metadata
        classification_parts = []
        if cipher_type:
            classification_parts.append(cipher_type)
        if analysis_mode:
            classification_parts.append(analysis_mode.replace("targeted_", "").replace("_", " "))
        if provenance_verdict:
            classification_parts.append(provenance_verdict.lower())
        if blocked_reason:
            classification_parts.append(blocked_reason.lower())
        classification = " ".join(classification_parts) if classification_parts else ""

        # Static handoff overlay can only produce blocked, never solved
        training_status = TRAINING_STATUS_BLOCKED

        # Build evidence sources
        evidence_sources = [f"source:{artifact_path.name}", "static_handoff", "static_blocked_artifact"]
        if cipher_type:
            evidence_sources.append("static_cipher_analysis")
        if provenance_verdict:
            evidence_sources.append(f"provenance:{provenance_verdict}")
        if confidence:
            evidence_sources.append(f"confidence:{confidence}")

        # Determine next action
        next_action = recommended_next or f"resolve: {blocked_reason}"

        entry: dict[str, Any] = {
            "training_status": training_status,
            "blocked_reason": blocked_reason,
            "classification": classification,
            "evidence_sources": evidence_sources,
            "next_action": next_action,
        }

        existing_priority = overlay_priority.get(sample_id)
        if existing_priority is None or artifact_priority > existing_priority:
            overlay[sample_id] = entry
            overlay_priority[sample_id] = artifact_priority
        elif artifact_priority == existing_priority:
            existing = overlay[sample_id]
            for k, v in entry.items():
                if k not in existing or not existing.get(k):
                    existing[k] = v

    return overlay


def _build_static_tool_blocked_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for current static tool failures.

    Tool failures are evidence that a sample still needs triage, not evidence
    that the sample itself is semantically blocked.
    """
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue
        if meta.get("kind") != "local_reverse_single_sample_static_triage":
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        if not sample_id:
            continue

        if artifact.get("static_only") is not True:
            continue
        if artifact.get("executed_sample") is not False:
            continue
        if artifact.get("runtime_validated") is not False:
            continue
        if artifact.get("candidate") is not None:
            continue
        if artifact.get("tool_status") != "blocked":
            continue

        blocked_reason = artifact.get("blocked_reason", "")
        if not str(blocked_reason).startswith("STATIC_TOOL_"):
            continue

        source_tool = artifact.get("source_tool", "")
        evidence_sources = [
            f"source:{artifact_path.name}",
            "static_tool_blocked",
            "tool_status:blocked",
        ]
        if source_tool:
            evidence_sources.append(f"source_tool:{source_tool}")

        overlay[sample_id] = {
            "training_status": TRAINING_STATUS_NEEDS_TRIAGE,
            "blocked_reason": blocked_reason,
            "classification": artifact.get("analysis_mode", ""),
            "evidence_sources": evidence_sources,
            "next_action": f"resolve static tool blocker: {blocked_reason}",
        }

    return overlay


def _build_static_triage_success_overlay(
    artifact_index_path: Path,
) -> dict[str, dict[str, Any]]:
    """Scan artifact_index for successful current static triage artifacts.

    A successful static triage means the sample has enough current static
    evidence to leave the static-triage queue, but it is not solved until a
    later constraint-recovery or validation round proves a candidate.
    """
    if not artifact_index_path.exists():
        return {}

    artifact_index = _load_json(artifact_index_path, "artifact_index")
    v2 = artifact_index.get("latest_artifacts_v2", {})

    overlay: dict[str, dict[str, Any]] = {}
    for key, meta in v2.items():
        if meta.get("freshness") != "current":
            continue
        if meta.get("kind") != "local_reverse_single_sample_static_triage":
            continue

        artifact_path_text = meta.get("path", "")
        if not artifact_path_text:
            continue
        artifact_path = _resolve_artifact_path(artifact_path_text, artifact_index_path)

        artifact = _load_json(artifact_path, f"artifact:{key}")
        if not artifact:
            continue

        sample_id = artifact.get("sample_id") or meta.get("sample_id", "")
        if not sample_id:
            continue

        if artifact.get("static_only") is not True:
            continue
        if artifact.get("executed_sample") is not False:
            continue
        if artifact.get("runtime_validated") is not False:
            continue
        if artifact.get("candidate") is not None:
            continue
        if artifact.get("tool_status") != "success":
            continue

        triage = artifact.get("triage", {})
        triage = triage if isinstance(triage, dict) else {}
        hypotheses = triage.get("solver_profile_hypotheses", [])
        hypotheses = [str(item) for item in hypotheses if item]
        source_tool = artifact.get("source_tool", "")

        evidence_sources = [
            f"source:{artifact_path.name}",
            "static_triage_completed",
            "tool_status:success",
        ]
        if source_tool:
            evidence_sources.append(f"source_tool:{source_tool}")
        evidence_sources.extend(f"hypothesis:{item}" for item in hypotheses[:5])

        classification = "; ".join(hypotheses) or artifact.get("analysis_mode", "")
        overlay[sample_id] = {
            "training_status": TRAINING_STATUS_NEEDS_TRIAGE,
            "blocked_reason": "",
            "classification": classification,
            "evidence_sources": evidence_sources,
            "next_action": "constraint recovery or targeted decompilation; runtime validation required",
        }

    return overlay


def _resolve_artifact_path(artifact_path_text: str, artifact_index_path: Path) -> Path:
    artifact_path = Path(artifact_path_text)
    if artifact_path.is_absolute() or artifact_path.exists():
        return artifact_path

    index_relative_path = artifact_index_path.parent / artifact_path
    if index_relative_path.exists():
        return index_relative_path

    return artifact_path


def _static_blocked_artifact_priority(
    key: str,
    meta: dict[str, Any],
    artifact: dict[str, Any],
) -> int | None:
    """Return specificity priority for artifacts eligible for static-blocked overlay."""
    kind = str(meta.get("kind", ""))
    analysis_mode = str(artifact.get("analysis_mode", ""))
    artifact_type = str(artifact.get("artifact_type", ""))
    haystack = " ".join((key, kind, analysis_mode, artifact_type)).lower()

    for token, priority in _STATIC_BLOCKED_ARTIFACT_PRIORITY:
        if token in haystack:
            return priority

    if any(key.startswith(prefix) or kind.startswith(prefix) for prefix in _STATIC_HANDOFF_SUFFIXES):
        return 20
    if any(key.startswith(prefix) or kind.startswith(prefix) for prefix in _STATIC_ANALYSIS_SUFFIXES):
        return 5
    return None


def _build_evidence_sources_map(
    solver_data: dict[str, Any],
    validated_path: Path,
    constraint_path: Path,
) -> dict[str, list[str]]:
    """Map sample_id -> list of evidence source descriptions."""
    result: dict[str, dict[str, bool]] = {}
    for target in solver_data.get("targets", []):
        sid = target.get("sample_id", "")
        sources: dict[str, bool] = {}
        if target.get("classification"):
            sources["ida_solver_classification"] = True
        if target.get("validation_evidence"):
            sources["runtime_validation"] = True
        if sources:
            result[sid] = sources
    # Always include the validated and constraint files as sources
    for sid_dict in result.values():
        sid_dict[f"source:{validated_path.name}"] = True
        sid_dict[f"source:{constraint_path.name}"] = True
    return {k: list(v.keys()) for k, v in result.items()}


def _build_sample_entry(
    entry: dict[str, Any],
    status: str,
    info: dict[str, Any],
    evidence_sources_map: dict[str, list[str]],
) -> dict[str, Any]:
    sample_id = entry["sample_id"]
    sha256 = entry.get("sha256", "")
    short_id = sha256[:16]

    # Prefer entry's own sample_id, fall back to short_id for lookup
    sources = evidence_sources_map.get(sample_id, evidence_sources_map.get(short_id, []))

    # Merge overlay evidence sources if present
    overlay_sources = info.get("evidence_sources", [])
    if overlay_sources:
        merged_sources = list(sources)
        for s in overlay_sources:
            if s not in merged_sources:
                merged_sources.append(s)
        sources = merged_sources

    if status == TRAINING_STATUS_SOLVED:
        next_action = info.get("next_action", "inspect sub_40100A hook data flow and confirm file compare source")
    elif status == TRAINING_STATUS_BLOCKED:
        next_action = info.get("next_action", "resolve blocking constraint before proceeding")
    else:
        next_action = info.get("next_action", "static triage and manual evaluation required")

    return {
        "sample_id": sample_id,
        "relative_path": entry.get("relative_path", ""),
        "sha256": sha256,
        "size_bytes": entry.get("size_bytes", 0),
        "extension": entry.get("extension", ""),
        "guessed_file_type": entry.get("guessed_file_type", "unknown"),
        "category": entry.get("category", "unknown"),
        "tags": entry.get("tags", []),
        "training_status": status,
        "known_candidate": info.get("known_candidate", ""),
        "blocked_reason": info.get("blocked_reason", ""),
        "classification": info.get("classification", ""),
        "evidence_sources": sources,
        "next_action": next_action,
    }


def _build_evaluation_queue(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a prioritized evaluation queue from unsolved inventory_only samples."""
    # Priority rules:
    # 1. Exclude solved and blocked samples
    # 2. Exclude solver scripts and support files
    # 3. Prefer small PE / source challenges
    # 4. Prefer simple static categories: xor, shift, strcmp, array_compare, base64
    # 5. Defer hash题 unless bounded domain is known
    # 6. DES/RC4 as second batch
    SIMPLE_TAGS = {"xor", "shift", "strcmp", "serial_check", "array_compare", "base64"}
    SECOND_BATCH_TAGS = {"rc4", "des", "aes"}
    DEFERRED_TAGS = {"hash", "packed_or_obfuscated"}
    EXCLUDED_ROLES = {"solver_script", "support_file"}

    def queue_rank(sample: dict[str, Any]) -> tuple[int, int, str]:
        tags = set(sample.get("tags", []))
        category = sample.get("category", "")
        # Prefer PE samples
        is_pe = "pe" in tags or ".exe" in sample.get("relative_path", "")
        role_rank = 0 if is_pe else 1
        # Prefer simple static tags
        if SIMPLE_TAGS & tags:
            priority_rank = 0
        elif SECOND_BATCH_TAGS & tags:
            priority_rank = 1
        elif DEFERRED_TAGS & tags:
            priority_rank = 3
        else:
            priority_rank = 2
        size = sample.get("size_bytes", 0)
        return (priority_rank, role_rank, str(size))

    # First pass: collect all eligible samples with their priority info
    eligible: list[tuple[dict[str, Any], int]] = []  # (sample, priority_rank)
    for sample in samples:
        status = sample.get("training_status", "")
        if status != TRAINING_STATUS_INVENTORY_ONLY:
            continue
        tags = set(sample.get("tags", []))
        # Skip obvious solver scripts and support files.
        name = sample.get("sample_id", "").lower()
        rel = sample.get("relative_path", "").lower()
        if any(kw in name for kw in ("solver", "script", "decrypt", "encrypt")):
            continue
        if any(kw in rel for kw in ("solver", "script", "decrypt", "encrypt", "interactive")):
            continue
        if EXCLUDED_ROLES & tags:
            continue
        # Skip DES interactive solver and non-target support documents.
        if "des" in tags and "interactive" in rel:
            continue
        if not _is_static_triage_queue_target(sample):
            continue

        # Determine priority rank based on tags.
        if SIMPLE_TAGS & tags:
            priority_rank = 0
        elif SECOND_BATCH_TAGS & tags:
            priority_rank = 1
        elif DEFERRED_TAGS & tags:
            priority_rank = 3
        else:
            priority_rank = 2

        eligible.append((sample, priority_rank))

    # Sort by priority rank, then by sample_id for stability
    eligible.sort(key=lambda x: (x[1], x[0]["sample_id"]))

    # Build queue items
    queue_items: list[dict[str, Any]] = []
    for rank, (sample, _) in enumerate(eligible, 1):
        tags_list = list(set(sample.get("tags", [])))
        queue_items.append({
            "rank": rank,
            "sample_id": sample["sample_id"],
            "relative_path": sample["relative_path"],
            "reason": _queue_reason(sample, tags_list),
            "proposed_next_mainline": "tool_integration",
            "allowed_actions": ["static_triage"],
            "forbidden_actions": ["runtime_probe", "bruteforce", "upload_binary"],
        })

    # Re-rank after sort
    for i, item in enumerate(queue_items, 1):
        item["rank"] = i

    return {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "queue_policy": QUEUE_POLICY,
        "items": queue_items,
    }


def _is_static_triage_queue_target(sample: dict[str, Any]) -> bool:
    rel = str(sample.get("relative_path", ""))
    extension = str(sample.get("extension", "") or Path(rel).suffix).lower()
    guessed_file_type = str(sample.get("guessed_file_type", "")).lower()
    tags = {str(tag).lower() for tag in sample.get("tags", [])}

    if extension in STATIC_TRIAGE_EXCLUDED_EXTENSIONS:
        return False
    if extension in STATIC_TRIAGE_TARGET_EXTENSIONS:
        return True
    if guessed_file_type in STATIC_TRIAGE_TARGET_FILE_TYPES:
        return True
    if "pe" in tags or "elf" in tags:
        return True
    return False


def _extract_tags_from_reason(reason: str) -> list[str]:
    """Extract tag names from queue reason string."""
    known = ["xor", "shift", "strcmp", "array_compare", "base64", "rc4", "des", "aes", "hash", "packed_or_obfuscated"]
    return [t for t in known if t in reason.lower()]


def _propose_solver_family(tags: list[str]) -> str:
    tag_set = set(tags)
    if "xor" in tag_set or "array_compare" in tag_set:
        return "xor_array_static_solver"
    if "shift" in tag_set:
        return "shift_or_affine_static_solver"
    if "strcmp" in tag_set or "serial_check" in tag_set:
        return "string_compare_static_solver"
    if "base64" in tag_set:
        return "encoding_static_solver"
    if "rc4" in tag_set or "des" in tag_set or "aes" in tag_set:
        return "crypto_static_triage_plan"
    if "hash" in tag_set:
        return "hash_constant_static_solver"
    return "manual_static_triage"


def _queue_reason(sample: dict[str, Any], tags: list[str]) -> str:
    size = sample.get("size_bytes", 0)
    file_type = sample.get("guessed_file_type", "unknown")
    tag_str = ", ".join(tags[:4]) if tags else "unknown"
    return f"{file_type} sample ({size} bytes), static triage tags: {tag_str}"


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build training status overlay from metadata inventory and existing results."
    )
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY),
                        help="Path to local_reverse_inventory.json")
    parser.add_argument("--github-inventory", default=str(DEFAULT_GITHUB_INVENTORY),
                        help="Path to GitHub-safe inventory.json")
    parser.add_argument("--validated", default=str(DEFAULT_VALIDATED),
                        help="Path to local_reverse_validated_candidate_handoff.json")
    parser.add_argument("--constraint-recovery", default=str(DEFAULT_CONSTRAINT),
                        help="Path to local_reverse_constraint_recovery_result.json")
    parser.add_argument("--solver-result", default=str(DEFAULT_SOLVER),
                        help="Path to local_reverse_ida_solver_result.json")
    parser.add_argument("--artifact-index", default=str(DEFAULT_ARTIFACT_INDEX),
                        help="Path to artifact_index.json for static handoff overlay")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Path for local_reverse_training_status.json")
    parser.add_argument("--queue-out", default=str(DEFAULT_QUEUE_OUT),
                        help="Path for local_reverse_evaluation_queue.json")
    parser.add_argument("--github-status-out", default=str(DEFAULT_GITHUB_STATUS),
                        help="Path for GitHub-safe status_overlay.json")
    parser.add_argument("--json", action="store_true",
                        help="Print a read-only JSON summary without writing output files")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
