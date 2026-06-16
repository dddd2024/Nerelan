"""Pause-aware runtime evidence review for cpp1_2f6fcb63.

This module reads the existing runtime boundary probe artifact and produces
a pause-aware classification of each probe's output, without re-executing
the sample.  It is a thin parser/classifier invoked by the gate pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SUCCESS_MARKERS = [
    "congratulations",
    "you are right",
    "correct",
    "success!",
]

FAILURE_MARKERS = [
    "wrong",
    "fail",
    "invalid",
    "incorrect",
    "error",
]

PAUSE_MARKERS = [
    "press any key to continue",
]

CLASSIFICATION_VALUES = frozenset({
    "SUCCESS_MARKER_SEEN",
    "FAILURE_MARKER_SEEN",
    "PAUSE_ONLY_TIMEOUT",
    "NO_DECISIVE_MARKER",
    "MIXED_MARKERS",
})


def _classify_probe(
    success_marker_seen: bool,
    failure_marker_seen: bool,
    timeout: bool,
    stdout_text: str,
) -> str:
    """Classify a single probe based on its markers and output."""
    has_pause = any(m in stdout_text.lower() for m in PAUSE_MARKERS)
    has_success = success_marker_seen or any(m in stdout_text.lower() for m in SUCCESS_MARKERS)
    has_failure = failure_marker_seen or any(m in stdout_text.lower() for m in FAILURE_MARKERS)

    if has_success and has_failure:
        return "MIXED_MARKERS"
    if has_success:
        return "SUCCESS_MARKER_SEEN"
    if has_failure:
        return "FAILURE_MARKER_SEEN"
    if timeout and has_pause and not has_success and not has_failure:
        return "PAUSE_ONLY_TIMEOUT"
    return "NO_DECISIVE_MARKER"


def _determine_preview_status(
    per_probe: dict,
    runtime_validated: bool,
) -> str:
    """Determine the overall current_preview_status."""
    if runtime_validated:
        return "SUCCESS_CONFIRMED"
    classifications = {v["classification"] for v in per_probe.values()}
    if "SUCCESS_MARKER_SEEN" in classifications:
        return "SUCCESS_CONFIRMED"
    if "MIXED_MARKERS" in classifications:
        return "MIXED_OUTPUT_NEEDS_TOOL_RECHECK"
    if "FAILURE_MARKER_SEEN" in classifications:
        return "REJECTED_BY_RUNTIME_OUTPUT"
    return "INCONCLUSIVE_NO_DECISIVE_MARKER"


def review(
    runtime_boundary_path: Path,
    target_revalidation_path: Path,
    success_boundary_path: Path,
    artifact_index_path: Path,
    output_path: Path,
    decision_id: str = "",
    round_id: str = "",
) -> dict:
    """Produce a pause-aware runtime evidence review artifact."""
    runtime_boundary = json.loads(runtime_boundary_path.read_text(encoding="utf-8"))
    target_revalidation = json.loads(target_revalidation_path.read_text(encoding="utf-8"))
    success_boundary = json.loads(success_boundary_path.read_text(encoding="utf-8"))

    sample_id = runtime_boundary.get("sample_id", "")
    relative_path = runtime_boundary.get("relative_path", "")
    sha256 = runtime_boundary.get("sha256", "")

    # Classify each probe
    per_probe: dict[str, dict] = {}
    success_markers_found: list[str] = []
    failure_markers_found: list[str] = []
    pause_markers_found: list[str] = []

    for probe in runtime_boundary.get("probes", []):
        name = probe.get("probe_name", "unknown")
        stdout_text = probe.get("stdout_preview", "")
        classification = _classify_probe(
            success_marker_seen=probe.get("success_marker_seen", False),
            failure_marker_seen=probe.get("failure_marker_seen", False),
            timeout=probe.get("timeout", False),
            stdout_text=stdout_text,
        )
        per_probe[name] = {
            "probe_name": name,
            "stdin_hex": probe.get("stdin_hex", ""),
            "timeout": probe.get("timeout", False),
            "exit_code": probe.get("exit_code"),
            "success_marker_seen": probe.get("success_marker_seen", False),
            "failure_marker_seen": probe.get("failure_marker_seen", False),
            "pause_marker_seen": any(m in stdout_text.lower() for m in PAUSE_MARKERS),
            "classification": classification,
        }
        if probe.get("success_marker_seen"):
            success_markers_found.append(name)
        if probe.get("failure_marker_seen"):
            failure_markers_found.append(name)
        if any(m in stdout_text.lower() for m in PAUSE_MARKERS):
            pause_markers_found.append(name)

    runtime_validated = any(
        p.get("classification") == "SUCCESS_MARKER_SEEN" for p in per_probe.values()
    )

    current_preview_status = _determine_preview_status(per_probe, runtime_validated)

    static_boundary_contradicted = False
    if runtime_validated and success_boundary.get("compare_loop_exit_reason_review", {}).get(
        "status", ""
    ) not in ("current_payload_not_success_boundary_safe",):
        static_boundary_contradicted = True

    # Build recommended next action
    if current_preview_status == "REJECTED_BY_RUNTIME_OUTPUT":
        recommended_next_action = (
            "Use a separate tool_integration/static-debugger decision to inspect why the "
            "success boundary fails: specifically, determine the actual value of Destination[16] "
            "after the transform loop for a candidate input, and whether byte_429A30[16]==0x00 "
            "creates an unavoidable match that prevents i==16 exit. Do not rerun the same payloads. "
            "Consider patching system('pause') out of the binary for clean runtime testing, "
            "or using a debugger script to set a breakpoint at the compare loop."
        )
    elif current_preview_status == "SUCCESS_CONFIRMED":
        recommended_next_action = (
            "Runtime output confirms success. Proceed with candidate confirmation."
        )
    elif current_preview_status == "MIXED_OUTPUT_NEEDS_TOOL_RECHECK":
        recommended_next_action = (
            "Mixed markers in output. Use a debugger or patched binary to disambiguate."
        )
    else:
        recommended_next_action = (
            "No decisive marker found. Use a debugger or patched binary to capture "
            "clean output before the pause loop."
        )

    stop_conditions = [
        "Do not rerun CPP1.exe with the same payloads that already timed out.",
        "Do not treat timeout alone as success or failure; only captured markers are decisive.",
        "Do not mark CPP1 as solved or runtime_validated without an exact success marker.",
        "Do not repeat the printable inverse path unless target bytes or transform semantics change.",
        "Do not modify project_gate.py in the next round unless an engineering_branch decision explicitly authorizes it.",
        "Before any new runtime validation, first resolve the Destination[16] success boundary contradiction.",
        "If a new runtime campaign is proposed, use a separate decision that patches out system('pause') or uses debugger/console automation.",
    ]

    artifact = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "sample_id": sample_id,
        "relative_path": relative_path,
        "sha256": sha256,
        "analysis_mode": "pause_aware_runtime_evidence_review",
        "mainline": "reverse_solving",
        "source_artifacts": {
            "runtime_boundary_probe": str(runtime_boundary_path),
            "target_revalidation": str(target_revalidation_path),
            "success_boundary_static_recheck": str(success_boundary_path),
        },
        "source_artifact_freshness": {
            "runtime_boundary_probe": {
                "artifact_key": "local_reverse_cpp1_2f6fcb63_runtime_boundary_probe",
                "path": str(runtime_boundary_path),
                "freshness": "current",
                "source_run": runtime_boundary.get("round_id", ""),
                "sample_id": sample_id,
            },
            "target_revalidation": {
                "artifact_key": "local_reverse_cpp1_2f6fcb63_target_bytes_revalidation",
                "path": str(target_revalidation_path),
                "freshness": "current",
                "source_run": target_revalidation.get("round_id", ""),
                "sample_id": sample_id,
            },
            "success_boundary_static_recheck": {
                "artifact_key": "local_reverse_cpp1_2f6fcb63_success_boundary_static_recheck",
                "path": str(success_boundary_path),
                "freshness": "current",
                "source_run": success_boundary.get("round_id", ""),
                "sample_id": sample_id,
            },
        },
        "executed_sample": False,
        "reviewed_prior_runtime_execution": True,
        "runtime_validated": runtime_validated,
        "success_markers": success_markers_found,
        "failure_markers": failure_markers_found,
        "pause_markers": pause_markers_found,
        "per_probe_classification": per_probe,
        "candidate_bytes_hex": None,
        "candidate_text": None,
        "current_preview_status": current_preview_status,
        "static_boundary_contradicted": static_boundary_contradicted,
        "recommended_next_action": recommended_next_action,
        "stop_conditions_for_next_round": stop_conditions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pause-aware runtime evidence review for cpp1_2f6fcb63"
    )
    parser.add_argument(
        "--runtime-boundary",
        type=Path,
        required=True,
        help="Path to runtime boundary probe artifact JSON",
    )
    parser.add_argument(
        "--target-revalidation",
        type=Path,
        required=True,
        help="Path to target bytes revalidation artifact JSON",
    )
    parser.add_argument(
        "--success-boundary",
        type=Path,
        required=True,
        help="Path to success boundary static recheck artifact JSON",
    )
    parser.add_argument(
        "--artifact-index",
        type=Path,
        required=True,
        help="Path to artifact_index.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for the review artifact JSON",
    )
    parser.add_argument("--decision-id", default="", help="Current decision_id")
    parser.add_argument("--round-id", default="", help="Current round_id")
    args = parser.parse_args()

    result = review(
        runtime_boundary_path=args.runtime_boundary,
        target_revalidation_path=args.target_revalidation,
        success_boundary_path=args.success_boundary,
        artifact_index_path=args.artifact_index,
        output_path=args.out,
        decision_id=args.decision_id,
        round_id=args.round_id,
    )
    print(f"pause_aware_runtime_review: {result['current_preview_status']}")
    print(f"runtime_validated: {result['runtime_validated']}")
    print(f"artifact: {args.out}")


if __name__ == "__main__":
    main()
