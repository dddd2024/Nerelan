"""
Local Reverse Training Review
=============================

Provides review capabilities for local reverse engineering training samples.
Supports two review types:
- completeness: Check if sample has all required metadata and artifacts
- quality: Evaluate the quality of training data and annotations

This module does NOT:
- Modify sample files or metadata
- Upload data to external systems
- Run solvers or dynamic analysis

It DOES:
- Read from local_reverse_training_status.json (status overlay)
- Read from local_reverse_inventory.json (metadata)
- Read from artifact_index.json (artifact tracking)
- Produce review reports with findings and recommendations
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reverse_agent.local_reverse_training_status import (
    TRAINING_STATUS_BLOCKED,
    TRAINING_STATUS_INVENTORY_ONLY,
    TRAINING_STATUS_NEEDS_TRIAGE,
    TRAINING_STATUS_SOLVED,
    build_training_status,
)

DEFAULT_TRAINING_STATUS = Path("project_state/local_reverse_training_status.json")
DEFAULT_INVENTORY = Path("project_state/local_reverse_inventory.json")
DEFAULT_ARTIFACT_INDEX = Path("project_state/artifact_index.json")
DEFAULT_OUT = Path("project_state/local_reverse_training_review_report.json")

REVIEW_TYPE_COMPLETENESS = "completeness"
REVIEW_TYPE_QUALITY = "quality"
VALID_REVIEW_TYPES = {REVIEW_TYPE_COMPLETENESS, REVIEW_TYPE_QUALITY}

# Severity levels for review findings
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    review_type = args.review_type
    if review_type not in VALID_REVIEW_TYPES:
        print(f"[review] Error: Invalid review type '{review_type}'. Valid types: {VALID_REVIEW_TYPES}")
        return 1

    # Build fresh training status if requested
    if args.refresh_status:
        print("[review] Refreshing training status...")
        build_training_status(
            inventory_path=Path(args.inventory),
            validated_path=Path(args.validated),
            constraint_path=Path(args.constraint_recovery),
            solver_result_path=Path(args.solver_result),
            artifact_index_path=Path(args.artifact_index),
            out_path=Path(args.training_status),
            queue_out_path=Path(args.queue_out) if args.queue_out else None,
        )

    # Load training status
    training_status = _load_json(Path(args.training_status), "training_status")
    if not training_status:
        print(f"[review] Error: Cannot load training status from {args.training_status}")
        return 1

    # Load inventory for additional metadata
    inventory = _load_json(Path(args.inventory), "inventory")

    # Load artifact index for artifact completeness checks
    artifact_index = _load_json(Path(args.artifact_index), "artifact_index")

    # Perform review
    if args.sample_id:
        # Single sample review
        result = review_sample(
            sample_id=args.sample_id,
            review_type=review_type,
            training_status=training_status,
            inventory=inventory,
            artifact_index=artifact_index,
        )
        findings = result.get("findings", [])
        print(f"[review] Sample: {args.sample_id}")
        print(f"[review] Review type: {review_type}")
        print(f"[review] Findings: {len(findings)}")
        for f in findings:
            print(f"  [{f['severity'].upper()}] {f['category']}: {f['message']}")
    elif args.sample_ids:
        # Batch review
        sample_ids = [s.strip() for s in args.sample_ids.split(",")]
        result = review_batch(
            sample_ids=sample_ids,
            review_type=review_type,
            training_status=training_status,
            inventory=inventory,
            artifact_index=artifact_index,
        )
        print(f"[review] Batch review complete: {len(sample_ids)} samples")
        print(f"[review] Total findings: {result.get('total_findings', 0)}")
    else:
        # Full review report
        result = generate_review_report(
            review_type=review_type,
            training_status=training_status,
            inventory=inventory,
            artifact_index=artifact_index,
        )
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(out_path, result)
        print(f"[review] Review report generated: {out_path}")
        print(f"[review] Samples reviewed: {result.get('samples_reviewed', 0)}")
        print(f"[review] Total findings: {result.get('total_findings', 0)}")
        print(f"[review] Critical/High findings: {result.get('critical_high_count', 0)}")

    return 0


def review_sample(
    sample_id: str,
    review_type: str,
    training_status: dict[str, Any],
    inventory: dict[str, Any],
    artifact_index: dict[str, Any],
) -> dict[str, Any]:
    """Review a single sample for completeness or quality issues.

    Args:
        sample_id: The sample ID to review
        review_type: Either "completeness" or "quality"
        training_status: Loaded training_status.json content
        inventory: Loaded inventory.json content
        artifact_index: Loaded artifact_index.json content

    Returns:
        Dict with review results including findings list
    """
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review type: {review_type}")

    # Find sample in training status
    sample = _find_sample_in_status(sample_id, training_status)
    if not sample:
        return {
            "sample_id": sample_id,
            "review_type": review_type,
            "findings": [
                {
                    "severity": SEVERITY_CRITICAL,
                    "category": "missing_sample",
                    "message": f"Sample '{sample_id}' not found in training status",
                }
            ],
        }

    # Find sample in inventory for additional metadata
    inventory_entry = _find_sample_in_inventory(sample_id, inventory)

    if review_type == REVIEW_TYPE_COMPLETENESS:
        findings = _check_completeness(sample, inventory_entry, artifact_index)
    else:  # REVIEW_TYPE_QUALITY
        findings = _check_quality(sample, inventory_entry, artifact_index)

    return {
        "sample_id": sample_id,
        "review_type": review_type,
        "training_status": sample.get("training_status"),
        "findings": findings,
        "finding_count": len(findings),
    }


def review_batch(
    sample_ids: list[str],
    review_type: str,
    training_status: dict[str, Any],
    inventory: dict[str, Any],
    artifact_index: dict[str, Any],
) -> dict[str, Any]:
    """Review multiple samples in batch.

    Args:
        sample_ids: List of sample IDs to review
        review_type: Either "completeness" or "quality"
        training_status: Loaded training_status.json content
        inventory: Loaded inventory.json content
        artifact_index: Loaded artifact_index.json content

    Returns:
        Dict with aggregated review results
    """
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review type: {review_type}")

    results = []
    total_findings = 0
    severity_counts = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0, SEVERITY_INFO: 0}

    for sample_id in sample_ids:
        result = review_sample(sample_id, review_type, training_status, inventory, artifact_index)
        results.append(result)
        total_findings += result.get("finding_count", 0)
        for finding in result.get("findings", []):
            sev = finding.get("severity", SEVERITY_INFO)
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "review_type": review_type,
        "samples_reviewed": len(sample_ids),
        "total_findings": total_findings,
        "severity_counts": severity_counts,
        "critical_high_count": severity_counts[SEVERITY_CRITICAL] + severity_counts[SEVERITY_HIGH],
        "results": results,
    }


def generate_review_report(
    review_type: str,
    training_status: dict[str, Any],
    inventory: dict[str, Any],
    artifact_index: dict[str, Any],
) -> dict[str, Any]:
    """Generate a comprehensive review report for all samples.

    Args:
        review_type: Either "completeness" or "quality"
        training_status: Loaded training_status.json content
        inventory: Loaded inventory.json content
        artifact_index: Loaded artifact_index.json content

    Returns:
        Dict with complete review report
    """
    if review_type not in VALID_REVIEW_TYPES:
        raise ValueError(f"Invalid review type: {review_type}")

    samples = training_status.get("samples", [])
    sample_ids = [s["sample_id"] for s in samples]

    batch_result = review_batch(sample_ids, review_type, training_status, inventory, artifact_index)

    # Add summary by status
    status_summary = _summarize_findings_by_status(batch_result["results"])

    # Add recommendations
    recommendations = _generate_recommendations(batch_result, review_type)

    report = {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "review_type": review_type,
        "source_training_status": training_status.get("source_inventory", ""),
        "samples_reviewed": batch_result["samples_reviewed"],
        "total_findings": batch_result["total_findings"],
        "severity_counts": batch_result["severity_counts"],
        "critical_high_count": batch_result["critical_high_count"],
        "findings_by_status": status_summary,
        "recommendations": recommendations,
        "sample_results": batch_result["results"],
    }

    return report


def _check_completeness(
    sample: dict[str, Any],
    inventory_entry: dict[str, Any] | None,
    artifact_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check sample for completeness issues."""
    findings = []
    sample_id = sample.get("sample_id", "")
    status = sample.get("training_status", "")

    # Check required fields
    required_fields = ["sample_id", "relative_path", "sha256", "training_status"]
    for field in required_fields:
        if not sample.get(field):
            findings.append({
                "severity": SEVERITY_HIGH,
                "category": "missing_required_field",
                "field": field,
                "message": f"Missing required field: {field}",
            })

    # Check inventory entry exists
    if not inventory_entry:
        findings.append({
            "severity": SEVERITY_HIGH,
            "category": "missing_inventory_entry",
            "message": f"Sample '{sample_id}' not found in inventory",
        })
    else:
        # Check inventory has required metadata
        inv_required = ["size_bytes", "extension", "guessed_file_type"]
        for field in inv_required:
            if not inventory_entry.get(field):
                findings.append({
                    "severity": SEVERITY_MEDIUM,
                    "category": "incomplete_inventory_metadata",
                    "field": field,
                    "message": f"Inventory missing field: {field}",
                })

    # Check status-specific completeness
    if status == TRAINING_STATUS_SOLVED:
        if not sample.get("known_candidate"):
            findings.append({
                "severity": SEVERITY_HIGH,
                "category": "solved_missing_candidate",
                "message": "Solved sample missing known_candidate",
            })
        if not sample.get("evidence_sources"):
            findings.append({
                "severity": SEVERITY_MEDIUM,
                "category": "solved_missing_evidence",
                "message": "Solved sample missing evidence_sources",
            })

    elif status == TRAINING_STATUS_BLOCKED:
        if not sample.get("blocked_reason"):
            findings.append({
                "severity": SEVERITY_MEDIUM,
                "category": "blocked_missing_reason",
                "message": "Blocked sample missing blocked_reason",
            })
        if not sample.get("next_action"):
            findings.append({
                "severity": SEVERITY_LOW,
                "category": "blocked_missing_next_action",
                "message": "Blocked sample missing next_action",
            })

    elif status == TRAINING_STATUS_NEEDS_TRIAGE:
        if not sample.get("blocked_reason"):
            findings.append({
                "severity": SEVERITY_LOW,
                "category": "triage_missing_reason",
                "message": "Needs-triage sample missing blocked_reason (tool failure info)",
            })

    # Check artifact completeness for solved samples
    if status == TRAINING_STATUS_SOLVED:
        artifacts = _find_sample_artifacts(sample_id, artifact_index)
        if not artifacts:
            findings.append({
                "severity": SEVERITY_MEDIUM,
                "category": "solved_missing_artifacts",
                "message": "Solved sample has no artifacts in artifact_index",
            })

    return findings


def _check_quality(
    sample: dict[str, Any],
    inventory_entry: dict[str, Any] | None,
    artifact_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check sample for quality issues."""
    findings = []
    sample_id = sample.get("sample_id", "")
    status = sample.get("training_status", "")

    # Check category quality
    category = sample.get("category", "")
    if not category or category == "unknown":
        findings.append({
            "severity": SEVERITY_MEDIUM,
            "category": "poor_category",
            "message": "Sample has no or 'unknown' category",
        })

    # Check tags quality
    tags = sample.get("tags", [])
    if not tags:
        findings.append({
            "severity": SEVERITY_LOW,
            "category": "missing_tags",
            "message": "Sample has no tags",
        })
    elif len(tags) < 2:
        findings.append({
            "severity": SEVERITY_LOW,
            "category": "insufficient_tags",
            "message": f"Sample has only {len(tags)} tag(s)",
        })

    # Check classification quality
    classification = sample.get("classification", "")
    if status in (TRAINING_STATUS_SOLVED, TRAINING_STATUS_BLOCKED) and not classification:
        findings.append({
            "severity": SEVERITY_MEDIUM,
            "category": "missing_classification",
            "message": f"{status} sample missing classification",
        })

    # Check evidence source quality
    evidence_sources = sample.get("evidence_sources", [])
    if status == TRAINING_STATUS_SOLVED:
        has_validation_source = any("validation" in str(s).lower() for s in evidence_sources)
        if not has_validation_source:
            findings.append({
                "severity": SEVERITY_MEDIUM,
                "category": "solved_no_validation_source",
                "message": "Solved sample lacks validation evidence source",
            })

    # Check inventory metadata quality
    if inventory_entry:
        size_bytes = inventory_entry.get("size_bytes", 0)
        if size_bytes == 0:
            findings.append({
                "severity": SEVERITY_MEDIUM,
                "category": "zero_size",
                "message": "Sample has zero size in inventory",
            })
        elif size_bytes < 100:
            findings.append({
                "severity": SEVERITY_LOW,
                "category": "very_small_file",
                "message": f"Sample is very small ({size_bytes} bytes)",
            })

        # Check file type consistency
        guessed_type = inventory_entry.get("guessed_file_type", "")
        extension = inventory_entry.get("extension", "")
        if guessed_type == "unknown" and extension in (".exe", ".dll"):
            findings.append({
                "severity": SEVERITY_LOW,
                "category": "file_type_mismatch",
                "message": f"PE extension '{extension}' but guessed_file_type is 'unknown'",
            })

    return findings


def _find_sample_in_status(sample_id: str, training_status: dict[str, Any]) -> dict[str, Any] | None:
    """Find a sample in training status by ID."""
    for sample in training_status.get("samples", []):
        if sample.get("sample_id") == sample_id:
            return sample
        # Also try matching by short SHA
        sha256 = sample.get("sha256", "")
        if sha256[:16] == sample_id or sha256 == sample_id:
            return sample
    return None


def _find_sample_in_inventory(sample_id: str, inventory: dict[str, Any]) -> dict[str, Any] | None:
    """Find a sample in inventory by ID."""
    if not inventory:
        return None
    for entry in inventory.get("entries", []):
        if entry.get("sample_id") == sample_id:
            return entry
        sha256 = entry.get("sha256", "")
        if sha256[:16] == sample_id or sha256 == sample_id:
            return entry
    return None


def _find_sample_artifacts(sample_id: str, artifact_index: dict[str, Any]) -> list[dict[str, Any]]:
    """Find all artifacts for a sample in artifact_index."""
    artifacts = []
    v2 = artifact_index.get("latest_artifacts_v2", {})
    for key, meta in v2.items():
        if meta.get("sample_id") == sample_id:
            artifacts.append({"key": key, **meta})
    return artifacts


def _summarize_findings_by_status(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize findings grouped by training status."""
    by_status: dict[str, dict] = {}

    for result in results:
        status = result.get("training_status", "unknown")
        if status not in by_status:
            by_status[status] = {"count": 0, "findings": 0, "categories": set()}

        by_status[status]["count"] += 1
        by_status[status]["findings"] += result.get("finding_count", 0)

        for finding in result.get("findings", []):
            by_status[status]["categories"].add(finding.get("category", "unknown"))

    # Convert sets to lists for JSON serialization
    for status_data in by_status.values():
        status_data["categories"] = list(status_data["categories"])

    return by_status


def _generate_recommendations(batch_result: dict[str, Any], review_type: str) -> list[dict[str, Any]]:
    """Generate recommendations based on review findings."""
    recommendations = []
    severity_counts = batch_result.get("severity_counts", {})
    total_findings = batch_result.get("total_findings", 0)
    samples_reviewed = batch_result.get("samples_reviewed", 0)

    if severity_counts.get(SEVERITY_CRITICAL, 0) > 0:
        recommendations.append({
            "priority": "immediate",
            "action": "address_critical_findings",
            "message": f"Address {severity_counts[SEVERITY_CRITICAL]} critical finding(s) immediately",
        })

    if severity_counts.get(SEVERITY_HIGH, 0) > 10:
        recommendations.append({
            "priority": "high",
            "action": "review_high_severity_batch",
            "message": f"Batch review {severity_counts[SEVERITY_HIGH]} high severity findings",
        })

    if review_type == REVIEW_TYPE_COMPLETENESS:
        # Check for patterns in completeness issues
        recommendations.append({
            "priority": "medium",
            "action": "ensure_inventory_sync",
            "message": "Ensure all samples in training_status have corresponding inventory entries",
        })

        recommendations.append({
            "priority": "medium",
            "action": "validate_solved_samples",
            "message": "All solved samples should have known_candidate and evidence_sources",
        })

    else:  # REVIEW_TYPE_QUALITY
        recommendations.append({
            "priority": "low",
            "action": "improve_tag_coverage",
            "message": "Consider adding more descriptive tags to samples with insufficient tags",
        })

        recommendations.append({
            "priority": "low",
            "action": "classify_unknown_categories",
            "message": "Review samples with 'unknown' category for proper classification",
        })

    # General recommendation based on finding density
    if samples_reviewed > 0:
        finding_rate = total_findings / samples_reviewed
        if finding_rate > 5:
            recommendations.append({
                "priority": "high",
                "action": "comprehensive_audit",
                "message": f"High finding rate ({finding_rate:.1f} per sample). Consider comprehensive audit.",
            })

    return recommendations


def _load_json(path: Path, label: str) -> dict[str, Any]:
    """Load JSON file, return empty dict if not found or invalid."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON file with proper formatting."""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Review local reverse engineering training samples for completeness or quality."
    )
    parser.add_argument(
        "--review-type",
        choices=list(VALID_REVIEW_TYPES),
        default=REVIEW_TYPE_COMPLETENESS,
        help="Type of review to perform",
    )
    parser.add_argument(
        "--sample-id",
        help="Review a specific sample by ID",
    )
    parser.add_argument(
        "--sample-ids",
        help="Comma-separated list of sample IDs for batch review",
    )
    parser.add_argument(
        "--training-status",
        default=str(DEFAULT_TRAINING_STATUS),
        help="Path to local_reverse_training_status.json",
    )
    parser.add_argument(
        "--inventory",
        default=str(DEFAULT_INVENTORY),
        help="Path to local_reverse_inventory.json",
    )
    parser.add_argument(
        "--artifact-index",
        default=str(DEFAULT_ARTIFACT_INDEX),
        help="Path to artifact_index.json",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Path for review report output",
    )
    parser.add_argument(
        "--refresh-status",
        action="store_true",
        help="Refresh training status before review",
    )
    parser.add_argument(
        "--validated",
        default="project_state/local_reverse_validated_candidate_handoff.json",
        help="Path to validated candidate handoff (for --refresh-status)",
    )
    parser.add_argument(
        "--constraint-recovery",
        default="project_state/local_reverse_constraint_recovery_result.json",
        help="Path to constraint recovery result (for --refresh-status)",
    )
    parser.add_argument(
        "--solver-result",
        default="project_state/local_reverse_ida_solver_result.json",
        help="Path to solver result (for --refresh-status)",
    )
    parser.add_argument(
        "--queue-out",
        default="",
        help="Path for evaluation queue output (for --refresh-status)",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
